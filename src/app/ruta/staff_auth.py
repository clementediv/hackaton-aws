"""Public fictitious officer accounts for local demonstrations only."""

import hmac

DEMO_PASSWORD = "Ejecutivo2026!"
DEMO_ACCOUNTS = {
    "ejecutivo.rm@example.com": {"name": "Carolina Soto", "role": "Ejecutiva de atención"},
    "social.rm@example.com": {"name": "Daniel Fuentes", "role": "Asistente social"},
}


def authenticate(email: str, password: str) -> str:
    normalized = email.strip().casefold()
    if normalized not in DEMO_ACCOUNTS or not hmac.compare_digest(
        password.encode("utf-8"), DEMO_PASSWORD.encode("utf-8")
    ):
        raise ValueError("El correo o la clave no coinciden. Revisa los datos de demostración.")
    return normalized
