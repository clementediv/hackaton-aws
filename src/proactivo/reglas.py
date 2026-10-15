"""Deterministic evaluation of catalog requirements stored as data.

A requirement is `{"campo", "op", "valor", "texto"}`. A missing field means a
missing record: the requirement cannot be evaluated and the person is not
contacted as eligible. The LLM never takes part in this decision.
"""

import calendar
from dataclasses import dataclass, field
from datetime import date, timedelta
from decimal import Decimal
from typing import Any

OPERADORES = {
    ">=": lambda a, b: a >= b,
    "<=": lambda a, b: a <= b,
    ">": lambda a, b: a > b,
    "<": lambda a, b: a < b,
    "==": lambda a, b: a == b,
    "!=": lambda a, b: a != b,
    "in": lambda a, b: a in b,
}


def _plain(value: Any) -> Any:
    """DynamoDB returns Decimal; rules compare plain ints/floats."""
    if isinstance(value, Decimal):
        return int(value) if value == value.to_integral_value() else float(value)
    if isinstance(value, list | set | tuple):
        return [_plain(v) for v in value]
    return value


def add_years(d: date, years: int) -> date:
    year = d.year + years
    return date(year, d.month, min(d.day, calendar.monthrange(year, d.month)[1]))


def full_years(since: date, ref: date) -> int:
    return ref.year - since.year - ((ref.month, ref.day) < (since.month, since.day))


def derived_fields(person: dict, ref: date) -> dict:
    """Stored attributes plus the ones computed at the evaluation date."""
    values = {k: _plain(v) for k, v in person.items()}
    if birth := values.get("fecha_nacimiento"):
        values["edad"] = full_years(date.fromisoformat(birth), ref)
    if married := values.get("fecha_matrimonio"):
        values["anios_casado"] = full_years(date.fromisoformat(married), ref)
    return values


@dataclass
class Evaluacion:
    beneficio_id: str
    cumple: bool | None  # None: a record is missing
    motivos: list[str] = field(default_factory=list)


def evaluate(person: dict, benefit: dict, ref: date) -> Evaluacion:
    values = derived_fields(person, ref)
    result = Evaluacion(benefit["beneficio_id"], True)
    for req in benefit["requisitos"]:
        text = req.get("texto", req["campo"])
        current = values.get(req["campo"])
        if current is None:
            result.motivos.append(f"Falta antecedente: {text}")
            if result.cumple:
                result.cumple = None
            continue
        if OPERADORES[req["op"]](current, _plain(req["valor"])):
            result.motivos.append(f"Cumple: {text}")
        else:
            result.motivos.append(f"No cumple: {text}")
            result.cumple = False
    return result


def excluded(person: dict, benefit: dict) -> str | None:
    """Reason not to contact the person about this benefit at all."""
    if person.get("fallecido"):
        return "Persona fallecida"
    if benefit["beneficio_id"] in (person.get("beneficios_vigentes") or []):
        return "Ya recibe el beneficio"
    return None


def eligible_from(person: dict, benefit: dict, ref: date) -> date | None:
    """First date within the anticipation window when the person meets every
    requirement, or None. Only age-driven requirements change with time."""
    days = int(_plain(benefit.get("anticipar_dias") or 0))
    if not days or not person.get("fecha_nacimiento"):
        return None
    if evaluate(person, benefit, ref).cumple:
        return ref
    birth = date.fromisoformat(person["fecha_nacimiento"])
    limit = ref + timedelta(days=days)
    candidates = sorted(
        add_years(birth, int(_plain(r["valor"])) + (1 if r["op"] == ">" else 0))
        for r in benefit["requisitos"]
        if r["campo"] == "edad" and r["op"] in (">=", ">")
    )
    for when in candidates:
        if ref < when <= limit and evaluate(person, benefit, when).cumple:
            return when
    return None


def changed_fields(old: dict | None, new: dict, benefit: dict, ref: date) -> list[str]:
    """Human-readable list of relevant changes that explain a detection."""
    if old is None:
        return []
    before, after = derived_fields(old, ref), derived_fields(new, ref)
    out = []
    for campo in dict.fromkeys(r["campo"] for r in benefit["requisitos"]):
        if before.get(campo) != after.get(campo):
            label = LABELS.get(campo, campo)
            out.append(f"{label}: {_show(before.get(campo))} → {_show(after.get(campo))}")
    return out


LABELS = {
    "edad": "edad",
    "num_hijos": "número de hijos",
    "estado_civil": "estado civil",
    "anios_casado": "años de matrimonio",
    "tramo_rsh": "tramo del Registro Social de Hogares",
    "percentil_pfp": "percentil de focalización previsional",
    "residencia_cumple": "requisito de residencia",
    "trabaja": "trabaja",
    "accidente_laboral": "accidente laboral registrado",
    "sexo": "sexo registral",
}


def _show(value: Any) -> str:
    if value is None:
        return "sin dato"
    if isinstance(value, bool):
        return "sí" if value else "no"
    return str(value)
