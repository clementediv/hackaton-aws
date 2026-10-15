"""Email, SMS and landing pages: ChileAtiende look, plain language, one action.

Four email kinds, chosen by the contact:
- aviso (etapa preparacion / recordatorio): before the application opens;
- disponible: apparently eligible (PGU: "¡Felicidades!");
- riesgo: someone who receives the benefit could lose it;
- anticipado: generic early notice for other benefits.
Every email stresses that eligibility is apparent and amounts are referential.

Email HTML uses tables and inline styles only (Gmail/Outlook drop <style> and
SVG). Palette as in the app assets (src/app/assets): logo blue/red, portal blue,
Roboto.
"""

from dataclasses import dataclass, field
from html import escape
from urllib.parse import urlencode

BLUE = "#0f69b4"
BLUE_DARK = "#0d4d82"
LOGO_BLUE = "#00499B"
LOGO_RED = "#E5002C"
TEXT = "#363636"
MUTED = "#4a4a4a"
BACKGROUND = "#f2f2f2"
NOTICE_BG = "#fff6db"
NOTICE_BORDER = "#946c00"
SANS = "Roboto,Arial,Helvetica,sans-serif"
# Minimalist sans-serif headings (weight 600), instead of a slab serif.
HEAD = "'Helvetica Neue',Helvetica,Arial,sans-serif"

DISCLAIMER = (
    "La presente información constituye una orientación preliminar basada en los datos "
    "disponibles a la fecha: el resultado es aparente, no constituye una resolución y no "
    "garantiza el otorgamiento del beneficio. El Instituto de Previsión Social revisará sus "
    "requisitos y resolverá. Los montos indicados son referenciales: el monto que usted podría "
    "recibir puede ser distinto y será calculado por el IPS. Las condiciones están sujetas a "
    "cambios."
)
RISK_DISCLAIMER = (
    "El presente es un aviso preventivo basado en los datos disponibles: no significa que "
    "usted haya perdido el beneficio. El Instituto de Previsión Social revisa cada caso y "
    "resuelve. Las condiciones están sujetas a cambios."
)
PHONE_LINE = (
    "Si prefiere atención personalizada, puede llamar al 101 o acudir a cualquier sucursal "
    "ChileAtiende."
)
GREETING = "Junto con saludarle, le informamos que "


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


def salutation(person: dict) -> str:
    name = (person.get("nombre") or "").strip()
    return f"Estimado(a) {name}:" if name else "Estimado(a):"


def _lower_first(text: str) -> str:
    return text[:1].lower() + text[1:]


@dataclass
class Content:
    title: str
    why: str
    button: str
    salutation: str = "Estimado(a):"
    sections: list[tuple[str, str]] = field(default_factory=list)
    checklist: tuple[str, list[str]] | None = None
    missing: tuple[str, list[str]] | None = None
    disclaimer: str = DISCLAIMER
    warning: bool = False


def compose(person: dict, benefit: dict, contact: dict) -> Content:
    """Texts of the notice; the HTML and plain-text renderers share them."""
    name = _first_name(person)
    values = {
        "nombre": name,
        "apertura": contact.get("disponible_desde", ""),
        "acceso": contact.get("acceso_desde", ""),
        "valor": contact.get("riesgo_valor", ""),
    }
    about = [
        ("¿En qué consiste?", benefit.get("descripcion", "")),
        ("¿Por qué le conviene?", benefit.get("por_que_te_conviene", "")),
    ]
    if amount := benefit.get("monto_referencial"):
        about.append(("Monto referencial", amount))
    requirements = list(dict.fromkeys(r["texto"] for r in benefit["requisitos"]))
    kind = contact.get("tipo")

    if kind == "riesgo":
        risk = next(r for r in benefit["riesgos"] if r["id"] == contact["riesgo_id"])
        return Content(
            title=risk["titulo"].format(**values),
            why=risk["motivo"].format(**values),
            button=risk["boton"],
            sections=[("Información relevante", risk["explicacion"])],
            disclaimer=RISK_DISCLAIMER,
            warning=True,
        )
    if kind == "aviso":
        stage = next(n for n in benefit["avisos_previos"] if n["id"] == contact["etapa"])
        missing = list(contact.get("faltantes") or [])
        return Content(
            title=stage["titulo"].format(**values),
            why=stage["motivo"].format(**values),
            button=stage["boton"],
            sections=about,
            checklist=(
                "Documentos que le recomendamos preparar",
                list(benefit.get("documentos") or []),
            ),
            missing=(
                ("Según sus datos, aún le falta", missing)
                if missing
                else (
                    "Según los datos disponibles, no le falta ningún antecedente. Le "
                    "recomendamos revisar que sus documentos se encuentren vigentes.",
                    [],
                )
            ),
        )
    if kind == "anticipado":
        return Content(
            title=f"Próximamente usted podría acceder a {benefit['nombre']}",
            why=(
                f"{GREETING}a partir del {values['apertura']} usted cumpliría los requisitos "
                "de este beneficio. Le escribimos con anticipación para que pueda solicitarlo "
                "oportunamente."
            ),
            button=benefit.get("boton", "Solicitar el beneficio"),
            sections=about,
            checklist=("Según sus datos, usted cumpliría con", requirements),
        )
    title = (
        benefit.get("titulo_elegible")
        or "Aparentemente usted podría recibir " + (benefit["nombre"])
    )
    return Content(
        title=title.format(**values),
        why=GREETING
        + _lower_first(contact.get("motivo_persona") or "Revisamos sus datos.")
        + " Según la información disponible, aparentemente usted cumple los requisitos de "
        "este beneficio.",
        button=benefit.get("boton", "Solicitar el beneficio"),
        sections=about,
        checklist=("Según sus datos, aparentemente cumple con", requirements),
    )


