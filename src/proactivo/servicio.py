"""Detect → contact → escalate → record the answer, persisted in DynamoDB.

Contact rule (ADR 0012): only an answer (accept/decline) stops the next
channels. Opening the email or entering the link is recorded but does not.
"""

import hmac
import itertools
import os
import secrets
from dataclasses import dataclass, field
from datetime import UTC, date, datetime, timedelta
from uuid import uuid4

import boto3
from boto3.dynamodb.conditions import Attr, Key

from . import mensajes
from .esquema import QUEUE_INDEX, QUEUE_PENDING, STATE_INDEX
from .reglas import changed_fields, eligible_from, evaluate, excluded

ANSWERS = {"acepto", "rechazo", "sin_respuesta"}
CLOSED = {"aceptado", "rechazado"}
# Chile mainland offset in October (DST); dates only, so an hour off is harmless.
CHILE_OFFSET = timedelta(hours=-3)
_sequence = itertools.count()


@dataclass(frozen=True)
class Settings:
    personas: str = "ca-personas"
    beneficios: str = "ca-beneficios"
    contactos: str = "ca-contactos"
    historial: str = "ca-historial"
    sender: str = ""
    real_emails: frozenset[str] = field(default_factory=frozenset)
    response_url: str = "https://example.invalid"
    wait_email_min: int = 5
    wait_sms_min: int = 5
    reference_date: date | None = None

    @classmethod
    def from_env(cls) -> "Settings":
        env = os.environ
        ref = env.get("FECHA_REFERENCIA", "").strip()
        return cls(
            personas=env.get("TABLA_PERSONAS", cls.personas),
            beneficios=env.get("TABLA_BENEFICIOS", cls.beneficios),
            contactos=env.get("TABLA_CONTACTOS", cls.contactos),
            historial=env.get("TABLA_HISTORIAL", cls.historial),
            sender=env.get("REMITENTE", ""),
            real_emails=frozenset(
                e.strip().lower() for e in env.get("EMAILS_REALES", "").split(",") if e.strip()
            ),
            response_url=env.get("URL_RESPUESTA", cls.response_url),
            wait_email_min=int(env.get("ESPERA_EMAIL_MIN", cls.wait_email_min)),
            wait_sms_min=int(env.get("ESPERA_SMS_MIN", cls.wait_sms_min)),
            reference_date=date.fromisoformat(ref) if ref else None,
        )

    def table_names(self) -> dict[str, str]:
        return {
            "personas": self.personas,
            "beneficios": self.beneficios,
            "contactos": self.contactos,
            "historial": self.historial,
        }


