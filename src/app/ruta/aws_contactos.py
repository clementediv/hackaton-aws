"""Read-only access to the proactive-detection tables deployed on AWS.

The app never writes here: detection, sending and escalation run in the
Lambdas (src/proactivo). Credentials come from the `hackaton` profile in .env;
when they are missing or expired, `check()` explains it instead of failing.
"""

import os
from collections import Counter
from decimal import Decimal
from pathlib import Path

import boto3
from boto3.dynamodb.conditions import Key
from dotenv import dotenv_values

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


def session() -> boto3.Session:
    """Session with the event profile (`AWS_PROFILE` in .env or env)."""
    values = {**dotenv_values(ROOT / ".env"), **os.environ}
    return boto3.Session(
        profile_name=(values.get("AWS_PROFILE") or "").strip() or None,
        region_name=(values.get("AWS_REGION") or "").strip() or "us-east-1",
    )


def resource():
    return session().resource("dynamodb")


def check(dynamodb=None) -> tuple[bool, str]:
    """(ok, message): can the app read the contacts table right now?"""
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


def load_contacts(dynamodb=None) -> list[dict]:
    """Every contact, with the person's name and a readable status."""
    db = dynamodb or resource()
    names = {p["run"]: p.get("nombre", "") for p in _scan(db.Table(TABLES["personas"]))}
    contacts = _scan(db.Table(TABLES["contactos"]))
    for c in contacts:
        c.pop("token", None)  # never shown: it authorizes the email links
        c["nombre"] = names.get(c["run"], "")
        c["estado_texto"] = STATE_LABELS.get(c.get("estado"), c.get("estado", ""))
        kind = KIND_LABELS.get(c.get("tipo"), c.get("tipo", ""))
        if c.get("etapa"):
            kind += f" · {STAGE_LABELS.get(c['etapa'], c['etapa'])}"
        c["tipo_texto"] = kind
    return sorted(contacts, key=lambda c: c.get("detectado_en", ""), reverse=True)


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
