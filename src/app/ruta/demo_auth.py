"""Explicit demo-only sign-in for the synthetic dataset; never contacts ClaveÚnica."""

import hmac
import re

DEMO_PASSWORD = "demo2026"


def normalize_run(value: str) -> str:
    compact = re.sub(r"[.\s-]", "", value).upper()
    if not re.fullmatch(r"[1-9]\d{6,8}[0-9K]", compact):
        raise ValueError("Ingresa un RUN válido, con su dígito verificador.")
    body, digit = compact[:-1], compact[-1]
    check = 11 - sum(int(n) * (2 + index % 6) for index, n in enumerate(reversed(body))) % 11
    expected = "0" if check == 11 else "K" if check == 10 else str(check)
    if digit != expected:
        raise ValueError("Revisa el dígito verificador del RUN.")
    return f"{body}-{digit}"


def authenticate(run: str, password: str, allowed_runs) -> str:
    normalized = normalize_run(run)
    if normalized not in allowed_runs or not hmac.compare_digest(
        password.encode("utf-8"), DEMO_PASSWORD.encode("utf-8")
    ):
        raise ValueError(
            "El RUN o la clave de demostración no coinciden. Usa los datos de ejemplo."
        )
    return normalized
