"""Authorized lookup of synthetic citizen profiles from dataset A."""

import json
import re
from pathlib import Path

from src.contracts import Case, Profile

DEFAULT_DATASET_PATH = (
    Path(__file__).resolve().parents[2] / "data/raw/dataset_A_participantes/perfiles.json"
)


def normalize_run(run: str) -> str:
    """Accept a RUN with/without thousands separators and validate its DV."""
    if not isinstance(run, str):
        raise ValueError("El RUN debe ser texto.")
    value = re.sub(r"\s", "", run).upper()
    if re.fullmatch(r"[0-9]{8,10}|[0-9]{1,3}(?:\.[0-9]{3}){2}[0-9K]", value):
        value = value[:-1] + "-" + value[-1]
    elif re.fullmatch(r"[0-9]{7,9}K", value):
        value = value[:-1] + "-K"
    if not re.fullmatch(r"(?:[0-9]{7,9}|[0-9]{1,3}(?:\.[0-9]{3}){2})-[0-9K]", value):
        raise ValueError("Formato de RUN inválido; use dígitos y guion con dígito verificador.")
    number, check_digit = value.replace(".", "").split("-")
    total = sum(int(digit) * (2 + index % 6) for index, digit in enumerate(reversed(number)))
    remainder = 11 - total % 11
    expected = "0" if remainder == 11 else "K" if remainder == 10 else str(remainder)
    if check_digit != expected:
        raise ValueError("Dígito verificador de RUN inválido.")
    return f"{number}-{check_digit}"


class ProfileRepository:
    """Load the dataset lazily, only after checking the trusted case context.

    Keep one instance per process to reuse the validated index. Returned profiles
    are deep copies so callers cannot mutate the shared nested lists.
    """

    def __init__(self, dataset_path: str | Path = DEFAULT_DATASET_PATH) -> None:
        self.dataset_path = Path(dataset_path)
        self._profiles: dict[str, Profile] | None = None

    def _load(self) -> dict[str, Profile]:
        raw = json.loads(self.dataset_path.read_text(encoding="utf-8"))
        if not isinstance(raw, list):
            raise ValueError("El dataset de perfiles debe ser una lista.")
        profiles: dict[str, Profile] = {}
        for record in raw:
            profile = Profile.model_validate(record)
            normalized = normalize_run(profile.run)
            if normalized in profiles:
                raise ValueError("El dataset contiene RUN duplicados.")
            profiles[normalized] = profile
        return profiles

    def lookup(self, run: str, *, case: Case | None = None) -> Profile | None:
        # Check authorization before reading the file or revealing whether a RUN exists.
        if case is None or not case.can_read_profile:
            raise PermissionError("Se requiere autorización del caso para consultar el perfil.")
        normalized = normalize_run(run)
        if normalize_run(case.run) != normalized:
            raise PermissionError("El RUN consultado no corresponde al caso autorizado.")
        if self._profiles is None:
            self._profiles = self._load()
        profile = self._profiles.get(normalized)
        return profile.model_copy(deep=True) if profile is not None else None


_default_repository = ProfileRepository()


def consultar_perfil(
    run: str,
    *,
    case: Case | None = None,
    repository: ProfileRepository | None = None,
) -> Profile | None:
    """Return a typed profile, or None if a valid authorized RUN is not found.

    The application supplies `case`; it must never be supplied by the LLM as a
    tool argument. A missing/declined authorization raises PermissionError.
    """
    return (repository or _default_repository).lookup(run, case=case)
