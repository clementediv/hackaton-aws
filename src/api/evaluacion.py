"""Evaluación fuera del LLM, sin importar Streamlit ni SQLite."""

import json
import os
from dataclasses import asdict
from pathlib import Path

DATA_DIR = Path(
    os.environ.setdefault(
        "DATA_DIR", str(Path(__file__).resolve().parents[2] / "data/raw/dataset_A_participantes")
    )
)

from src.app.ruta import config, reglas  # noqa: E402


def evaluar(case):
    if not case.can_read_profile:
        raise PermissionError("Se requiere invitación aceptada y autorización.")
    profiles = json.loads((DATA_DIR / "perfiles.json").read_text())
    profile = next((p for p in profiles if p["run"] == case.run), None)
    result = {
        "source": config.FUENTE_PGU,
        "sources_verified": False,
        "reference_date": config.FECHA_REFERENCIA.isoformat(),
        "preliminary": True,
    }
    if profile is None:
        return {**result, "status": "sin_registro"}
    # Convert dates to ISO before writing to DynamoDB.
    return json.loads(
        json.dumps(
            {
                **result,
                "pgu": asdict(reglas.evaluar_pgu(profile)),
                "milestones": asdict(reglas.calcular_hitos(profile)),
            },
            default=str,
        )
    )
