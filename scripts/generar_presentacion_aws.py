"""Genera diagramas SVG/HTML 16:9 para la presentación desde el estado revisado."""

import argparse
from html import escape
from pathlib import Path

OUT = Path(__file__).resolve().parents[1] / "20-arquitectura/presentacion-aws"
OUT.mkdir(parents=True, exist_ok=True)
parts = [
    """<svg xmlns="http://www.w3.org/2000/svg" width="1920" height="1080" viewBox="0 0 1920 1080">
<defs><marker id="arrow" viewBox="0 0 10 10" refX="9" refY="5" markerWidth="8"
markerHeight="8" orient="auto-start-reverse">
<path d="M0,0 L10,5 L0,10 Z" fill="#60738d"/></marker></defs>
<style>
text{font-family:Arial,Helvetica,sans-serif}
.title{font-size:48px;font-weight:700;fill:#102945}
.subtitle{font-size:24px;fill:#53667b}
.label{font-size:24px;font-weight:700;fill:#102945}
.body{font-size:22px;fill:#3f556e}
.small{font-size:20px;fill:#53667b}
</style>
<rect width="1920" height="1080" fill="#fff"/>
<rect x="48" y="45" width="10" height="64" rx="5" fill="#ff9900"/>
<text x="80" y="83" class="title">AWS en ChileAtiende a tiempo</text>
<text x="80" y="124" class="subtitle">
Página actualizada al 16-10-2026 · dos stacks AWS en us-east-1 · referencia: 912b025
</text>
"""
]


def rect(x, y, w, h, fill, stroke="none", r=18):
    parts.append(
        f'<rect x="{x}" y="{y}" width="{w}" height="{h}" rx="{r}" '
        f'fill="{fill}" stroke="{stroke}" stroke-width="2"/>'
    )


def txt(x, y, text, cls="body", anchor="start", fill=None):
    color = f' style="fill:{fill}"' if fill else ""
    parts.append(
        f'<text x="{x}" y="{y}" class="{cls}" text-anchor="{anchor}"{color}>{escape(text)}</text>'
    )


def node(x, y, title, lines=(), kind="aws", w=310, h=108):
    colors = {
        "aws": ("#fff6e8", "#edb66b"),
        "data": ("#eff5ff", "#8fb2e8"),
        "local": ("#fff", "#c8d4e1"),
        "ai": ("#f3eeff", "#ae95df"),
    }
    bg, stroke = colors[kind]
    rect(x, y, w, h, bg, stroke, 14)
    txt(x + w / 2, y + 35, title, "label", "middle")
    for i, line in enumerate(lines):
        txt(x + w / 2, y + 67 + i * 27, line, "small", "middle")


def arrow(x1, y1, x2, y2, label=None):
    parts.append(
        f'<path d="M{x1},{y1} L{x2},{y2}" stroke="#60738d" fill="none" '
        'stroke-width="2.5" marker-end="url(#arrow)"/>'
    )
    if label:
        txt((x1 + x2) / 2, (y1 + y2) / 2 - 12, label, "small", "middle")


def path(d):
    parts.append(
        f'<path d="{d}" stroke="#60738d" fill="none" stroke-width="2.5" marker-end="url(#arrow)"/>'
    )


rect(48, 164, 1824, 204, "#f1f5fa")
txt(76, 205, "01 · APP LOCAL", "label")
txt(76, 240, "Inicio · Mi Gobierno", "body")
txt(76, 271, "Asistente · Ejecutivo", "body")
txt(76, 310, "Streamlit / localhost", "small")
node(360, 196, "Portal ciudadano", ["Chat público o personal"], kind="local")
node(752, 196, "Python + contexto", ["Permiso, reglas PGU y fuentes"], kind="local")
node(1144, 196, "Amazon Bedrock", ["Claude · Converse / Stream"], kind="ai")
arrow(670, 250, 752, 250)
arrow(1062, 250, 1144, 250)
node(1536, 196, "Respuesta progresiva", ["Fuentes y próximo paso"], kind="local")
arrow(1454, 250, 1536, 250)
txt(
    360,
    342,
    (
        "SQLite: casos, documentos y trazabilidad. JSON: fuentes públicas."
        " Dictado y lectura opcional: navegador."
    ),
    "small",
)

