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


DECEASED = "Persona fallecida"
RECEIVES = "Ya recibe el beneficio"


def excluded(person: dict, benefit: dict) -> str | None:
    """Reason not to invite the person to this benefit (risk notices aside)."""
    if person.get("fallecido"):
        return DECEASED
    if benefit["beneficio_id"] in (person.get("beneficios_vigentes") or []):
        return RECEIVES
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


def add_months(d: date, months: int) -> date:
    total = d.month - 1 + months
    year, month = d.year + total // 12, total % 12 + 1
    return date(year, month, min(d.day, calendar.monthrange(year, month)[1]))


def months_old(birth: date, ref: date) -> int:
    months = (ref.year - birth.year) * 12 + ref.month - birth.month
    return months - (1 if ref.day < birth.day else 0)


@dataclass
class Aviso:
    """A dated notice before an age-driven benefit opens."""

    etapa: dict  # catalog notice: {"id", "meses", "titulo", "motivo"}
    apertura: date  # the application opens (a milestone, not a deadline)
    acceso: date  # the age requirement is met
    faltantes: list[str]


def upcoming_notice(person: dict, benefit: dict, ref: date) -> Aviso | None:
    """Latest catalog notice the person has reached before the access age.

    Sent to whoever meets, or still lacks records for, the other requirements:
    the notice helps them gather what is missing. A requirement that is not
    met (e.g. top 10% income) means no notice.
    """
    notices = benefit.get("avisos_previos") or []
    if not notices or not person.get("fecha_nacimiento"):
        return None
    ages = [
        int(_plain(r["valor"]))
        for r in benefit["requisitos"]
        if r["campo"] == "edad" and r["op"] == ">="
    ]
    if not ages:
        return None
    birth = date.fromisoformat(person["fecha_nacimiento"])
    access = add_years(birth, max(ages))
    if ref >= access:
        return None
    months = months_old(birth, ref)
    due = [n for n in notices if months >= int(_plain(n["meses"]))]
    if not due:
        return None
    result = evaluate(person, benefit, access)
    if result.cumple is False:
        return None
    missing = [
        m.removeprefix("Falta antecedente: ") for m in result.motivos if m.startswith("Falta")
    ]
    opening = add_months(birth, int(_plain(benefit.get("apertura_meses") or max(ages) * 12)))
    return Aviso(due[-1], opening, access, missing)


def risks_triggered(person: dict, benefit: dict) -> list[dict]:
    """Loss-risk notices for someone who already receives the benefit."""
    values = {k: _plain(v) for k, v in person.items()}
    out = []
    for risk in benefit.get("riesgos") or []:
        current = values.get(risk["campo"])
        if current is not None and OPERADORES[risk["op"]](current, _plain(risk["valor"])):
            out.append(risk)
    return out


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


def personal_reason(old: dict | None, new: dict, benefit: dict, ref: date) -> str | None:
    """The same relevant change, addressed to the person ("Usted cumplió 65 años")."""
    if old is None:
        return None
    before, after = derived_fields(old, ref), derived_fields(new, ref)
    phrases = []
    for campo in dict.fromkeys(r["campo"] for r in benefit["requisitos"]):
        was, now = before.get(campo), after.get(campo)
        if was == now:
            continue
        if campo == "edad":
            phrases.append(f"usted cumplió {now} años")
        elif campo == "num_hijos" and (now or 0) > (was or 0):
            phrases.append("registramos el nacimiento de su hijo o hija")
        elif campo == "estado_civil":
            phrases.append(
                "registramos su matrimonio"
                if now == "casado"
                else f"su estado civil cambió a {now}"
            )
        elif campo == "accidente_laboral" and now:
            phrases.append("registramos un accidente laboral")
        elif campo == "tramo_rsh":
            phrases.append(f"su Registro Social de Hogares indica ahora el tramo del {now}%")
        elif campo == "trabaja" and now:
            phrases.append("registramos que usted se encuentra trabajando")
        else:
            phrases.append(f"cambió su {LABELS.get(campo, campo)}")
    if not phrases:
        return None
    text = "; ".join(phrases)
    return text[0].upper() + text[1:] + "."


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
