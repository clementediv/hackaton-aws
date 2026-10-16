"""Access from the app to the proactive-detection tables deployed on AWS.

Detection, sending and escalation run in the Lambdas (src/proactivo). The app
reads contacts and history, and writes only two things: a person's data (to
simulate a life event; the table stream then runs the detector) and the
person's answer, through the same `Service.record_answer` the response Lambda
uses. Design: 20-arquitectura/app-aws-conectada.md. Credentials come from the
`hackaton` profile in .env; when they are missing or expired, `check()`
explains it instead of failing.
"""

import logging
import os
from collections import Counter
from datetime import UTC, date, datetime, timedelta
from decimal import Decimal
from pathlib import Path

import boto3
from boto3.dynamodb.conditions import Key
from dotenv import dotenv_values

from src.proactivo import mensajes
from src.proactivo.reglas import add_months
from src.proactivo.servicio import CLOSED, Service, Settings

log = logging.getLogger(__name__)

ROOT = Path(__file__).resolve().parents[3]
TABLES = {
    "personas": "ca-personas",
    "contactos": "ca-contactos",
    "historial": "ca-historial",
}

STATE_LABELS = {
    "detectado": "Detectado",
    "aviso_enviado": "Aviso informativo enviado",
    "email_enviado": "Email enviado, sin respuesta",
    "sms_enviado": "SMS enviado, sin respuesta",
    "terreno": "Asignado a equipo en terreno",
    "aceptado": "Aceptó",
    "rechazado": "Rechazó",
}
KIND_LABELS = {
    "disponible": "Podría recibirlo hoy",
    "aviso": "Aviso previo",
    "anticipado": "Aviso anticipado",
    "riesgo": "Riesgo de pérdida",
}
STAGE_LABELS = {"preparacion": "64 años: preparar", "recordatorio": "64 años y 8 meses"}
EVENT_LABELS = {
    "detectado": "Detectado",
    "nueva_etapa": "Nueva etapa de aviso",
    "ya_disponible": "Ya puede solicitarlo",
    "email_enviado": "Email enviado",
    "email_fallido": "Email fallido",
    "email_abierto": "Abrió el email",
    "entro_al_mensaje": "Entró al mensaje",
    "canal_omitido": "Canal omitido",
    "sin_respuesta": "Sin respuesta en el plazo",
    "sms_enviado": "SMS enviado (simulado)",
    "asignado_terreno": "Asignado a terreno",
    "no_contesta": "No contesta",
    "respuesta_acepto": "Aceptó",
    "respuesta_rechazo": "Rechazó",
}


def _plain(value):
    if isinstance(value, Decimal):
        return int(value) if value == value.to_integral_value() else float(value)
    if isinstance(value, list):
        return [_plain(v) for v in value]
    if isinstance(value, dict):
        return {k: _plain(v) for k, v in value.items()}
    return value


def _settings() -> dict:
    return {**dotenv_values(ROOT / ".env"), **os.environ}


def session() -> boto3.Session:
    """Session with the event profile (`AWS_PROFILE` in .env or env)."""
    values = _settings()
    return boto3.Session(
        profile_name=(values.get("AWS_PROFILE") or "").strip() or None,
        region_name=(values.get("AWS_REGION") or "").strip() or "us-east-1",
    )


def resource():
    return session().resource("dynamodb")


def service(dynamodb=None) -> Service:
    """The Lambdas' service, used for answers; the app never sends email."""
    if dynamodb is None:
        s = session()
        return Service(Settings(), dynamodb=s.resource("dynamodb"), ses=s.client("ses"))
    region = dynamodb.meta.client.meta.region_name
    return Service(Settings(), dynamodb=dynamodb, ses=boto3.client("ses", region_name=region))


def enabled() -> bool:
    """`CA_AWS=0` keeps the app away from AWS (the tests set it)."""
    return (_settings().get("CA_AWS") or "1").strip() != "0"


