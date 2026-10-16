"""Vector PDF with the exact aggregate snapshot displayed in the officer portal."""

from datetime import datetime
from html import escape
from io import BytesIO
from zoneinfo import ZoneInfo

from reportlab.lib import colors
from reportlab.lib.enums import TA_LEFT
from reportlab.lib.styles import ParagraphStyle, getSampleStyleSheet
from reportlab.lib.units import mm
from reportlab.platypus import (
    Flowable,
    KeepTogether,
    PageBreak,
    Paragraph,
    SimpleDocTemplate,
    Spacer,
    Table,
    TableStyle,
)

BLUE = colors.HexColor("#0d4d82")
TEAL = colors.HexColor("#087e8b")
INK = colors.HexColor("#173d59")
MUTED = colors.HexColor("#526879")
LIGHT = colors.HexColor("#eff5fa")


def generate_pdf(data):
    output = BytesIO()
    styles = getSampleStyleSheet()
    styles.add(
        ParagraphStyle(
            "ReportTitle",
            fontName="Helvetica-Bold",
            fontSize=27,
            leading=32,
            textColor=BLUE,
            spaceAfter=12,
        )
    )
    styles.add(
        ParagraphStyle(
            "ReportBody", fontName="Helvetica", fontSize=10, leading=15, textColor=INK, spaceAfter=8
        )
    )
    styles.add(
        ParagraphStyle(
            "ReportSmall", parent=styles["ReportBody"], fontSize=8, leading=11, textColor=MUTED
        )
    )
    styles.add(
        ParagraphStyle(
            "ReportHeading",
            parent=styles["ReportBody"],
            fontName="Helvetica-Bold",
            fontSize=14,
            leading=19,
            spaceBefore=17,
            spaceAfter=10,
        )
    )
    styles.add(
        ParagraphStyle(
            "ReportCell", parent=styles["ReportSmall"], fontSize=8, leading=11, alignment=TA_LEFT
        )
    )

    def text(value, style="ReportBody"):
        return Paragraph(escape(str(value)), styles[style])

    class StageBars(Flowable):
        def __init__(self):
            super().__init__()
            self.width = 174 * mm
            self.height = 42 * mm

        def draw(self):
            canvas = self.canv
            denominator = next(iter(data["stages"].values()))
            for i, (label, count) in enumerate(data["stages"].items()):
                y = self.height - 11 - i * 27
                canvas.setFillColor(INK)
                canvas.setFont("Helvetica", 9)
                canvas.drawString(0, y, label)
                canvas.setFillColor(LIGHT)
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
        topMargin=20 * mm,
        bottomMargin=22 * mm,
        title="Reporte institucional · ChileAtiende a Tiempo",
        author="ChileAtiende a Tiempo · Prototipo",
    )

    def date_label(value):
        return (
            datetime.fromisoformat(value)
            .astimezone(ZoneInfo("America/Santiago"))
            .strftime("%d/%m/%Y %H:%M (Santiago)")
        )

    mode = "ESCENARIO SIMULADO" if data["demo"] else "REGISTROS LOCALES · DATOS SINTÉTICOS"
    story = [
        text("CHILEATIENDE A TIEMPO  /  REPORTE INSTITUCIONAL", "ReportSmall"),
        Spacer(1, 5 * mm),
        text("Beneficios que llegan a tiempo", "ReportTitle"),
        text(data["institution"], "ReportHeading"),
        text(f"Destinatario: {data['audience']} · {mode}", "ReportSmall"),
        text(
            "Territorio: " + (", ".join(data["scope"]) or "Sin comunas seleccionadas"),
            "ReportSmall",
        ),
        text(
            f"Generado: {date_label(data['generated'])} · Corte: {date_label(data['cutoff'])}",
            "ReportSmall",
        ),
    ]
    cards = Table(
        [
            [
                text(str(data[key]), "ReportHeading")
                for key in ("total", "pending", "guidance", "progress")
            ],
            [
                text(label, "ReportSmall")
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
                ("BACKGROUND", (0, 0), (-1, -1), LIGHT),
                ("BOX", (0, 0), (-1, -1), 0.5, colors.white),
                ("LEFTPADDING", (0, 0), (-1, -1), 9),
                ("BOTTOMPADDING", (0, -1), (-1, -1), 12),
            ]
        )
    )
    story.extend([Spacer(1, 6 * mm), cards, text("Lectura ejecutiva", "ReportHeading")])
    story.extend(text(f"• {finding}") for finding in data["findings"])
    story.extend(
        [
            text("Del aviso al avance declarado", "ReportHeading"),
            StageBars(),
            text(
                "Porcentajes sobre personas con alerta fechada y eventos en orden temporal. "
                "No equivalen a beneficios entregados. Sin alerta fechada no se reconstruye "
                "el recorrido a partir del estado de contacto.",
                "ReportSmall",
            ),
        ]
    )
    if data["territory"]:
        story.append(PageBreak())
    story.append(text("Detalle territorial", "ReportHeading"))
    headers = ["Comuna", "Personas", "Por contactar", "Orientación", "Inicio", "Avance*", "Declinó"]
    rows = [[text(h, "ReportCell") for h in headers]]
    for row in data["territory"]:
        rows.append(
            [
                text(row[key], "ReportCell")
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
        rows.append([text("Sin casos", "ReportCell"), *[text("—", "ReportCell") for _ in range(6)]])
    table = Table(rows, colWidths=[42 * mm, *[22 * mm] * 6], repeatRows=1, hAlign="LEFT")
    table.setStyle(
        TableStyle(
            [
                ("BACKGROUND", (0, 0), (-1, 0), colors.HexColor("#dceaf5")),
                ("ROWBACKGROUNDS", (0, 1), (-1, -1), [colors.white, LIGHT]),
                ("VALIGN", (0, 0), (-1, -1), "TOP"),
                ("TOPPADDING", (0, 0), (-1, -1), 8),
                ("BOTTOMPADDING", (0, 0), (-1, -1), 8),
            ]
        )
    )
    story.extend(
        [
            table,
            text("*Avance declarado por la persona. Inicio: estado del colador.", "ReportSmall"),
        ]
    )
    if data["other"]:
        story.append(text(f"Otros estados o estados sin clasificar: {data['other']} personas."))
    story.append(
        KeepTogether(
            [
                text("Alcance y fuentes", "ReportHeading"),
                text(data["source"], "ReportSmall"),
                text(
                    "Comunas y contactos de la capa territorial sintética del MVP. "
                    "No incluye eventos AWS ni registros administrativos externos. "
                    "Contiene solo agregados; no incluye nombres, RUN ni datos de contacto.",
                    "ReportSmall",
                ),
                text(data["limitation"], "ReportSmall"),
            ]
        )
    )

    def footer(canvas, doc):
        canvas.saveState()
        canvas.setStrokeColor(colors.HexColor("#dce4eb"))
        canvas.line(18 * mm, 17 * mm, 192 * mm, 17 * mm)
        canvas.setFont("Helvetica", 8)
        canvas.setFillColor(MUTED)
        canvas.drawString(
            18 * mm, 12 * mm, "ChileAtiende a Tiempo · Prototipo con datos sintéticos"
        )
        canvas.drawRightString(192 * mm, 12 * mm, f"Página {doc.page}")
        canvas.restoreState()

    document.build(story, onFirstPage=footer, onLaterPages=footer)
    return output.getvalue()