def _source_note(benefit: dict) -> tuple[str, str, str]:
    source = benefit["fuente"]
    note = "" if source.get("verificado") else " (requisitos por verificar)"
    return source["titulo"], source["url"], note


def email(person: dict, benefit: dict, contact: dict, base_url: str) -> tuple[str, str, str]:
    """Return (subject, text, html) with a single call to action."""
    content = compose(person, benefit, contact)
    content.salutation = salutation(person)
    cta = link(base_url, contact, "acepto", "email")
    source_title, source_url, note = _source_note(benefit)

    lines = [content.salutation, "", content.title, "", content.why, ""]
    lines += [f"IMPORTANTE: {content.disclaimer}", ""]
    for heading, body in content.sections:
        lines += [f"{heading} {body}"]
    for block in (content.checklist, content.missing):
        if block:
            lines += ["", f"{block[0]}:" if block[1] else block[0], *(f"  • {i}" for i in block[1])]
    lines += [
        "",
        f"{content.button}: {cta}",
        PHONE_LINE,
        "",
        "Atentamente,",
        "ChileAtiende · Instituto de Previsión Social",
        "",
        f"Fuente: {source_title} {source_url}{note}",
        "Datos de demostración sintéticos.",
    ]
    text = "\n".join(lines)

    def heading(label: str) -> str:
        return (
            f'<p style="margin:0 0 4px;font-family:{HEAD};font-size:18px;font-weight:600;'
            f'color:{BLUE_DARK}">{escape(label)}</p>'
        )

    def paragraph(body: str) -> str:
        return (
            f'<p style="margin:0 0 20px;font-size:17px;line-height:1.55;color:{TEXT}">'
            f"{escape(body)}</p>"
        )

    def items(entries: list[str], mark: str, color: str) -> str:
        rows = "".join(
            f'<tr><td valign="top" style="padding:3px 10px 3px 0;color:{color};font-size:18px;'
            f'font-weight:bold">{mark}</td><td style="padding:3px 0;font-size:17px;'
            f'color:{TEXT}">{escape(e)}</td></tr>'
            for e in entries
        )
        return (
            f'<table role="presentation" cellpadding="0" cellspacing="0" '
            f'style="margin:0 0 20px">{rows}</table>'
        )

    body = paragraph(content.salutation)
    body += heading("Motivo de esta comunicación") + paragraph(content.why)
    body += (
        f'<table role="presentation" width="100%" cellpadding="0" cellspacing="0" '
        f'style="margin:0 0 22px"><tr><td style="background:{NOTICE_BG};'
        f"border-left:5px solid {NOTICE_BORDER};padding:14px 16px;font-size:15px;"
        f'line-height:1.5;color:{TEXT}"><strong>Importante:</strong> '
        f"{escape(content.disclaimer)}</td></tr></table>"
    )
    for label, text_body in content.sections:
        body += heading(label) + paragraph(text_body)
    if content.checklist:
        mark = "✓" if content.checklist[0].startswith("Según") else "•"
        body += heading(content.checklist[0] + ":") + items(content.checklist[1], mark, BLUE)
    if content.missing:
        label, entries = content.missing
        body += (
            heading(label + ":") + items(entries, "!", LOGO_RED) if entries else paragraph(label)
        )

    cta_html = f"""<table role="presentation" cellpadding="0" cellspacing="0"
 style="margin:8px 0 12px">
<tr><td style="background:{BLUE};border-radius:6px">
<a href="{escape(cta)}" style="display:inline-block;padding:16px 32px;font-family:{SANS};
font-size:19px;font-weight:bold;color:#ffffff;text-decoration:none">{escape(content.button)}</a>
</td></tr></table>
<p style="margin:0 0 22px;font-size:15px;color:{MUTED}">{escape(PHONE_LINE)}</p>
<p style="margin:0;font-size:16px;color:{TEXT}">Atentamente,<br>
<span style="font-family:{HEAD};font-weight:600;color:{BLUE_DARK}">ChileAtiende ·
Instituto de Previsión Social</span></p>"""
    footer = (
        f'Fuente: <a href="{escape(source_url)}" style="color:{BLUE}">{escape(source_title)}</a>'
        f"{escape(note)}. Datos de demostración sintéticos."
    )
    hero = LOGO_RED if content.warning else BLUE
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
<tr><td style="background:{hero};padding:26px 32px">
<p style="margin:0;font-family:{HEAD};font-size:24px;line-height:1.3;font-weight:600;
color:#ffffff">{escape(content.title)}</p></td></tr>
<tr><td style="padding:28px 32px 8px">{body}{cta_html}</td></tr>
<tr><td style="padding:20px 32px 28px">
<p style="margin:0;padding-top:16px;border-top:1px solid #e8e8e8;font-size:13px;line-height:1.5;
color:#7a7a7a">{footer}</p></td></tr>
</table></td></tr></table>
<img src="{pixel}" width="1" height="1" alt="" style="display:block;border:0">
</body></html>"""
    return content.title, text, html


def _brand_rows() -> str:
    """Flag-colored stripe and the ChileAtiende wordmark (no images: Gmail-safe)."""
    return f"""<tr><td style="padding:0;font-size:0;line-height:0">