def check(dynamodb=None) -> tuple[bool, str]:
    """(ok, message): can the app read the contacts table right now?"""
    if dynamodb is None and not enabled():
        return False, "La conexión con AWS está desactivada (`CA_AWS=0`)."
    try:
        table = (dynamodb or resource()).Table(TABLES["contactos"])
        table.scan(Limit=1)
        return True, ""
    except Exception as exc:  # noqa: BLE001 - shown to the officer, never raised
        name = type(exc).__name__
        text = str(exc)
        if "ExpiredToken" in text or "expired" in text.lower():
            return False, "Las credenciales del perfil `hackaton` vencieron: hay que renovarlas."
        if "NoCredentials" in name or "ProfileNotFound" in name:
            return False, "No hay credenciales AWS configuradas (perfil `hackaton`)."
        if "ResourceNotFound" in text:
            return False, "Las tablas no existen: falta desplegar el stack `ChileAtiendeProactivo`."
        return False, f"No se pudo leer AWS ({name})."


def _scan(table) -> list[dict]:
    items, options = [], {}
    while True:
        page = table.scan(**options)
        items += page["Items"]
        if "LastEvaluatedKey" not in page:
            return [_plain(i) for i in items]
        options["ExclusiveStartKey"] = page["LastEvaluatedKey"]


def _label(c: dict, name: str = "") -> dict:
    c.pop("token", None)  # never shown: it authorizes the email links
    c["nombre"] = name
    c["estado_texto"] = STATE_LABELS.get(c.get("estado"), c.get("estado", ""))
    kind = KIND_LABELS.get(c.get("tipo"), c.get("tipo", ""))
    if c.get("etapa"):
        kind += f" · {STAGE_LABELS.get(c['etapa'], c['etapa'])}"
    c["tipo_texto"] = kind
    return c


def load_people(dynamodb=None) -> list[dict]:
    """Demo people (RUN 9…) first, then the dataset."""
    people = _scan((dynamodb or resource()).Table(TABLES["personas"]))
    return sorted(people, key=lambda p: (not p["run"].startswith("9"), p["run"]))


def load_contacts(dynamodb=None) -> list[dict]:
    """Every contact, with the person's name and a readable status."""
    db = dynamodb or resource()
    names = {p["run"]: p.get("nombre", "") for p in _scan(db.Table(TABLES["personas"]))}
    contacts = [_label(c, names.get(c["run"], "")) for c in _scan(db.Table(TABLES["contactos"]))]
    return sorted(contacts, key=lambda c: c.get("detectado_en", ""), reverse=True)


def contacts_for(run: str, dynamodb=None) -> list[dict]:
    """One person's contacts (a key query, cheap enough for every page load),
    with the title and reason of the notice they received."""
    svc = service(dynamodb)
    person = svc.person(run) or {}
    contacts = [_plain(c) for c in svc.contacts_of(run)]
    for c in contacts:
        try:
            content = mensajes.compose(person, svc.benefit(c["beneficio_id"]), c)
            c["titulo"], c["por_que"] = content.title, content.why
        except (KeyError, StopIteration):  # the catalog changed after the contact
            c["titulo"], c["por_que"] = c.get("beneficio", ""), ""
        _label(c, person.get("nombre", ""))
    return sorted(contacts, key=lambda c: c.get("detectado_en", ""), reverse=True)


# -- writes ------------------------------------------------------------------------
def today_chile() -> date:
    return (datetime.now(UTC) - timedelta(hours=3)).date()


def event_values(
    *,
    age: tuple[int, int] | None = None,
    children: int | None = None,
    marital_status: str | None = None,
    accident: bool = False,
    rsh_bracket: int | None = None,
    days_abroad: int | None = None,
    reference: date | None = None,
) -> dict:
    """Attributes of `ca-personas` to change; same fields as `proactivo.py evento`."""
    values: dict = {}
    if age is not None:
        years, months = age
        birth = add_months(reference or today_chile(), -(years * 12 + months))
        values["fecha_nacimiento"] = birth.isoformat()
    if children is not None:
        values["num_hijos"] = children
    if marital_status:
        values["estado_civil"] = marital_status
    if accident:
        values["accidente_laboral"] = True
    if rsh_bracket is not None:
        values["tramo_rsh"] = rsh_bracket
    if days_abroad is not None:
        values["dias_fuera_ultimo_anio"] = days_abroad
    return values


