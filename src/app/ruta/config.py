"""Parámetros del MVP. Todo valor normativo vive aquí, con su fuente.

La IA nunca calcula estos valores: los lee el motor de reglas.
"""
import os
from datetime import date
from pathlib import Path


# --- Datos ---------------------------------------------------------------
def _data_dir() -> Path:
    """DATA_DIR del entorno; si no, data/ del repo (src/app/ruta -> raíz); si no, la copia local de Johann."""
    if env := os.getenv("DATA_DIR"):
        return Path(env)
    en_repo = Path(__file__).resolve().parents[3] / "data" / "raw" / "dataset_A_participantes"
    if (en_repo / "perfiles.json").exists():
        return en_repo
    return Path(r"c:\Users\Johann\Documents\hackathon\hackaton-aws\data\raw\dataset_A_participantes")


DATA_DIR = _data_dir()
PERFILES_PATH = DATA_DIR / "perfiles.json"

# Fecha de referencia del dataset (README: 2026-10-08). Las reglas se evalúan a esta fecha.
FECHA_REFERENCIA = date.fromisoformat(os.getenv("FECHA_REFERENCIA", "2026-10-08"))

# Base local de seguimiento de casos (invitaciones, autorizaciones, pasos, historial).
DB_PATH = Path(os.getenv("CASOS_DB", Path(__file__).resolve().parent.parent / "casos.db"))

# --- Parámetros PGU (ficha ChileAtiende, vigentes a oct-2026) --------------
FUENTE_PGU = "https://www.chileatiende.gob.cl/fichas/102077-pension-garantizada-universal-pgu"
FUENTE_PGU_AUMENTO = "https://www.chileatiende.gob.cl/fichas/130457-aumento-de-la-pension-garantizada-universal-pgu"

PGU = {
    "monto_max_65_74": 231_732,       # 65 a 74 años
    "monto_max_75_mas": 250_275,      # 75+ desde septiembre 2026
    "edad_tramo_superior": 75,
    "pension_inferior": 789_139,      # hasta aquí PGU completa
    "pension_superior": 1_252_602,    # desde aquí no corresponde PGU
    "pfp_percentil_max": 90,          # no pertenecer al 10% de mayores ingresos
    "edad_acceso": 65,
    "apertura_solicitud": (64, 9),    # años, meses
    "residencia_anios_desde_20": 20,
    "residencia_anios_ultimos_5": 4,
}

# --- Hitos de jubilación (PPT ChileAtiende a Tiempo) -----------------------
EDAD_LEGAL_VEJEZ = {"F": 60, "M": 65}
MESES_INVITACION_ANTICIPADA = 12      # "aprox. un año antes de la edad legal"

# --- Fuentes para la ruta (orientativas) ----------------------------------
FUENTES = {
    "pgu": FUENTE_PGU,
    "pgu_aumento": FUENTE_PGU_AUMENTO,
    "rsh": "https://www.registrosocial.gob.cl/",
    "spensiones": "https://www.spensiones.cl/",
    "chileatiende": "https://www.chileatiende.gob.cl/",
    "pdi": "https://www.pdichile.cl/",
    "dataset": "Dataset A (sintético), fecha de referencia 2026-10-08",
}

CANALES = ["Web ChileAtiende", "WhatsApp", "Call center 101", "Sucursal ChileAtiende"]

# --- IA generativa (opcional) ---------------------------------------------
# Si BEDROCK_MODEL_ID está vacío, el asistente usa respuestas basadas en plantillas.
BEDROCK_MODEL_ID = os.getenv("BEDROCK_MODEL_ID", "")
AWS_REGION = os.getenv("AWS_REGION", "us-east-1")

# Remitente SES del resumen de Mi Gobierno. Vacío o sin verificar: se envía desde la
# misma casilla verificada del destinatario (válido en el sandbox de SES).
SES_SENDER = os.getenv("REMITENTE", "")
