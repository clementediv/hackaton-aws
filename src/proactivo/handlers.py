"""AWS Lambda entry points. Business logic lives in servicio.py."""

import base64
import logging
from html import escape

from boto3.dynamodb.types import TypeDeserializer

from .reglas import evaluate
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
    cite = (
        f'<p class="s">Fuente: <a href="{escape(source["url"])}">{escape(source["titulo"])}</a>. '
        "Orientación preliminar: el organismo competente revisa y resuelve. "
        "Datos de demostración sintéticos.</p>"
    )
    if action == "acepto" or contact["estado"] == "aceptado":
        body = (
            "<p>¡Gracias! Registramos que quieres ayuda.</p>"
            f"<p><strong>Tu próximo paso:</strong> {escape(contact.get('paso_siguiente', ''))}</p>"
        )
        return _html(200, benefit["nombre"], body + cite)
    if action == "rechazo" or contact["estado"] == "rechazado":
        body = "<p>Entendido. No te volveremos a contactar por este beneficio.</p>"
        return _html(200, benefit["nombre"], body + cite)
    person = svc.person(run) or {}
    reasons = "".join(
        f"<li>{escape(m)}</li>" for m in evaluate(person, benefit, svc.today()).motivos
    )
    yes = f"?c={escape(run)}&b={escape(benefit_id)}&t={escape(token)}&v={escape(via)}&a=acepto"
    no = yes.replace("a=acepto", "a=rechazo")
    body = (
        f"<p>{escape(contact.get('motivo', ''))}</p><ul>{reasons}</ul>"
        f'<p><a class="b" href="{yes}">Sí, quiero ayuda</a> '
        f'<a class="b n" href="{no}">No me interesa</a></p>'
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
    page = f"""<!doctype html><html lang="es"><head><meta charset="utf-8">
<meta name="viewport" content="width=device-width,initial-scale=1"><title>{escape(title)}</title>
<style>body{{font-family:Arial,sans-serif;font-size:20px;line-height:1.5;max-width:640px;
margin:24px auto;padding:0 16px;color:#1a1a1a}}h1{{font-size:26px;color:#0f69c4}}
.b{{display:inline-block;padding:14px 22px;margin:6px 8px 6px 0;border-radius:8px;
background:#0f69c4;color:#fff;text-decoration:none}}.n{{background:#e9e9e9;color:#1a1a1a}}
.s{{font-size:16px;color:#555}}</style></head>
<body><p>ChileAtiende a Tiempo</p><h1>{escape(title)}</h1>{body}</body></html>"""
    return {
        "statusCode": status,
        "headers": {"Content-Type": "text/html; charset=utf-8", "Cache-Control": "no-store"},
        "body": page,
    }