def apply_event(run: str, values: dict, dynamodb=None) -> None:
    """Change a person's data; the table stream runs the detector Lambda."""
    if not values:
        raise ValueError("Indique al menos un cambio.")
    (dynamodb or resource()).Table(TABLES["personas"]).update_item(
        Key={"run": run},
        UpdateExpression="SET " + ", ".join(f"#{k} = :{k}" for k in values),
        ExpressionAttributeNames={f"#{k}": k for k in values},
        ExpressionAttributeValues={f":{k}": v for k, v in values.items()},
        ConditionExpression="attribute_exists(run)",
    )


def reset_person(run: str, dynamodb=None) -> tuple[int, int]:
    """Forget a person's contacts and history to repeat a demo (data stays)."""
    svc = service(dynamodb)
    contacts, history = svc.contacts_of(run), svc.history_of(run)
    with svc.contacts.batch_writer() as batch:
        for c in contacts:
            batch.delete_item(Key={"run": c["run"], "beneficio_id": c["beneficio_id"]})
    with svc.history.batch_writer() as batch:
        for e in history:
            batch.delete_item(Key={"run": e["run"], "sk": e["sk"]})
    return len(contacts), len(history)


def record_answer(run: str, benefit_id: str, answer: str, channel: str, dynamodb=None) -> dict:
    """Answer one contact; stops the following channels, like the email button."""
    return _plain(service(dynamodb).record_answer(run, benefit_id, answer, channel))


def sync_invitation(run: str, accepted: bool, channel: str, dynamodb=None) -> list[str]:
    """Accepting or declining the accompaniment in the app answers every open
    contact of that RUN on AWS. Returns the benefit ids that changed."""
    if not enabled():
        return []
    svc = service(dynamodb)
    answer = "acepto" if accepted else "rechazo"
    changed = []
    for contact in svc.contacts_of(run):
        if contact["estado"] not in CLOSED:
            svc.record_answer(run, contact["beneficio_id"], answer, channel)
            changed.append(contact["beneficio_id"])
    if changed:
        log.info("AWS: %s %s en %s", run, answer, changed)
    return changed


def load_history(run: str, dynamodb=None) -> list[dict]:
    table = (dynamodb or resource()).Table(TABLES["historial"])
    items, query = [], {"KeyConditionExpression": Key("run").eq(run)}
    while True:
        page = table.query(**query)
        items += page["Items"]
        if "LastEvaluatedKey" not in page:
            break
        query["ExclusiveStartKey"] = page["LastEvaluatedKey"]
    events = [_plain(i) for i in items]
    for e in events:
        e["fecha"] = e["sk"][:19].replace("T", " ")
        e["evento_texto"] = EVENT_LABELS.get(e["evento"], e["evento"])
    return events


def summary(contacts: list[dict]) -> dict:
    """Counts for the dashboard: people, channels and answers."""
    real = [c for c in contacts if c.get("email_enviado") and not c.get("email_simulado")]
    return {
        "contactos": len(contacts),
        "personas": len({c["run"] for c in contacts}),
        "emails_reales": len(real),
        "emails_simulados": sum(bool(c.get("email_simulado")) for c in contacts),
        "abiertos": sum(bool(c.get("email_abierto")) for c in contacts),
        "entraron": sum(bool(c.get("email_click") or c.get("sms_click")) for c in contacts),
        "sms": sum(bool(c.get("sms_enviado")) for c in contacts),
        "terreno": sum(c.get("estado") == "terreno" for c in contacts),
        "aceptan": sum(c.get("respuesta") == "acepto" for c in contacts),
        "rechazan": sum(c.get("respuesta") == "rechazo" for c in contacts),
        "por_estado": Counter(c.get("estado_texto", "") for c in contacts),
        "por_beneficio": Counter(c.get("beneficio", "") for c in contacts),
    }
