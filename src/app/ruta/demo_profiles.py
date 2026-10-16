"""Extra citizen demo account, separate from the original 500-person dataset."""

from .datos import cargar_perfiles

CONSENT_DEMO_LOGIN = "123456789"
CONSENT_DEMO_RUN = "12345678-9"


def consent_demo_profile() -> dict:
    """Return a fresh fictitious identity with unconfirmed personal records."""
    return {
        "run": CONSENT_DEMO_RUN,
        "registro_civil": {
            "run_formateado": "12.345.678-9",
            "nombres": "Persona",
            "apellido_paterno": "De",
            "apellido_materno": "Prueba",
            "fecha_nacimiento": "1961-01-01",
            "sexo": "F",
            "estado_civil": "sin_informacion",
            "tiene_conyuge_conviviente": False,
            "tiene_hijos": False,
            "fecha_defuncion": None,
            "estado": "no_fallecido",
        },
        "rsh": None,
        "residencia": None,
        "prevision": None,
        "pensiones_beneficios": [],
        "situacion_laboral": None,
    }


def load_citizen_profiles() -> dict[str, dict]:
    """Include the extra account only in citizen sign-in and personal chat."""
    return {**cargar_perfiles(), CONSENT_DEMO_RUN: consent_demo_profile()}