rect(48, 390, 1824, 327, "#f8f9fc")
txt(76, 432, "02 · CONTACTO", "label")
txt(76, 465, "PROACTIVO", "label")
txt(76, 508, "Stack AWS", "body")
txt(76, 540, "ChileAtiendeProactivo", "small")
node(360, 420, "Amazon DynamoDB", ["Personas + catálogo"], kind="data", h=100)
node(752, 420, "AWS Lambda", ["Detecta con reglas Python"], h=100)
node(1144, 420, "Amazon SES", ["Email a casillas verificadas"], h=100)
node(1536, 420, "Respuesta de la persona", ["Lambda Function URL"], h=100)
arrow(670, 470, 752, 470, "Stream")
arrow(1062, 470, 1144, 470)
arrow(1454, 470, 1536, 470)
node(360, 578, "Amazon EventBridge", ["Revisión diaria / cada minuto"], h=100)
node(752, 578, "AWS Lambda", ["Revisar y escalar pendientes"], h=100)
node(1144, 578, "Amazon DynamoDB", ["Contactos + historial"], kind="data", h=100)
node(1536, 578, "Panel del ejecutivo", ["Lee AWS desde la app"], kind="local", h=100)
arrow(670, 628, 752, 628)
arrow(1062, 628, 1144, 628)
arrow(1454, 628, 1536, 628, "Lectura")
path("M907,520 L907,550 L1299,550 L1299,578")
path("M1691,520 L1691,550 L1450,550 L1450,578")
txt(
    360,
    704,
    (
        "Sin respuesta: email → SMS simulado → terreno. Aceptar o rechazar"
        " detiene el escalamiento; abrir no lo detiene."
    ),
    "small",
)

rect(48, 739, 1824, 205, "#f1f5fa")
txt(76, 780, "03 · API DE CHAT", "label")
txt(76, 822, "Stack AWS", "body")
txt(76, 854, "ChileAtiendeChat", "small")
node(360, 770, "API Gateway", ["HTTPS + clave de API"], h=100)
node(752, 770, "AWS Lambda", ["Agente y evaluación PGU"], h=100)
node(1144, 770, "Amazon Bedrock", ["Genera la explicación"], kind="ai", h=100)
node(1536, 770, "Amazon DynamoDB", ["Casos + consentimiento"], kind="data", h=100)
arrow(670, 820, 752, 820)
arrow(1062, 820, 1144, 820)
path("M907,870 L907,893 L1691,893 L1691,870")
txt(
    360,
    925,
    (
        "API separada: el frontend local todavía utiliza su adaptador "
        "directo a Bedrock. La Lambda persiste casos e historial."
    ),
    "small",
)

rect(48, 968, 1824, 75, "#102945", r=14)
txt(
    78,
    999,
    (
        "SOPORTE: IAM · permisos  |  Secrets Manager · claves de API  |  "
        "CloudWatch · logs  |  CDK / CloudFormation · despliegue"
    ),
    "small",
    fill="#fff",
)
txt(
    78,
    1028,
    (
        "La IA explica. El código calcula elegibilidad y plazos. Las bases"
        " locales y AWS aún no están completamente unificadas."
    ),
    "small",
    fill="#c9d9ea",
)
txt(
    1844,
    1067,
    "16-10-2026 · Cambios de interfaz integrados; despliegue AWS sin revalidar en vivo.",
    "small",
    "end",
)
parts.append("</svg>")
svg = "".join(parts)
(OUT / "arquitectura-aws.svg").write_text(svg, encoding="utf-8")
(OUT / "arquitectura-aws.html").write_text(
    (
        "<!doctype html><meta "
        'charset="utf-8"><style>html,body{margin:0;width:1920px;height:1080px;overflow:hidden}svg{display:block}</style>'
    )
    + svg,
    encoding="utf-8",
)
print(OUT / "arquitectura-aws.svg")

# Segunda diapositiva: recorrido de la página, sin confundir UI con servicios AWS.
parts = [svg[: svg.index('<rect width="1920"')], '<rect width="1920" height="1080" fill="#fff"/>']
txt(72, 82, "Del portal al acompañamiento personalizado", "title")
txt(
    72,
    126,
    "Recorrido vigente de la página · 16-10-2026 · interfaz local y conexiones con AWS",
    "subtitle",
)

rect(48, 167, 1824, 190, "#f1f5fa")
txt(76, 209, "01 · ORIENTACIÓN", "label")
txt(76, 245, "Sin consultar perfil", "body")
node(360, 197, "Inicio", ["Banner y navegación"], kind="local")
node(752, 197, "Asistente de IA", ["Consulta general"], kind="local")
node(1144, 197, "Fuentes públicas", ["Búsqueda local + Bedrock*"], kind="ai")
node(1536, 197, "Próximo paso", ["Explicación y enlaces"], kind="local")
for x in (670, 1062, 1454):
    arrow(x, 251, x + 82, 251)
txt(
    360,
    338,
    (
        "Home con animaciones y movimiento reducido; chat con historial "
        "público separado de los antecedentes personales."
    ),
    "small",
)

