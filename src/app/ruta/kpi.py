"""Next valid step within the deadline: the user's ≥75% goal, measured on the case log.

The deadline is a demo proposal, not an institutional one, and steps are declared
by the person or the officer: the agency has not confirmed them. Contact, opening
and «inicio» do not count. Design: 20-arquitectura/kpi-proximo-paso.md.
"""

import sqlite3
from collections import Counter
from datetime import UTC, datetime, timedelta
from pathlib import Path

from .engagement import parse_time

GOAL = 0.75
DEADLINE_DAYS = 30
ACCEPT = {"invitacion_aceptada", "colador_answered", "colador_contacted", "colador_started"}
DECLINE = {"invitacion_rechazada", "colador_declined"}
STEP = {"paso_completado", "eligible_step_completed"}
INFORMATIVE = {"G0", "", None}
ON_TIME, LATE, EXPIRED, OPEN = "en_plazo", "fuera_de_plazo", "vencido", "en_curso"
LABELS = {
    ON_TIME: "Dio el paso dentro del plazo",
    LATE: "Dio el paso fuera del plazo",
    EXPIRED: "Plazo vencido sin paso",
    OPEN: "Plazo vigente, sin paso todavía",
}


def reference_time(db_path: str | Path) -> datetime:
    """The later of now and the funnel's simulated clock (naive UTC)."""
    now = datetime.now(UTC).replace(tzinfo=None)
    path = Path(db_path)
    if not path.exists():
        return now
    con = sqlite3.connect(path)
    try:
        if not con.execute(
            "SELECT 1 FROM sqlite_master WHERE type='table' AND name='funnel_clock'"
        ).fetchone():
            return now
        row = con.execute("SELECT now FROM funnel_clock WHERE id=1").fetchone()
    finally:
        con.close()
    clock = parse_time(row[0]) if row else None
    return max(now, clock) if clock else now


def _step(event: dict) -> str | None:
    data = event.get("datos") or {}
    if event["tipo"] == "eligible_step_completed" and data.get("possible") is not True:
        return None
    return data.get("paso") or data.get("step_id")


def outcomes(events: list[dict], now: datetime, deadline_days: int = DEADLINE_DAYS) -> list[dict]:
    """One row per person of the cohort: confirmed contact that was not declined."""
    by_run: dict[str, list] = {}
    for e in events:
        if at := parse_time(e["fecha"]):
            by_run.setdefault(e["run"], []).append((at, e))
    rows = []
    for run, history in by_run.items():
        history.sort(key=lambda item: item[0])
        answers = [(at, e["tipo"]) for at, e in history if e["tipo"] in ACCEPT | DECLINE]
        if not answers or answers[-1][1] in DECLINE:
            continue
        last_decline = max((at for at, kind in answers if kind in DECLINE), default=None)
        contact = next(
            at
            for at, kind in answers
            if kind in ACCEPT and (last_decline is None or at >= last_decline)
        )
        done: dict[str, tuple[datetime, str]] = {}
        for at, e in history:
            step = _step(e) if e["tipo"] in STEP else None
            if step not in INFORMATIVE and at >= contact:
                done.setdefault(step, (at, (e.get("datos") or {}).get("titulo", "") or step))
            elif e["tipo"] == "paso_reabierto":
                done.pop((e.get("datos") or {}).get("paso"), None)
        deadline = contact + timedelta(days=deadline_days)
        first = min(done.values(), default=None)
        if first:
            state = ON_TIME if first[0] <= deadline else LATE
        else:
            state = EXPIRED if now > deadline else OPEN
        rows.append(
            {
                "run": run,
                "contacto": contact,
                "plazo": deadline,
                "paso": first[0] if first else None,
                "paso_titulo": first[1] if first else "",
                "estado": state,
                "plazo_cumplido": now > deadline,
            }
        )
    return sorted(rows, key=lambda r: r["contacto"])


def summary(rows: list[dict]) -> dict:
    """KPI over the cohort whose deadline already passed; provisional over all."""
    mature = [r for r in rows if r["plazo_cumplido"]]
    on_time = sum(r["estado"] == ON_TIME for r in mature)
    provisional = sum(r["estado"] == ON_TIME for r in rows)
    return {
        "cohorte": len(rows),
        "plazo_cumplido": len(mature),
        "kpi": on_time / len(mature) if mature else None,
        "provisional": provisional / len(rows) if rows else None,
        "en_plazo_total": provisional,
        "meta": GOAL,
        "por_estado": Counter(r["estado"] for r in rows),
    }
