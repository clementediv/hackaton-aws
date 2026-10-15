"""Email and SMS texts: plain language, large type, one clear action."""

from html import escape
from urllib.parse import urlencode


def link(base_url: str, contact: dict, action: str, via: str) -> str:
    query = {
        "c": contact["run"],
        "b": contact["beneficio_id"],
        "t": contact["token"],
        "a": action,
        "v": via,
    }
    return f"{base_url.rstrip('/')}/?{urlencode(query)}"


def _intro(person: dict, benefit: dict, contact: dict) -> str:
    name = person.get("nombre", "").split(" ")[0] or "Hola"
    if contact.get("tipo") == "anticipado":
        when = contact.get("disponible_desde", "")
        return (
            f"{name}, desde el {when} podrías acceder a {benefit['nombre']}. "
            "Te avisamos antes para que lo cobres apenas puedas."
        )
    return f"{name}, según tus datos actuales podrías acceder a {benefit['nombre']}."


def email(person: dict, benefit: dict, contact: dict, base_url: str) -> tuple[str, str, str]:
    """Return (subject, text, html)."""
    subject = f"ChileAtiende: podrías acceder a {benefit['nombre']}"
    intro = _intro(person, benefit, contact)
    why = contact.get("motivo", "")
    see, yes, no = (link(base_url, contact, a, "email") for a in ("ver", "acepto", "rechazo"))
    source = benefit["fuente"]
    note = "" if source.get("verificado") else " (requisitos por verificar)"
    text = (
        f"{intro}\n\nPor qué te escribimos: {why}\n\n"
        f"¿Quieres que te acompañemos? Sí: {yes}\nNo me interesa: {no}\nVer detalle: {see}\n\n"
        "Esto es una orientación preliminar: el organismo competente revisa y resuelve.\n"
        f"Fuente: {source['titulo']} {source['url']}{note}\n"
        "Datos de demostración sintéticos."
    )
    button = (
        "display:inline-block;padding:14px 22px;margin:6px 8px 6px 0;border-radius:8px;"
        "font-size:20px;text-decoration:none;"
    )
    page = "font-family:Arial,sans-serif;font-size:20px;line-height:1.5;color:#1a1a1a"
    html = f"""<div style="{page}">
<p style="font-size:24px"><strong>{escape(intro)}</strong></p>
<p>Por qué te escribimos: {escape(why)}</p>
<p>¿Quieres que te acompañemos en el trámite?</p>
<p><a href="{escape(yes)}" style="{button}background:#0f69c4;color:#fff">Sí, quiero ayuda</a>
<a href="{escape(no)}" style="{button}background:#e9e9e9;color:#1a1a1a">No me interesa</a></p>
<p><a href="{escape(see)}">Ver el detalle de los requisitos</a></p>
<p style="font-size:16px;color:#555">Esto es una orientación preliminar: el organismo competente
revisa y resuelve. Fuente: <a href="{escape(source["url"])}">{escape(source["titulo"])}</a>
{escape(note)}. Datos de demostración sintéticos.</p>
<img src="{escape(link(base_url, contact, "abrir", "email"))}" width="1" height="1" alt="">
</div>"""
    return subject, text, html


def sms(person: dict, benefit: dict, contact: dict, base_url: str) -> str:
    return (
        f"ChileAtiende: {_intro(person, benefit, contact)} "
        f"Responde aquí: {link(base_url, contact, 'ver', 'sms')}"
    )