class Service:
    def __init__(self, settings: Settings, *, dynamodb=None, ses=None, clock=None) -> None:
        self.settings = settings
        dynamodb = dynamodb or boto3.resource("dynamodb")
        self.people = dynamodb.Table(settings.personas)
        self.catalog = dynamodb.Table(settings.beneficios)
        self.contacts = dynamodb.Table(settings.contactos)
        self.history = dynamodb.Table(settings.historial)
        self.ses = ses or boto3.client("ses")
        self.clock = clock or (lambda: datetime.now(UTC))
        self._benefits: list[dict] | None = None

    # -- helpers ------------------------------------------------------------
    def now(self) -> str:
        return self.clock().isoformat(timespec="seconds")

    def today(self) -> date:
        return self.settings.reference_date or (self.clock() + CHILE_OFFSET).date()

    def benefits(self) -> list[dict]:
        if self._benefits is None:
            self._benefits = _scan(self.catalog)
        return self._benefits

    def benefit(self, benefit_id: str) -> dict:
        found = next((b for b in self.benefits() if b["beneficio_id"] == benefit_id), None)
        if found is None:
            raise KeyError(f"Beneficio desconocido: {benefit_id}")
        return found

    def person(self, run: str) -> dict | None:
        return self.people.get_item(Key={"run": run}).get("Item")

    def contact(self, run: str, benefit_id: str) -> dict | None:
        return self.contacts.get_item(Key={"run": run, "beneficio_id": benefit_id}).get("Item")

    def log(self, run: str, benefit_id: str, event: str, channel: str, **detail) -> None:
        self.history.put_item(
            Item={
                "run": run,
                # Microseconds + per-process counter keep same-instant events in order.
                "sk": f"{self.clock().isoformat(timespec='microseconds')}"
                f"#{next(_sequence):06d}#{uuid4().hex[:6]}",
                "beneficio_id": benefit_id,
                "evento": event,
                "canal": channel,
                "detalle": {k: v for k, v in detail.items() if v is not None},
            }
        )

    def _update(self, contact: dict, values: dict, remove: tuple[str, ...] = (), when=None):
        names = {f"#{k}": k for k in [*values, *remove]}
        expr = "SET " + ", ".join(f"#{k} = :{k}" for k in values)
        if remove:
            expr += " REMOVE " + ", ".join(f"#{k}" for k in remove)
        options = {}
        if when is not None:
            options["ConditionExpression"] = when
        result = self.contacts.update_item(
            Key={"run": contact["run"], "beneficio_id": contact["beneficio_id"]},
            UpdateExpression=expr,
            ExpressionAttributeNames=names,
            ExpressionAttributeValues={f":{k}": v for k, v in values.items()},
            ReturnValues="ALL_NEW",
            **options,
        )
        return result["Attributes"]

    def _conditional_failed(self, exc: Exception) -> bool:
        return isinstance(exc, self.contacts.meta.client.exceptions.ConditionalCheckFailedException)

    # -- detection ------------------------------------------------------------
    def on_person_change(self, old: dict | None, new: dict | None, origin: str) -> list[dict]:
        """Open (or upgrade) one contact per benefit the person could now get."""
        if not new:
            return []
        return [c for b in self.benefits() if (c := self._detect(old, new, b, origin))]

    def _detect(self, old, person, benefit, origin) -> dict | None:
        if excluded(person, benefit):
            return None
        ref = self.today()
        existing = self.contact(person["run"], benefit["beneficio_id"])
        changes = changed_fields(old, person, benefit, ref)
        if evaluate(person, benefit, ref).cumple:
            if existing is None:
                return self._open(person, benefit, "disponible", _reason(changes, origin))
            if existing["tipo"] == "anticipado" and existing["respuesta"] != "rechazo":
                return self._available_now(existing, person, benefit)
            return None
        when = eligible_from(person, benefit, ref)
        if when and existing is None:
            reason = f"Se acerca la fecha en que cumplirías los requisitos ({when:%d-%m-%Y})."
            if changes:
                reason = _reason(changes, origin) + " " + reason
            return self._open(person, benefit, "anticipado", reason, when)
        return None

    def reconcile_all(self, origin: str = "diario") -> int:
        """Daily: time changes ages without anyone editing the table."""
        return sum(len(self.on_person_change(None, p, origin)) for p in _scan(self.people))

    def _open(self, person, benefit, kind, reason, available_from: date | None = None):
        run, benefit_id = person["run"], benefit["beneficio_id"]
        item = {
            "run": run,
            "beneficio_id": benefit_id,
            "beneficio": benefit["nombre"],
            "tipo": kind,
            "estado": "detectado",
            "token": secrets.token_urlsafe(16),
            "detectado_en": self.now(),
            "motivo": reason,
            "respuesta": "pendiente",
            "email_enviado": False,
            "email_abierto": False,
            "email_click": False,
            "sms_enviado": False,
            "sms_click": False,
            "terreno": False,
            "intentos": 0,
        }
        if available_from:
            item["disponible_desde"] = available_from.strftime("%d-%m-%Y")
        try:
            self.contacts.put_item(Item=item, ConditionExpression=Attr("run").not_exists())
        except Exception as exc:  # stream retries / concurrent daily run
            if self._conditional_failed(exc):
                return None
            raise
        self.log(run, benefit_id, "detectado", "sistema", tipo=kind, motivo=reason)
        return self._send_email(item, person, benefit)

    def _available_now(self, contact, person, benefit):
        """An anticipated benefit opened: notify again. Whoever already accepted
        is told, but not chased through the other channels."""
        accepted = contact["estado"] == "aceptado"
        values = {"tipo": "disponible", "motivo": "Ya cumples los requisitos."}
        if not accepted:
            values["respuesta"] = "pendiente"
        contact = self._update(contact, values, remove=("disponible_desde",))
        self.log(contact["run"], contact["beneficio_id"], "ya_disponible", "sistema")
        return self._send_email(contact, person, benefit, follow_up=not accepted)

    # -- channels ---------------------------------------------------------------
    def _queue(self, minutes: int) -> dict:
        when = (self.clock() + timedelta(minutes=minutes)).isoformat(timespec="seconds")
        return {"cola": QUEUE_PENDING, "siguiente_accion_en": when}

    def _send_email(self, contact, person, benefit, *, follow_up: bool = True):
        run, benefit_id = contact["run"], contact["beneficio_id"]
        address = (person.get("email") or "").strip()
        if not address:
            self.log(run, benefit_id, "canal_omitido", "email", motivo="Sin email registrado")
            return self._send_sms(contact, person, benefit) if follow_up else contact
        subject, text, html = mensajes.email(person, benefit, contact, self.settings.response_url)
        real = address.lower() in self.settings.real_emails and bool(self.settings.sender)
        message_id = None
        if real:
            try:
                message_id = self.ses.send_email(
                    Source=self.settings.sender,
                    Destination={"ToAddresses": [address]},
                    Message={
                        "Subject": {"Data": subject, "Charset": "UTF-8"},
                        "Body": {
                            "Text": {"Data": text, "Charset": "UTF-8"},
                            "Html": {"Data": html, "Charset": "UTF-8"},
                        },
                    },
                )["MessageId"]
            except Exception as exc:  # noqa: BLE001 - a failed send is a recorded outcome
                self.log(run, benefit_id, "email_fallido", "email", error=type(exc).__name__)
                contact = self._update(contact, {"email_error": type(exc).__name__})
                return self._send_sms(contact, person, benefit) if follow_up else contact
        values = {
            "email_enviado": True,
            "email_enviado_en": self.now(),
            "email_simulado": not real,
            "intentos": int(contact.get("intentos", 0)) + 1,
        }
        if follow_up:
            values |= {"estado": "email_enviado", **self._queue(self.settings.wait_email_min)}
        contact = self._update(contact, values)
        self.log(
            run,
            benefit_id,
            "email_enviado",
            "email",
            asunto=subject,
            simulado=not real,
            ses_message_id=message_id,
        )
        return contact

    def _send_sms(self, contact, person, benefit):
        run, benefit_id = contact["run"], contact["beneficio_id"]
        phone = (person.get("telefono") or "").strip()
        if not phone:
            self.log(run, benefit_id, "canal_omitido", "sms", motivo="Sin teléfono registrado")
            return self._to_field(contact, person)
        text = mensajes.sms(person, benefit, contact, self.settings.response_url)
        contact = self._update(
            contact,
            {
                "estado": "sms_enviado",
                "sms_enviado": True,
                "sms_enviado_en": self.now(),
                "sms_simulado": True,
                "sms_texto": text,
                "intentos": int(contact.get("intentos", 0)) + 1,
                **self._queue(self.settings.wait_sms_min),
            },
        )
        self.log(run, benefit_id, "sms_enviado", "sms", simulado=True, texto=text)
        return contact

    def _to_field(self, contact, person):
        contact = self._update(
            contact,
            {
                "estado": "terreno",
                "terreno": True,
                "terreno_desde": self.now(),
                "respuesta": "sin_respuesta",
            },
            remove=("cola", "siguiente_accion_en"),
        )
        self.log(
            contact["run"],
            contact["beneficio_id"],
            "asignado_terreno",
            "terreno",
            comuna=person.get("comuna"),
        )
        return contact

    # -- escalation -------------------------------------------------------------
    def escalate(self) -> int:
        """Move every due, unanswered contact to its next channel."""
        moved = 0
        query = {
            "IndexName": QUEUE_INDEX,
            "KeyConditionExpression": Key("cola").eq(QUEUE_PENDING)
            & Key("siguiente_accion_en").lte(self.now()),
        }
        due = []
        while True:
            page = self.contacts.query(**query)
            due += page["Items"]
            if "LastEvaluatedKey" not in page:
                break
            query["ExclusiveStartKey"] = page["LastEvaluatedKey"]
        for item in due:
            try:  # claim it: an answer may have arrived meanwhile
                contact = self._update(
                    item,
                    {"ultimo_escalamiento": self.now()},
                    remove=("cola", "siguiente_accion_en"),
                    when=Attr("estado").eq(item["estado"]) & Attr("cola").exists(),
                )
            except Exception as exc:
                if self._conditional_failed(exc):
                    continue
                raise
            person = self.person(contact["run"]) or {"run": contact["run"]}
            channel = "email" if contact["estado"] == "email_enviado" else "sms"
            self.log(contact["run"], contact["beneficio_id"], "sin_respuesta", channel)
            if contact["estado"] == "email_enviado":
                self._send_sms(contact, person, self.benefit(contact["beneficio_id"]))
            else:
                self._to_field(contact, person)
            moved += 1
        return moved

    # -- answers ----------------------------------------------------------------
    def interact(self, run: str, benefit_id: str, token: str, action: str, via: str) -> dict:
        """Link in the email/SMS: abrir (pixel), ver (entered), acepto, rechazo."""
        contact = self.contact(run, benefit_id)
        if contact is None or not hmac.compare_digest(str(token), contact["token"]):
            raise PermissionError("Enlace inválido o vencido.")
        via = via if via in ("email", "sms") else "email"
        if action == "abrir":
            if not contact.get("email_abierto"):
                contact = self._update(
                    contact, {"email_abierto": True, "email_abierto_en": self.now()}
                )
                self.log(run, benefit_id, "email_abierto", "email")
            return contact
        if action == "ver":
            if not contact.get(f"{via}_click"):
                contact = self._update(
                    contact, {f"{via}_click": True, f"{via}_click_en": self.now()}
                )
                self.log(run, benefit_id, "entro_al_mensaje", via)
            return contact
        if action in ("acepto", "rechazo"):
            return self.record_answer(run, benefit_id, action, via)
        raise ValueError("Acción no reconocida.")

    def record_answer(self, run: str, benefit_id: str, answer: str, channel: str) -> dict:
        """Answer from a link, a phone call or the field team."""
        if answer not in ANSWERS:
            raise ValueError("Respuesta no reconocida.")
        contact = self.contact(run, benefit_id)
        if contact is None:
            raise KeyError("No hay contacto para esa persona y beneficio.")
        if contact["estado"] in CLOSED:
            return contact  # first answer wins; history keeps everything
        if answer == "sin_respuesta":
            self.log(run, benefit_id, "no_contesta", channel)
            return self._update(contact, {"respuesta": "sin_respuesta"})
        values = {
            "estado": "aceptado" if answer == "acepto" else "rechazado",
            "respuesta": answer,
            "respuesta_canal": channel,
            "respuesta_en": self.now(),
        }
        if answer == "acepto":
            values["paso_siguiente"] = self.benefit(benefit_id)["paso_siguiente"]
        contact = self._update(contact, values, remove=("cola", "siguiente_accion_en"))
        self.log(run, benefit_id, f"respuesta_{answer}", channel)
        return contact

    # -- listings ---------------------------------------------------------------
    def by_state(self, state: str) -> list[dict]:
        return _query_all(
            self.contacts, IndexName=STATE_INDEX, KeyConditionExpression=Key("estado").eq(state)
        )

    def history_of(self, run: str) -> list[dict]:
        return _query_all(self.history, KeyConditionExpression=Key("run").eq(run))

    def contacts_of(self, run: str) -> list[dict]:
        return _query_all(self.contacts, KeyConditionExpression=Key("run").eq(run))


def _reason(changes: list[str], origin: str) -> str:
    if changes:
        return "Cambió tu información (" + "; ".join(changes) + ")."
    if origin == "carga":
        return "Lo detectamos al revisar tus datos registrados."
    return "Lo detectamos en la revisión periódica de tus datos."


def _scan(table) -> list[dict]:
    items, options = [], {}
    while True:
        page = table.scan(**options)
        items += page["Items"]
        if "LastEvaluatedKey" not in page:
            return items
        options["ExclusiveStartKey"] = page["LastEvaluatedKey"]


def _query_all(table, **query) -> list[dict]:
    items = []
    while True:
        page = table.query(**query)
        items += page["Items"]
        if "LastEvaluatedKey" not in page:
            return items
        query["ExclusiveStartKey"] = page["LastEvaluatedKey"]
