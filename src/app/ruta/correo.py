"""Email changed by the person in Mi Gobierno and the benefit summary sent to it.

The new address lives with the person's other self-reported data (consent
required, deleted on revoke) and becomes the contact every view shows.
Sending uses Amazon SES with the event profile. SES is in sandbox: an address
receives mail only after it clicks the AWS verification link, so the first
attempt asks AWS to send that link instead of the summary.
"""

import re
from html import escape

from . import casos, config, government
from . import reglas as rules
from .aws_contactos import session as _aws_session
from .fechas import fmt

EMAIL_PATTERN = re.compile(r"^[^@\s]+@[^@\s]+\.[A-Za-z]{2,}$")
CHANNEL = "Web ChileAtiende"

SENT = "enviado"
VERIFICATION_SENT = "verificacion_enviada"
PENDING_VERIFICATION = "verificacion_pendiente"


def normalize(address: str) -> str:
    address = (address or "").strip().lower()
    if not EMAIL_PATTERN.match(address):
        raise ValueError("Ingresa un correo válido, por ejemplo nombre@dominio.cl.")
    return address


def saved_email(run: str) -> str:
    """The address the person declared, or '' (also without consent)."""
    try:
        return government.load_profile(run).get("email", "")
    except PermissionError:
        return ""


def save_email(run: str, address: str) -> str:
    address = normalize(address)
    previous = saved_email(run)
    government.save_profile(run, {**government.load_profile(run), "email": address})
    if address != previous:
        casos.registrar_evento(run, CHANNEL, "correo_actualizado", {"correo": address})
    return address


def ses_client():
    """SES with the same profile and region as the AWS read-only views."""
    return _aws_session().client("ses")


def summary(diagnosis: rules.Diagnostico) -> tuple[str, str, str]:
    """(subject, text, html) with the PGU orientation computed by the rules engine."""
    pgu = diagnosis.pgu
    amount = (
        f"${pgu.monto_estimado:,.0f} al mes (orientativo)".replace(",", ".")
        if pgu.resultado in (rules.ELEGIBLE, rules.PROXIMO) and pgu.monto_estimado
        else ""
    )
    status = pgu.resultado.replace("_", " ")
    lines = [
        ("Pensión Garantizada Universal (PGU)", status.capitalize()),
        ("Motivo", pgu.motivo),
        ("Monto estimado", amount),
        ("Puedes solicitarla desde", fmt(diagnosis.hitos.fecha_apertura_pgu)),
        (
            "Jubilación",
            f"{diagnosis.jubilacion.resultado.replace('_', ' ')} — {diagnosis.jubilacion.motivo}",
        ),
    ]
    lines = [(label, value) for label, value in lines if value]
    first_name = diagnosis.nombre.split()[0]
    subject = "Mi Gobierno · Resumen de tus beneficios"
    note = (
        "Esta es una orientación calculada con datos de demostración al "
        f"{fmt(config.FECHA_REFERENCIA)}. No es una resolución: el IPS evalúa y resuelve."
    )
    text = "\n".join(
        [f"Hola {first_name}:", "", "Este es el resumen de tus beneficios en Mi Gobierno.", ""]
        + [f"- {label}: {value}" for label, value in lines]
        + ["", f"Fuente: {config.FUENTE_PGU}", note, ""]
        + ["ChileAtiende · Instituto de Previsión Social"]
    )
    rows = "".join(
        f'<tr><td style="padding:6px 12px 6px 0;color:#555;vertical-align:top">{escape(label)}</td>'
        f'<td style="padding:6px 0;font-weight:bold">{escape(value)}</td></tr>'
        for label, value in lines
    )
    html = (
        '<div style="font-family:Arial,sans-serif;font-size:15px;color:#222;max-width:600px">'
        '<p style="background:#0f69b4;color:#fff;padding:14px 18px;margin:0;font-size:18px">'
        "Mi Gobierno · ChileAtiende</p>"
        f'<div style="padding:18px"><p>Hola {escape(first_name)}:</p>'
        "<p>Este es el resumen de tus beneficios en Mi Gobierno.</p>"
        f'<table style="border-collapse:collapse">{rows}</table>'
        f'<p>Fuente: <a href="{escape(config.FUENTE_PGU)}">ChileAtiende · PGU</a></p>'
        f'<p style="color:#666;font-size:13px">{escape(note)}</p>'
        "<p>ChileAtiende · Instituto de Previsión Social</p></div></div>"
    )
    return subject, text, html


def _verified(ses, address: str) -> bool:
    attributes = ses.get_identity_verification_attributes(Identities=[address])
    status = attributes["VerificationAttributes"].get(address, {}).get("VerificationStatus")
    return status == "Success"


def send_summary(run: str, diagnosis: rules.Diagnostico, ses=None) -> str:
    """Send the summary to the saved address; in sandbox, start its verification first.

    Returns SENT, VERIFICATION_SENT (AWS just mailed the link) or
    PENDING_VERIFICATION (link already sent, not clicked yet).
    """
    address = saved_email(run)
    if not address:
        raise ValueError("Guarda primero tu correo electrónico.")
    ses = ses or ses_client()
    if not _verified(ses, address):
        known = ses.get_identity_verification_attributes(Identities=[address])
        if address in known["VerificationAttributes"]:
            return PENDING_VERIFICATION
        ses.verify_email_identity(EmailAddress=address)
        casos.registrar_evento(run, CHANNEL, "correo_verificacion_solicitada", {"correo": address})
        return VERIFICATION_SENT
    sender = config.SES_SENDER
    if not sender or not _verified(ses, sender):
        sender = address
    subject, text, html = summary(diagnosis)
    message_id = ses.send_email(
        Source=sender,
        Destination={"ToAddresses": [address]},
        Message={
            "Subject": {"Data": subject, "Charset": "UTF-8"},
            "Body": {
                "Text": {"Data": text, "Charset": "UTF-8"},
                "Html": {"Data": html, "Charset": "UTF-8"},
            },
        },
    )["MessageId"]
    casos.registrar_evento(
        run, CHANNEL, "resumen_enviado", {"correo": address, "ses_message_id": message_id}
    )
    return SENT