<table role="presentation" width="100%" cellpadding="0" cellspacing="0"><tr>
<td width="38%" style="background:{LOGO_BLUE};height:6px;font-size:0">&nbsp;</td>
<td style="background:{LOGO_RED};height:6px;font-size:0">&nbsp;</td></tr></table></td></tr>
<tr><td style="padding:18px 32px;border-bottom:1px solid #e8e8e8">
<span style="font-family:{HEAD};font-size:26px;font-weight:600;color:{LOGO_BLUE}">Chile</span><span
 style="font-family:{HEAD};font-size:26px;font-weight:600;color:{LOGO_RED}">Atiende</span>
<span style="display:block;font-family:{HEAD};font-size:14px;font-weight:500;color:{BLUE_DARK}">
Instituto de Previsión Social</span>
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
.hero h1{{margin:0;font-family:{HEAD};font-size:24px;font-weight:600;line-height:1.3}}
.content{{padding:28px 32px;font-size:18px;line-height:1.55}}
.content h2{{margin:0 0 4px;font-family:{HEAD};font-size:18px;font-weight:600;color:{BLUE_DARK}}}
.content p{{margin:0 0 18px}}
.btn{{display:inline-block;padding:16px 32px;border-radius:6px;background:{BLUE};color:#fff;
font-weight:bold;font-size:19px;text-decoration:none}}
.notice{{background:{NOTICE_BG};border-left:5px solid {NOTICE_BORDER};padding:14px 16px;
font-size:15px;margin:0 0 20px}}
.note-text{{font-size:13px;color:#7a7a7a}}
.note-text a{{color:{BLUE}}}
@media (max-width:480px){{.hero,.content{{padding-left:16px;padding-right:16px}}}}
</style></head>
<body><table role="presentation" class="card" width="100%" cellpadding="0" cellspacing="0">
{_brand_rows()}
<tr><td class="hero"><h1>{escape(title)}</h1></td></tr>
<tr><td class="content">{body_html}
<p class="notice"><strong>Importante:</strong> {escape(DISCLAIMER)}</p></td></tr>
</table></body></html>"""


def sms(person: dict, benefit: dict, contact: dict, base_url: str) -> str:
    title = compose(person, benefit, contact).title
    return f"ChileAtiende: {title}. Más información: {link(base_url, contact, 'ver', 'sms')}"
