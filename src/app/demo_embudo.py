"""Independent local visual test: uv run --group app streamlit run src/app/demo_embudo.py."""

import streamlit as st
from ruta.datos import cargar_perfiles
from ui_embudo import render_campaign_lab

st.set_page_config(page_title="Demo · Embudo ChileAtiende", page_icon="📊", layout="wide")
st.markdown("# ChileAtiende a Tiempo · Backend del embudo")
st.caption("Laboratorio de simulación · Región Metropolitana · datos ficticios")
render_campaign_lab(cargar_perfiles())
