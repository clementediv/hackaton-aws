"""AWS Lambda entry points. Business logic lives in servicio.py."""

import base64
import logging
from html import escape

from boto3.dynamodb.types import TypeDeserializer

from . import mensajes
from .servicio import Service, Settings

log = logging.getLogger()
log.setLevel(logging.INFO)

_service: Service | None = None
# 1x1 transparent GIF for the open-tracking pixel.
PIXEL = base64.b64decode("R0lGODlhAQABAIAAAAAAAP///yH5BAEAAAAALAAAAAABAAEAAAIBRAA7")


def service() -> Service:
    global _service
    if _service is None:
        _service = Service(Settings.from_env())
    _service._benefits = None  # the catalog is editable: reload per invocation
    return _service


def on_person_change(event, context):
    """DynamoDB stream of `Personas` (NEW_AND_OLD_IMAGES), partial batch failures."""
    deserializer = TypeDeserializer()
    svc, failures = service(), []

    def image(record, key):
        raw = record["dynamodb"].get(key)
        return {k: deserializer.deserialize(v) for k, v in raw.items()} if raw else None

    for record in event.get("Records", []):
        if record["eventName"] not in ("INSERT", "MODIFY"):
            continue
        try:
            origin = "carga" if record["eventName"] == "INSERT" else "cambio"
            opened = svc.on_person_change(
                image(record, "OldImage"), image(record, "NewImage"), origin
            )
            for contact in opened:
                log.info(
                    "contacto %s %s %s", contact["run"], contact["beneficio_id"], contact["estado"]
                )
        except Exception:
            log.exception("Fallo al procesar %s", record["dynamodb"].get("SequenceNumber"))
            failures.append({"itemIdentifier": record["dynamodb"]["SequenceNumber"]})
    return {"batchItemFailures": failures}


def on_escalate(event, context):
    moved = service().escalate()
    log.info("escalados %s", moved)
    return {"escalados": moved}


def on_daily(event, context):
    opened = service().reconcile_all("diario")
    log.info("contactos abiertos en la revisión diaria %s", opened)
    return {"abiertos": opened}


def on_http(event, context):
    """Lambda Function URL: links from the email and the SMS."""
    q = event.get("queryStringParameters") or {}
    run, benefit_id, token = q.get("c", ""), q.get("b", ""), q.get("t", "")
    action, via = q.get("a", "ver"), q.get("v", "email")
    svc = service()
    try:
        contact = svc.interact(run, benefit_id, token, action, via)
    except (PermissionError, ValueError, KeyError) as exc:
        if action == "abrir":
            return _gif()
        return _html(400, "Enlace no válido", f"<p>{escape(str(exc))}</p>")
    if action == "abrir":
        return _gif()
    benefit = svc.benefit(benefit_id)
    source = benefit["fuente"]
    note = "" if source.get("verificado") else " (requisitos por verificar)"
    cite = (
        f'<p class="note-text">Orientación preliminar: el organismo competente revisa y '
        f'resuelve. Fuente: <a href="{escape(source["url"])}">{escape(source["titulo"])}</a>'
        f"{escape(note)}. Datos de demostración sintéticos.</p>"
    )
    if action == "acepto" or contact["estado"] == "aceptado":
        body = (
            "<h2>¡Listo! Registramos tu solicitud de ayuda</h2>"
            "<p>Te acompañaremos durante el trámite.</p>"
            f"<h2>Tu próximo paso</h2><p>{escape(contact.get('paso_siguiente', ''))}</p>"
            "<p>¿Prefieres hablar con alguien? Llama al <strong>101</strong> o acércate a "
            "una sucursal ChileAtiende.</p>"
        )
        return _html(200, benefit["nombre"], body + cite)
    if action == "rechazo" or contact["estado"] == "rechazado":
        body = "<p>Entendido. No te volveremos a contactar por este beneficio.</p>"
        return _html(200, benefit["nombre"], body + cite)
    yes = f"?c={escape(run)}&b={escape(benefit_id)}&t={escape(token)}&v={escape(via)}&a=acepto"
    checks = "".join(f"<li>{escape(r['texto'])}</li>" for r in benefit["requisitos"])
    body = (
        f"<h2>¿Por qué te escribimos?</h2>"
        f"<p>{escape(contact.get('motivo_persona') or contact.get('motivo', ''))}</p>"
        f"<h2>¿Qué es?</h2><p>{escape(benefit.get('descripcion', ''))}</p>"
        f"<h2>¿Por qué te conviene?</h2><p>{escape(benefit.get('por_que_te_conviene', ''))}</p>"
        f"<h2>Requisitos</h2><ul>{checks}</ul>"
        f'<p><a class="btn" href="{yes}">'
        f'{escape(benefit.get("boton", "Quiero solicitarlo"))}</a></p>'
    )
    return _html(200, benefit["nombre"], body + cite)


def _gif():
    return {
        "statusCode": 200,
        "headers": {"Content-Type": "image/gif", "Cache-Control": "no-store"},
        "body": base64.b64encode(PIXEL).decode(),
        "isBase64Encoded": True,
    }


def _html(status: int, title: str, body: str):
    return {
        "statusCode": status,
        "headers": {"Content-Type": "text/html; charset=utf-8", "Cache-Control": "no-store"},
        "body": mensajes.web_page(title, body),
    }
