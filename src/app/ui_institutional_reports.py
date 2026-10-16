"""Institutional overview and automatic downloadable PDF in the officer workspace."""

from datetime import datetime
from html import escape
from pathlib import Path
from zoneinfo import ZoneInfo

import pandas as pd
import streamlit as st
from ruta import engagement, trazabilidad
from ruta.institutional_pdf import generate_pdf
from ruta.institutional_reports import build_report, commune_of
from ruta.report_heatmap import render_heatmap

ASSETS = Path(__file__).parent / "assets"


def render(state, db_file, *, demo=False, profiles=None):
    st.html("<style>" + (ASSETS / "institutional-reports.css").read_text() + "</style>")
    st.html(
        '<div class="report-hero"><div class="report-eyebrow">INTELIGENCIA TERRITORIAL</div>'
        "<h2>Información para acercar los beneficios.</h2>"
        "<p>Una mirada compartida para municipalidades y ministerios: dónde acompañar, "
        "qué brechas atender y cómo dar continuidad.</p></div>"
    )
    with st.container(border=True, key="institutional_report_controls"):
        recipient, name = st.columns([1, 2])
        audience = recipient.selectbox(
            "Destinatario", ["Municipalidad", "Ministerio"], key="institutional_audience"
        )
        institution = name.text_input(
            "Nombre de la institución",
            max_chars=120,
            placeholder="Ej.: Municipalidad de Santiago",
            key="institutional_name",
        )
        options = sorted({commune_of(p) for p in state["people"]})
        communes = st.multiselect(
            "Comunas del reporte", options, default=options, key="institutional_communes"
        )
        st.caption(
            "El documento se actualiza automáticamente con la campaña y el territorio elegidos."
        )
    if demo:
        engagement.seed_demo(db_file, state, profiles)
    data = build_report(
        state,
        trazabilidad.load_events(db_file),
        audience=audience,
        institution=institution,
        communes=communes,
        demo=demo,
        profiles=profiles,
    )
    cutoff = datetime.fromisoformat(data["cutoff"]).astimezone(ZoneInfo("America/Santiago"))
    mode = "Escenario simulado" if demo else "Registros de la aplicación"
    st.caption(f"{mode} · Datos sintéticos · Corte: {cutoff:%d/%m/%Y %H:%M} (Santiago)")
    st.html(
        '<div class="report-metrics">'
        + "".join(
            f'<div class="report-metric"><span>{label}</span><strong>{data[key]}</strong>'
            f"<small>{detail}</small></div>"
            for key, label, detail in [
                ("total", "Personas de la campaña", "Únicas en el territorio elegido"),
                ("pending", "Por contactar", "Sin respuesta confirmada"),
                ("guidance", "Esperan orientación", "Respondieron; necesitan acompañamiento"),
                ("progress", "Avances declarados", "Requieren validación del organismo"),
            ]
        )
        + "</div>"
    )
    chart, summary = st.columns([1.4, 1], gap="large")
    with chart:
        st.markdown("#### Del aviso al avance declarado")
        denominator = next(iter(data["stages"].values()))
        st.html(
            '<div class="report-bars">'
            + "".join(
                f'<div class="report-stage"><div><span>{label}</span><b>{value}</b></div>'
                f'<div class="report-track"><span style="width:'
                f'{100 * value / denominator if denominator else 0}%"></span></div></div>'
                for label, value in data["stages"].items()
            )
            + "</div>"
        )
        st.caption("Hitos en orden temporal. Sin alerta fechada no se infiere ingreso ni avance.")
    with summary:
        st.markdown("#### Focos de gestión")
        for finding in data["findings"]:
            st.html(f'<div class="report-finding">{escape(finding)}</div>')
    st.markdown("#### Dónde concentrar la atención en terreno")
    st.image(render_heatmap(data["heatmap"]), use_container_width=True)
    st.caption(
        f"{data['heatmap']['mapped']} ubicaciones simuladas publicables. " + data["heatmap"]["note"]
    )
    st.caption(data["heatmap"]["source"])
    st.markdown("#### Distribución territorial")
    if data["territory"]:
        st.dataframe(
            pd.DataFrame(data["territory"]).rename(
                columns={
                    "commune": "Comuna",
                    "people": "Personas",
                    "pending": "Por contactar",
                    "guidance": "Orientación",
                    "started": "Inicio registrado",
                    "progress": "Avance declarado",
                    "declined": "Declinó",
                }
            ),
            hide_index=True,
            use_container_width=True,
        )
    else:
        st.info(
            "No hay casos en el territorio seleccionado. El PDF documentará esta ausencia de datos."
        )
    with st.container(border=True, key="institutional_report_download"):
        copy, download = st.columns([2, 1], vertical_alignment="center")
        copy.markdown("**Tu reporte está listo para compartir**")
        copy.caption(
            "Resumen ejecutivo, indicadores, detalle territorial y fuentes. Solo cifras agregadas."
        )
        download.download_button(
            "Descargar reporte PDF",
            generate_pdf(data),
            file_name=f"reporte-{audience.lower()}-{cutoff:%Y%m%d}.pdf",
            mime="application/pdf",
            type="primary",
            use_container_width=True,
            key="institutional_pdf",
        )
    st.caption(data["limitation"])
    with st.expander("Fuentes y alcance del reporte"):
        st.write(data["source"])
        st.write(
            "Las comunas y contactos provienen de la capa territorial sintética del MVP. "
            "El informe no incluye historiales AWS, nombres, RUN ni datos de contacto. "
            "La generación y descarga no envían el documento a ninguna institución."
        )
