"""Explicit platform visits and ordered post-alert milestones; no inferred conversions."""

import json
import sqlite3
from datetime import UTC, datetime, timedelta
from pathlib import Path
from statistics import median
from zoneinfo import ZoneInfo

from .casos import ESQUEMA

KINDS = {
    "platform_login",
    "platform_logout",
    "process_viewed",
    "eligible_step_completed",
    "autorizacion_otorgada",
}
ALERTS = {"invitacion_enviada", "colador_entered", "colador_signal"}


def parse_time(value):
    try:
        parsed = datetime.fromisoformat(value)
        # Existing SQLite dates use Chile local time without an offset.
        if parsed.tzinfo:
            return parsed.astimezone(UTC).replace(tzinfo=None)
        return (
            parsed.replace(tzinfo=ZoneInfo("America/Santiago")).astimezone(UTC).replace(tzinfo=None)
        )
    except (TypeError, ValueError):
        return None


def record(db_path, run, kind, *, key, at=None, **detail):
    if kind not in KINDS:
        raise ValueError("Evento de plataforma no reconocido.")
    Path(db_path).parent.mkdir(parents=True, exist_ok=True)
    with sqlite3.connect(db_path) as con:
        con.executescript(
            ESQUEMA
            + """
            CREATE TABLE IF NOT EXISTS platform_event_keys (event_key TEXT PRIMARY KEY);
        """
        )
        inserted = con.execute(
            "INSERT OR IGNORE INTO platform_event_keys VALUES (?)", (key,)
        ).rowcount
        if inserted:
            con.execute(
                "INSERT INTO eventos(run,fecha,canal,tipo,detalle) VALUES (?,?,?,?,?)",
                (
                    run,
                    at or datetime.now(UTC).isoformat(),
                    "Web ChileAtiende",
                    kind,
                    json.dumps(detail, ensure_ascii=False),
                ),
            )


def report(people, events, now=None):
    reference = (parse_time(now) if now else None) or datetime.now(UTC).replace(tzinfo=None)
    rows = []
    for person in people:
        history = sorted(
            [
                (at, event)
                for event in events
                if event["run"] == person["run"]
                if (at := parse_time(event["fecha"])) is not None and at <= reference
            ],
            key=lambda pair: pair[0],
        )
        alert = next((at for at, event in history if event["tipo"] in ALERTS), None)
        if alert is None:
            continue
        visits = {}
        for at, event in history:
            if at >= alert and event["tipo"] == "platform_login":
                session = event.get("datos", {}).get("session_id")
                if session:
                    visits.setdefault(session, at)
        logins = sorted(visits.values())
        entered = logins[0] if logins else None
        consent = next(
            (
                at
                for at, event in history
                if entered and at >= entered and event["tipo"] == "autorizacion_otorgada"
            ),
            None,
        )
        progress = next(
            (
                at
                for at, event in history
                if consent
                and at >= consent
                and event["tipo"] == "eligible_step_completed"
                and event.get("datos", {}).get("possible") is True
                and event.get("datos", {}).get("step_id") not in (None, "", "G0")
            ),
            None,
        )
        views = [
            at
            for at, event in history
            if entered and at >= entered and event["tipo"] == "process_viewed"
        ]
        rows.append(
            {
                "run": person["run"],
                "name": person["name"],
                "status": person.get("status", "active"),
                "alert": alert,
                "entered": entered,
                "consent": consent,
                "progress": progress,
                "logins": logins,
                "sessions": len(logins),
                "views": len(views),
                "last_view": max(views) if views else None,
                "last_login": logins[-1] if logins else None,
                "away_days": (reference - logins[-1]).days if logins else None,
                "return_hours": (logins[-1] - logins[-2]).total_seconds() / 3600
                if len(logins) > 1
                else None,
            }
        )
    counts = [
        sum(row[field] is not None for row in rows)
        for field in ("alert", "entered", "consent", "progress")
    ]
    returning = [row for row in rows if row["sessions"] > 1]
    gaps = [row["return_hours"] for row in returning]
    retention = []
    for days in (7, 30):
        cohort = [
            row
            for row in rows
            if row["entered"] and reference - row["entered"] >= timedelta(days=days)
        ]
        retained = sum(
            any(login <= row["entered"] + timedelta(days=days) for login in row["logins"][1:])
            for row in cohort
        )
        retention.append(
            {
                "days": days,
                "eligible": len(cohort),
                "returned": retained,
                "percent": round(100 * retained / len(cohort)) if cohort else None,
            }
        )
    daily = []
    for offset in reversed(range(14)):
        day = reference.replace(tzinfo=UTC).astimezone(ZoneInfo("America/Santiago")).date()
        day -= timedelta(days=offset)
        daily.append(
            {
                "Día": day.isoformat(),
                "Personas que ingresaron": sum(
                    any(
                        login.replace(tzinfo=UTC).astimezone(ZoneInfo("America/Santiago")).date()
                        == day
                        for login in row["logins"]
                    )
                    for row in rows
                ),
            }
        )
    return {
        "people": rows,
        "counts": counts,
        "returning": len(returning),
        "median_return_hours": median(gaps) if gaps else None,
        "views": sum(row["views"] for row in rows),
        "retention": retention,
        "daily": daily,
        "reference": reference,
    }


def seed_demo(db_path, state, profiles):
    """Add an explicit, repeatable usage scenario only to the isolated officer demo."""
    from . import reglas

    with sqlite3.connect(db_path) as con:
        exists = con.execute(
            "SELECT 1 FROM sqlite_master WHERE name='platform_event_keys'"
        ).fetchone()
        if (
            exists
            and con.execute(
                "SELECT 1 FROM platform_event_keys WHERE event_key='usage-demo-v1:ready'"
            ).fetchone()
        ):
            return
    start = parse_time(state["clock"]["start"])
    for index, person in enumerate(state["people"]):
        if index % 5 == 0:
            continue
        run = person["run"]
        first = start + timedelta(hours=8 + index % 24)

        def add(kind, suffix, at, *, run=run, **detail):
            record(
                db_path,
                run,
                kind,
                key=f"usage-demo-v1:{run}:{suffix}",
                at=at.replace(tzinfo=UTC).isoformat(),
                simulated=True,
                **detail,
            )

        sessions = [first]
        if index % 2:
            sessions.append(first + timedelta(days=3 + index % 6))
        if index % 4 == 1:
            sessions.append(start + timedelta(days=18, hours=index % 12))
        for number, at in enumerate(sessions):
            session = f"demo:{run}:{number}"
            add("platform_login", f"login:{number}", at, session_id=session)
            if index % 5 != 1:
                add(
                    "process_viewed",
                    f"view:{number}",
                    at + timedelta(minutes=5),
                    session_id=session,
                    benefit="PGU",
                )
        if index % 5 != 1:
            add("autorizacion_otorgada", "consent", first + timedelta(minutes=4))
            diagnosis = reglas.diagnosticar(profiles[run])
            if diagnosis.pgu.resultado == reglas.ELEGIBLE and index % 2:
                add(
                    "eligible_step_completed",
                    "step",
                    first + timedelta(days=2),
                    benefit="PGU",
                    possible=True,
                    step_id="G1",
                    message="Avance declarado en un trámite posible (simulación)",
                )
    with sqlite3.connect(db_path) as con:
        con.execute("INSERT OR IGNORE INTO platform_event_keys VALUES ('usage-demo-v1:ready')")