rect(48, 379, 1824, 235, "#f8f9fc")
txt(76, 421, "02 · MI GOBIERNO", "label")
txt(76, 456, "Consulta personal", "body")
txt(76, 490, "con autorización", "body")
node(360, 411, "Acceso de demo", ["Sesión de la persona"], kind="local")
node(752, 411, "Consentimiento", ["Permiso para antecedentes"], kind="local")
node(1144, 411, "Beneficios y etapas", ["Evaluación PGU en Python"], kind="data")
node(1536, 411, "Asistente personal", ["Contexto autorizado + fuentes"], kind="ai")
for x in (670, 1062, 1454):
    arrow(x, 465, x + 82, 465)
txt(
    360,
    560,
    (
        "Datos personales: identidad, documentos, contacto, trabajo y "
        "salud; adjuntar archivos no concede un beneficio."
    ),
    "small",
)
txt(
    360,
    592,
    (
        "Seguimiento y progreso declarado se guardan localmente. Otros "
        "beneficios todavía no tienen evaluación personalizada."
    ),
    "small",
)

rect(48, 636, 1824, 206, "#f1f5fa")
txt(76, 678, "03 · EJECUTIVO", "label")
txt(76, 715, "Sesión separada", "body")
node(360, 667, "Acceso del equipo", ["Credenciales de demo"], kind="local")
node(752, 667, "Seguimiento y ficha", ["Casos, permisos e historial"], kind="local")
node(1144, 667, "Mapa y campañas", ["Ubicaciones sintéticas RM"], kind="local")
node(1536, 667, "Contactos AWS", ["DynamoDB · solo lectura"], kind="data")
for x in (670, 1062, 1454):
    arrow(x, 721, x + 82, 721)
txt(
    360,
    820,
    (
        "La vista reúne herramientas; las flechas representan el recorrido"
        " de revisión, no una sincronización automática."
    ),
    "small",
)

rect(48, 864, 1824, 130, "#102945", r=14)
txt(78, 905, "MEJORAS RECIENTES DE LA PÁGINA", "label", fill="#fff")
txt(
    78,
    944,
    (
        "Datos y detalles alineados · espera animada · scroll dentro del "
        "historial · texto a 25 ms por palabra y sin cursor"
    ),
    "body",
    fill="#fff",
)
txt(
    78,
    977,
    (
        "Animaciones de inicio y Mi Gobierno · movimiento reducido · "
        "respuesta breve ante insultos sin arrastrar el tema PGU"
    ),
    "small",
    fill="#c9d9ea",
)
txt(
    72,
    1034,
    (
        "* Bedrock cuando está configurado; existe respaldo local. Dictado"
        " y lectura pertenecen al navegador."
    ),
    "small",
)
txt(
    72,
    1066,
    (
        "La orientación es preliminar. El organismo competente valida y "
        "resuelve. API de chat y datos AWS aún se integran por separado."
    ),
    "small",
)
parts.append("</svg>")
journey = "".join(parts)
(OUT / "recorrido-pagina.svg").write_text(journey, encoding="utf-8")
(OUT / "recorrido-pagina.html").write_text(
    (
        "<!doctype html><meta "
        'charset="utf-8"><style>html,body{margin:0;width:1920px;height:1080px;overflow:hidden}svg{display:block}</style>'
    )
    + journey,
    encoding="utf-8",
)
print(OUT / "recorrido-pagina.svg")

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--png", action="store_true", help="Exportar con Playwright y Chrome")
    args = parser.parse_args()
    if args.png:
        from playwright.sync_api import sync_playwright

        chrome = next(
            (
                str(p)
                for p in (
                    Path("/Applications/Google Chrome.app/Contents/MacOS/Google Chrome"),
                    Path("C:/Program Files/Google/Chrome/Application/chrome.exe"),
                )
                if p.exists()
            ),
            None,
        )
        with sync_playwright() as playwright:
            browser = playwright.chromium.launch(executable_path=chrome, headless=True)
            page = browser.new_page(viewport={"width": 1920, "height": 1080})
            for name in ("arquitectura-aws", "recorrido-pagina"):
                page.goto((OUT / f"{name}.html").as_uri())
                overflow = page.locator("svg text").evaluate_all("""els => els.filter(e => {
                    const b = e.getBBox();
                    return b.x < 0 || b.x + b.width > 1920 || b.y < 0 || b.y + b.height > 1080;
                }).map(e => e.textContent)""")
                if overflow:
                    raise ValueError(f"Texto fuera de la diapositiva: {overflow}")
                page.screenshot(path=str(OUT / f"{name}.png"))
                print(OUT / f"{name}.png")
            browser.close()
