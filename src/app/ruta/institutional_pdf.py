"""Branded editorial PDF: executive cover, territorial map and methodology."""

from datetime import datetime
from html import escape
from io import BytesIO
from zoneinfo import ZoneInfo

from reportlab.lib import colors
from reportlab.lib.styles import ParagraphStyle, getSampleStyleSheet
from reportlab.lib.units import mm
from reportlab.platypus import (
    Flowable,
    Image,
    KeepTogether,
    PageBreak,
    Paragraph,
    SimpleDocTemplate,
    Spacer,
    Table,
    TableStyle,
)

from .report_heatmap import render_heatmap

BLUE = colors.HexColor("#0d4d82")
NAVY = colors.HexColor("#082e4d")
TEAL = colors.HexColor("#087e8b")
INK = colors.HexColor("#173d59")
MUTED = colors.HexColor("#526879")
LIGHT = colors.HexColor("#eaf1f7")
WHITE = colors.white


def generate_pdf(data):
    output = BytesIO()
    styles = getSampleStyleSheet()
    definitions = [
        ("Body", dict(fontSize=10, leading=15, textColor=INK, spaceAfter=8)),
        ("Small", dict(fontSize=8, leading=11, textColor=MUTED, spaceAfter=7)),
        (
            "Heading",
            dict(
                fontName="Helvetica-Bold",
                fontSize=18,
                leading=23,
                textColor=BLUE,
                spaceBefore=10,
                spaceAfter=12,
            ),
        ),
        (
            "Subheading",
            dict(
                fontName="Helvetica-Bold",
                fontSize=12,
                leading=17,
                textColor=BLUE,
                spaceBefore=12,
                spaceAfter=9,
            ),
        ),
        (
            "CoverTitle",
            dict(
                fontName="Helvetica-Bold", fontSize=36, leading=41, textColor=WHITE, spaceAfter=16
            ),
        ),
        (
            "CoverName",
            dict(fontSize=17, leading=22, textColor=colors.HexColor("#b6e8ef"), spaceAfter=12),
        ),
        (
            "CoverSmall",
            dict(fontSize=8, leading=12, textColor=colors.HexColor("#bfd3e2"), spaceAfter=6),
        ),
        (
            "CoverBody",
            dict(fontSize=9.5, leading=14, textColor=colors.HexColor("#e6f0f7"), spaceAfter=11),
        ),
        (
            "CoverHeading",
            dict(
                fontName="Helvetica-Bold",
                fontSize=13,
                leading=19,
                textColor=WHITE,
                spaceBefore=17,
                spaceAfter=12,
            ),
        ),
        ("Number", dict(fontName="Helvetica-Bold", fontSize=25, leading=30, textColor=BLUE)),
        ("Cell", dict(fontSize=8, leading=11, textColor=INK)),
    ]
    for name, options in definitions:
        styles.add(
            ParagraphStyle("Report" + name, fontName="Helvetica", **options)
            if "fontName" not in options
            else ParagraphStyle("Report" + name, **options)
        )

    def text(value, style="Body"):
        return Paragraph(escape(str(value)), styles["Report" + style])

    def date_label(value):
        return (
            datetime.fromisoformat(value)
            .astimezone(ZoneInfo("America/Santiago"))
            .strftime("%d/%m/%Y %H:%M")
        )

    class StageBars(Flowable):
        def __init__(self):
            super().__init__()
            self.width, self.height = 174 * mm, 42 * mm

        def draw(self):
            canvas = self.canv
            denominator = next(iter(data["stages"].values()))
            for i, (label, count) in enumerate(data["stages"].items()):
                y = self.height - 11 - i * 27
                canvas.setFillColor(INK)
                canvas.setFont("Helvetica", 9)
                canvas.drawString(0, y, label)
                canvas.setFillColor(colors.HexColor("#dce7ef"))
                canvas.roundRect(115, y - 2, 270, 12, 5, fill=1, stroke=0)
                if denominator and count:
                    canvas.setFillColor(TEAL if i == 3 else BLUE)
                    canvas.roundRect(115, y - 2, 270 * count / denominator, 12, 5, fill=1, stroke=0)
                canvas.setFillColor(INK)
                percent = f"{count / denominator:.0%}" if denominator else "s/d"
                canvas.drawString(400, y, f"{count}  /  {percent}")

    document = SimpleDocTemplate(
        output,
        pagesize=(210 * mm, 297 * mm),
        rightMargin=18 * mm,
        leftMargin=18 * mm,
        topMargin=27 * mm,
        bottomMargin=22 * mm,
        title="Reporte institucional · ChileAtiende a Tiempo",
        author="ChileAtiende a Tiempo",
    )
    story = [
        Spacer(1, 9 * mm),
        text("GESTIÓN TERRITORIAL  /  REPORTE INSTITUCIONAL", "CoverSmall"),
        Spacer(1, 5 * mm),
        Paragraph("Beneficios que llegan<br/>a tiempo.", styles["ReportCoverTitle"]),
        text(data["institution"], "CoverName"),
        text(f"Destinatario: {data['audience']}", "CoverSmall"),
        text(
            "Territorio: " + (", ".join(data["scope"]) or "Sin comunas seleccionadas"), "CoverSmall"
        ),
        text(
            f"Generado: {date_label(data['generated'])} · Corte: {date_label(data['cutoff'])} "
            "(Santiago)",
            "CoverSmall",
        ),
        Spacer(1, 9 * mm),
    ]
    cards = Table(
        [
            [text(data[key], "Number") for key in ("total", "pending", "guidance", "progress")],
            [
                text(label, "Small")
                for label in (
                    "Personas de la campaña",
                    "Por contactar",
                    "Esperan orientación",
                    "Avances declarados",
                )
            ],
        ],
        colWidths=[43.5 * mm] * 4,
    )
    cards.setStyle(
        TableStyle(
            [
                ("BACKGROUND", (0, 0), (-1, -1), WHITE),
                ("LINEBEFORE", (1, 0), (-1, -1), 0.5, LIGHT),
                ("LEFTPADDING", (0, 0), (-1, -1), 12),
                ("TOPPADDING", (0, 0), (-1, 0), 13),
                ("BOTTOMPADDING", (0, -1), (-1, -1), 10),
            ]
        )
    )
    story += [cards, text("Lectura ejecutiva", "CoverHeading")]
    story.extend(text(finding, "CoverBody") for finding in data["findings"])
    story += [
        PageBreak(),
        text("01  /  Inteligencia territorial", "Small"),
        text("Dónde concentrar la atención", "Heading"),
        text(
            f"{data['heatmap']['mapped']} ubicaciones representadas · "
            "Pendientes de atención en terreno",
            "Subheading",
        ),
        Image(BytesIO(render_heatmap(data["heatmap"])), width=174 * mm, height=98.3 * mm),
        Spacer(1, 4 * mm),
        text(data["heatmap"]["note"], "Small"),
        text(data["heatmap"]["source"], "Small"),
        text("Del aviso al avance declarado", "Subheading"),
        StageBars(),
        text(
            "Porcentajes sobre personas con alerta fechada y eventos en orden temporal. "
            "No equivalen a beneficios entregados. Sin alerta fechada no se reconstruye "
            "el recorrido a partir del estado de contacto.",
            "Small",
        ),
        PageBreak(),
        text("02  /  Gestión y evidencia", "Small"),
        text("Detalle territorial", "Heading"),
    ]
    headers = ["Comuna", "Personas", "Por contactar", "Orientación", "Inicio", "Avance*", "Declinó"]
    rows = [[text(h, "Cell") for h in headers]]
    for row in data["territory"]:
        rows.append(
            [
                text(row[key], "Cell")
                for key in (
                    "commune",
                    "people",
                    "pending",
                    "guidance",
                    "started",
                    "progress",
                    "declined",
                )
            ]
        )
    if len(rows) == 1:
        rows.append([text("Sin casos", "Cell"), *[text("—", "Cell") for _ in range(6)]])
    table = Table(rows, colWidths=[42 * mm, *[22 * mm] * 6], repeatRows=1, hAlign="LEFT")
    table.setStyle(
        TableStyle(
            [
                ("BACKGROUND", (0, 0), (-1, 0), colors.HexColor("#cbdfea")),
                ("ROWBACKGROUNDS", (0, 1), (-1, -1), [WHITE, colors.HexColor("#e7eef4")]),
                ("LINEBELOW", (0, 0), (-1, 0), 1, TEAL),
                ("VALIGN", (0, 0), (-1, -1), "TOP"),
                ("TOPPADDING", (0, 0), (-1, -1), 9),
                ("BOTTOMPADDING", (0, 0), (-1, -1), 9),
            ]
        )
    )
    story += [
        table,
        Spacer(1, 4 * mm),
        text("*Avance declarado por la persona. Inicio: estado del colador.", "Small"),
    ]
    if data["other"]:
        story.append(text(f"Otros estados o estados sin clasificar: {data['other']} personas."))
    story.append(
        KeepTogether(
            [
                text("Alcance y fuentes", "Subheading"),
                text(data["source"], "Small"),
                text(
                    "Cobertura territorial según la campaña y las comunas seleccionadas. "
                    "No incluye eventos AWS ni registros administrativos externos. "
                    "Contiene solo información sin nombres, RUN ni datos de contacto.",
                    "Small",
                ),
                text(data["limitation"], "Small"),
            ]
        )
    )

    def background(canvas, doc):
        canvas.saveState()
        cover = doc.page == 1
        canvas.setFillColor(NAVY if cover else colors.HexColor("#f0f4f8"))
        canvas.rect(0, 0, 210 * mm, 297 * mm, fill=1, stroke=0)
        if cover:
            canvas.setFillColor(colors.HexColor("#0b3958"))
            canvas.circle(220 * mm, 20 * mm, 110 * mm, fill=1, stroke=0)
            canvas.setStrokeColor(colors.HexColor("#164c68"))
            canvas.setLineWidth(1)
            canvas.circle(220 * mm, 20 * mm, 125 * mm, fill=0, stroke=1)
            canvas.circle(220 * mm, 20 * mm, 145 * mm, fill=0, stroke=1)
            canvas.setFillColor(colors.HexColor("#36c1ca"))
            canvas.rect(0, 0, 4 * mm, 297 * mm, fill=1, stroke=0)
        else:
            canvas.setFillColor(WHITE)
            canvas.rect(0, 275 * mm, 210 * mm, 22 * mm, fill=1, stroke=0)
            canvas.setFillColor(TEAL)
            canvas.rect(18 * mm, 276 * mm, 14 * mm, 1 * mm, fill=1, stroke=0)
        canvas.setFillColor(WHITE if cover else BLUE)
        canvas.setFont("Helvetica-Bold", 10)
        canvas.drawString(18 * mm, 282 * mm, "ChileAtiende a Tiempo")
        canvas.setFont("Helvetica", 8)
        canvas.drawRightString(192 * mm, 282 * mm, "REPORTE INSTITUCIONAL")
        canvas.setStrokeColor(colors.HexColor("#376078") if cover else colors.HexColor("#d5e0e9"))
        canvas.line(18 * mm, 17 * mm, 192 * mm, 17 * mm)
        canvas.setFillColor(colors.HexColor("#bfd3e2") if cover else MUTED)
        canvas.setFont("Helvetica", 8)
        canvas.drawString(18 * mm, 12 * mm, "ChileAtiende a Tiempo · Datos de ejemplo")
        canvas.drawRightString(192 * mm, 12 * mm, f"Página {doc.page}")
        canvas.restoreState()

    document.build(story, onFirstPage=background, onLaterPages=background)
    return output.getvalue()
