"""Email, SMS and landing pages: ChileAtiende look, plain language, one action.

Email HTML uses tables and inline styles only (Gmail/Outlook drop <style> and
SVG). Palette as in the app assets (src/app/assets): logo blue/red, portal blue,
Roboto.
"""

from html import escape
from urllib.parse import urlencode

BLUE = "#0f69b4"
BLUE_DARK = "#0d4d82"
LOGO_BLUE = "#00499B"
LOGO_RED = "#E5002C"
TEXT = "#363636"
MUTED = "#4a4a4a"
BACKGROUND = "#f2f2f2"
SANS = "Roboto,Arial,Helvetica,sans-serif"
SLAB = "'Roboto Slab',Georgia,serif"


def link(base_url: str, contact: dict, action: str, via: str) -> str:
    query = {
        "c": contact["run"],
        "b": contact["beneficio_id"],
        "t": contact["token"],
        "a": action,
        "v": via,
    }
    return f"{base_url.rstrip('/')}/?{urlencode(query)}"


def _first_name(person: dict) -> str:
    return (person.get("nombre") or "").split(" ")[0]


def _why(benefit: dict, contact: dict) -> str:
    if contact.get("tipo") == "anticipado":
        return (
            f"Desde el {contact.get('disponible_desde', '')} cumplirías los requisitos. "
            "Te avisamos antes para que la cobres apenas puedas."
        )
    return contact.get("motivo_persona") or "Revisamos tus datos y cumples los requisitos."


def _requirements(benefit: dict) -> list[str]:
    # Contacts open only when every requirement is (or will be) met.
    return list(dict.fromkeys(r["texto"] for r in benefit["requisitos"]))


def _source_note(benefit: dict) -> tuple[str, str, str]:
    source = benefit["fuente"]
    note = "" if source.get("verificado") else " (requisitos por verificar)"
    return source["titulo"], source["url"], note


def email(person: dict, benefit: dict, contact: dict, base_url: str) -> tuple[str, str, str]:
    """Return (subject, text, html) with a single call to action."""
    name = _first_name(person)
    subject = f"{name + ', p' if name else 'P'}odrías recibir {benefit['nombre']}"
    title = f"Podrías recibir {benefit['nombre']}"
    why = _why(benefit, contact)
    cta = link(base_url, contact, "acepto", "email")
    button = benefit.get("boton", "Quiero solicitarlo")
    requirements = _requirements(benefit)
    source_title, source_url, note = _source_note(benefit)
    verb = "cumplirás" if contact.get("tipo") == "anticipado" else "cumples"

    text = "\n".join(
        [
            f"Hola{' ' + name if name else ''}:",
            "",
            title,
            "",
            f"¿Por qué te escribimos? {why}",
            f"¿Qué es? {benefit.get('descripcion', '')}",
            f"¿Por qué te conviene? {benefit.get('por_que_te_conviene', '')}",
            f"Según tus datos, {verb} con:",
            *(f"  ✓ {r}" for r in requirements),
            "",
            f"{button}: {cta}",
            "¿Prefieres hablar con alguien? Llama al 101 o acércate a una sucursal ChileAtiende.",
            "",
            "Orientación preliminar: el organismo competente revisa y resuelve.",
            f"Fuente: {source_title} {source_url}{note}",
            "Datos de demostración sintéticos.",
        ]
    )

    def section(heading: str, body: str) -> str:
        return (
            f'<p style="margin:0 0 4px;font-family:{SLAB};font-size:18px;font-weight:bold;'
            f'color:{BLUE_DARK}">{escape(heading)}</p>'
            f'<p style="margin:0 0 20px;font-size:17px;line-height:1.55;color:{TEXT}">'
            f"{escape(body)}</p>"
        )

    checks = "".join(
        f'<tr><td valign="top" style="padding:3px 10px 3px 0;color:{BLUE};font-size:18px;'
        f'font-weight:bold">✓</td><td style="padding:3px 0;font-size:17px;color:{TEXT}">'
        f"{escape(r)}</td></tr>"
        for r in requirements
    )
    body = (
        section("¿Por qué te escribimos?", why)
        + section("¿Qué es?", benefit.get("descripcion", ""))
        + section("¿Por qué te conviene?", benefit.get("por_que_te_conviene", ""))
        + f'<p style="margin:0 0 6px;font-family:{SLAB};font-size:18px;font-weight:bold;'
        f'color:{BLUE_DARK}">Según tus datos, {verb} con:</p>'
        f'<table role="presentation" cellpadding="0" cellspacing="0" style="margin:0 0 8px">'
        f"{checks}</table>"
    )
    cta_html = f"""<table role="presentation" cellpadding="0" cellspacing="0"
 style="margin:8px 0 12px">
<tr><td style="background:{BLUE};border-radius:6px">
<a href="{escape(cta)}" style="display:inline-block;padding:16px 32px;font-family:{SANS};
font-size:19px;font-weight:bold;color:#ffffff;text-decoration:none">{escape(button)}</a>
</td></tr></table>
<p style="margin:0 0 6px;font-size:15px;color:{MUTED}">Te mostraremos tu próximo paso y te
acompañaremos en el trámite.</p>
<p style="margin:0;font-size:15px;color:{MUTED}">¿Prefieres hablar con alguien? Llama al
<strong>101</strong> o acércate a una sucursal ChileAtiende.</p>"""
    footer = (
        "Orientación preliminar: el organismo competente revisa los requisitos y resuelve. "
        f'Fuente: <a href="{escape(source_url)}" style="color:{BLUE}">{escape(source_title)}</a>'
        f"{escape(note)}. Datos de demostración sintéticos."
    )
    pixel = escape(link(base_url, contact, "abrir", "email"))
    html = f"""<!doctype html><html lang="es"><head><meta charset="utf-8">
<meta name="viewport" content="width=device-width,initial-scale=1"></head>
<body style="margin:0;padding:0;background:{BACKGROUND}">
<table role="presentation" width="100%" cellpadding="0" cellspacing="0"
 style="background:{BACKGROUND}">
<tr><td align="center" style="padding:24px 12px">
<table role="presentation" width="600" cellpadding="0" cellspacing="0"
 style="width:100%;max-width:600px;background:#ffffff;font-family:{SANS};color:{TEXT}">
{_brand_rows()}
<tr><td style="background:{BLUE};padding:26px 32px">
<p style="margin:0 0 6px;font-size:17px;color:#ffffff">Hola{escape(" " + name) if name else ""},</p>
<p style="margin:0;font-family:{SLAB};font-size:26px;line-height:1.25;font-weight:bold;
color:#ffffff">{escape(title)}</p></td></tr>
<tr><td style="padding:28px 32px 8px">{body}{cta_html}</td></tr>
<tr><td style="padding:20px 32px 28px">
<p style="margin:0;padding-top:16px;border-top:1px solid #e8e8e8;font-size:13px;line-height:1.5;
color:#7a7a7a">{footer}</p></td></tr>
</table></td></tr></table>
<img src="{pixel}" width="1" height="1" alt="" style="display:block;border:0">
</body></html>"""
    return subject, text, html


def _brand_rows() -> str:
    """Flag-colored stripe and the ChileAtiende wordmark (no images: Gmail-safe)."""
    return f"""<tr><td style="padding:0;font-size:0;line-height:0">
<table role="presentation" width="100%" cellpadding="0" cellspacing="0"><tr>
<td width="38%" style="background:{LOGO_BLUE};height:6px;font-size:0">&nbsp;</td>
<td style="background:{LOGO_RED};height:6px;font-size:0">&nbsp;</td></tr></table></td></tr>
<tr><td style="padding:18px 32px;border-bottom:1px solid #e8e8e8">
<span style="font-family:{SLAB};font-size:26px;font-weight:bold;color:{LOGO_BLUE}">Chile</span><span
 style="font-family:{SLAB};font-size:26px;font-weight:bold;color:{LOGO_RED}">Atiende</span>
<span style="display:block;font-size:12px;color:#7a7a7a;letter-spacing:.5px">
GOBIERNO DE CHILE</span>
</td></tr>"""


def web_page(title: str, body_html: str) -> str:
    """Landing page for the email/SMS links, same brand as the email."""
    return f"""<!doctype html><html lang="es"><head><meta charset="utf-8">
<meta name="viewport" content="width=device-width,initial-scale=1"><title>{escape(title)}</title>
<style>
body{{margin:0;background:{BACKGROUND};font-family:{SANS};color:{TEXT}}}
.card{{max-width:640px;margin:24px auto;background:#fff}}
.card td{{font-family:{SANS}}}
.hero{{background:{BLUE};color:#fff;padding:26px 32px}}
.hero h1{{margin:0;font-family:{SLAB};font-size:26px;line-height:1.25}}
.content{{padding:28px 32px;font-size:18px;line-height:1.55}}
.content h2{{margin:0 0 4px;font-family:{SLAB};font-size:18px;color:{BLUE_DARK}}}
.content p{{margin:0 0 18px}}
.btn{{display:inline-block;padding:16px 32px;border-radius:6px;background:{BLUE};color:#fff;
font-weight:bold;font-size:19px;text-decoration:none}}
.note{{padding:0 32px 28px;font-size:13px;color:#7a7a7a}}
.note a{{color:{BLUE}}}
@media (max-width:480px){{.hero,.content,.note{{padding-left:16px;padding-right:16px}}}}
</style></head>
<body><table role="presentation" class="card" width="100%" cellpadding="0" cellspacing="0">
{_brand_rows()}
<tr><td class="hero"><h1>{escape(title)}</h1></td></tr>
<tr><td class="content">{body_html}</td></tr>
</table></body></html>"""


def sms(person: dict, benefit: dict, contact: dict, base_url: str) -> str:
    name = _first_name(person)
    return (
        f"ChileAtiende: {name + ', p' if name else 'P'}odrías recibir {benefit['nombre']}. "
        f"Más información y solicitud: {link(base_url, contact, 'ver', 'sms')}"
    )
