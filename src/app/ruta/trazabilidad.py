"""Case traceability: every contact, answer and step leaves an auditable record.

With synthetic data we cannot prove that the ≥75% next-step KPI is met. What we
can show is that each case keeps a complete trail (when, through which channel,
what happened and from which source), ready to measure the KPI in a pilot.
Reads the `eventos` log that cases (casos.py) and the funnel (colador.py) write.
"""

import csv
import io
import json
import sqlite3
from datetime import datetime
from pathlib import Path

LOCAL_SOURCE = "Caso (registro local)"
AWS_SOURCE = "Detección automática (AWS)"

EVENT_LABELS = {
    "colador_entered": "Inicio de seguimiento por este canal",
    "colador_attempt": "Intento de contacto",
    "colador_skipped": "Canal sin datos de contacto",
    "colador_opened": "Abrió el mensaje",
    "colador_answered": "La persona respondió",
    "colador_contacted": "Contacto confirmado",
    "colador_started": "Inició su trámite",
    "colador_declined": "Declinó el acompañamiento",
    "colador_queued": "Pendiente de atención en terreno",
    "colador_signal": "Nueva alerta en el caso",
    "invitacion_enviada": "Invitación enviada",
    "invitacion_aceptada": "Aceptó el acompañamiento",
    "invitacion_rechazada": "Rechazó el acompañamiento",
    "autorizacion_otorgada": "Autorizó el uso de sus datos",
    "autorizacion_revocada": "Revocó la autorización",
    "paso_completado": "Completó un paso del trámite",
    "paso_reabierto": "Paso reabierto",
    "consulta_asistente": "Consultó al asistente",
    "tramite_iniciado": "Inició su trámite",
}
CONFIRMED_CONTACT = {
    "colador_answered",
    "colador_contacted",
    "colador_started",
    "colador_declined",
    "invitacion_aceptada",
    "invitacion_rechazada",
}
NEXT_STEP = {"paso_completado", "colador_started", "tramite_iniciado"}


def load_events(db_path: str | Path) -> list[dict]:
    """Every event of the campaign database, oldest first."""
    path = Path(db_path)
    if not path.exists():
        return []
    con = sqlite3.connect(path)
    con.row_factory = sqlite3.Row
    try:
        exists = con.execute(
            "SELECT 1 FROM sqlite_master WHERE type='table' AND name='eventos'"
        ).fetchone()
        if not exists:
            return []
        rows = con.execute(
            "SELECT id, run, fecha, canal, tipo, detalle FROM eventos ORDER BY fecha, id"
        ).fetchall()
    finally:
        con.close()
    events = []
    for row in rows:
        detail = row["detalle"]
        try:
            detail = json.loads(detail) if detail else {}
        except (TypeError, ValueError):
            detail = {"texto": detail}
        events.append(
            {
                "run": row["run"],
                "fecha": row["fecha"],
                "canal": row["canal"] or "",
                "tipo": row["tipo"],
                "evento": EVENT_LABELS.get(row["tipo"], row["tipo"].replace("_", " ")),
                "detalle": _detail_text(detail),
                "origen": LOCAL_SOURCE,
            }
        )
    return events


# The funnel records skipped channels with internal names ("Sin employer").
CHANNEL_WORDS = {
    "Sin email": "Sin correo",
    "Sin phone": "Sin teléfono",
    "Sin employer": "Sin empleador",
}


def _detail_text(detail) -> str:
    if not isinstance(detail, dict):
        return str(detail or "")
    for key in ("reason", "motivo", "message", "titulo", "asunto", "texto", "label"):
        if detail.get(key):
            text = str(detail[key])
            return CHANNEL_WORDS.get(text, text)
    return ""


def aws_events(history: list[dict]) -> list[dict]:
    """ca-historial items (see aws_contactos.load_history) in the same shape."""
    return [
        {
            "run": e["run"],
            "fecha": e["sk"][:19],
            "canal": e.get("canal", ""),
            "tipo": e["evento"],
            "evento": e.get("evento_texto", e["evento"]),
            "detalle": _detail_text(e.get("detalle", {})),
            "origen": AWS_SOURCE,
        }
        for e in history
    ]


def quality(events: list[dict]) -> dict:
    """How complete each record is: date, channel and event type."""
    total = len(events)
    complete = sum(bool(e["fecha"] and e["canal"] and e["tipo"]) for e in events)
    return {
        "eventos": total,
        "completos": complete,
        "porcentaje": round(100 * complete / total) if total else 0,
        "casos": len({e["run"] for e in events}),
    }


def _by_run(events: list[dict]) -> dict[str, list[dict]]:
    grouped: dict[str, list[dict]] = {}
    for e in events:
        grouped.setdefault(e["run"], []).append(e)
    return grouped


def kpi_evidence(people: list[dict], events: list[dict]) -> list[dict]:
    """How each KPI will be measured and how many demo cases already carry its evidence."""
    runs = {p["run"] for p in people} or {e["run"] for e in events}
    grouped = _by_run(events)
    total = len(runs)

    def count(predicate) -> str:
        n = sum(1 for run in runs if predicate(grouped.get(run, [])))
        return f"{n} de {total} casos"

    return [
        {
            "Indicador": "Contacto efectivo",
            "Meta": "Referencia IPS: 85%",
            "Evidencia que se guarda": "Respuesta, aceptación, rechazo o inicio, con fecha y canal",
            "Registro": "Se registra",
            "Casos con evidencia (demo)": count(
                lambda ev: any(e["tipo"] in CONFIRMED_CONTACT for e in ev)
            ),
        },
        {
            "Indicador": "Acepta el acompañamiento",
            "Meta": "Por definir con el IPS",
            "Evidencia que se guarda": "Aceptación de la invitación, con fecha y canal",
            "Registro": "Se registra",
            "Casos con evidencia (demo)": count(
                lambda ev: any(e["tipo"] in ("invitacion_aceptada", "colador_answered") for e in ev)
            ),
        },
        {
            "Indicador": "Próximo paso válido dentro del plazo",
            "Meta": "Al menos 75%",
            "Evidencia que se guarda": (
                "Fecha del contacto y fecha del paso completado; falta fijar el plazo por "
                "trámite y que el organismo confirme que el paso es válido"
            ),
            "Registro": "Parcial",
            "Casos con evidencia (demo)": count(lambda ev: any(e["tipo"] in NEXT_STEP for e in ev)),
        },
        {
            "Indicador": "Continuidad entre canales",
            "Meta": "Al menos 90%",
            "Evidencia que se guarda": "Eventos del mismo caso en más de un canal, sin reiniciar",
            "Registro": "Se registra",
            "Casos con evidencia (demo)": count(
                lambda ev: len({e["canal"] for e in ev if e["canal"]}) > 1
            ),
        },
    ]


def _parse(value: str) -> datetime | None:
    try:
        return datetime.fromisoformat(value[:19])
    except (TypeError, ValueError):
        return None


def follow_up(
    people: list[dict], events: list[dict], now: str | None, *, stale_days: int = 7
) -> list[dict]:
    """Open cases whose last recorded movement is older than `stale_days`."""
    reference = _parse(now) if now else None
    grouped = _by_run(events)
    if reference is None:
        dates = [d for e in events if (d := _parse(e["fecha"]))]
        reference = max(dates) if dates else None
    if reference is None:
        return []
    rows = []
    for person in people:
        if person.get("status") in ("declined", "started"):
            continue
        history = grouped.get(person["run"], [])
        last = max((d for e in history if (d := _parse(e["fecha"]))), default=None)
        if last is None:
            continue
        days = (reference - last).days
        if days < stale_days:
            continue
        waiting = person.get("status") == "contacted"
        rows.append(
            {
                "run": person["run"],
                "name": person.get("name", ""),
                "last": last.strftime("%d-%m-%Y"),
                "days": days,
                "last_event": history[-1]["evento"],
                "reason": (
                    f"Respondió y lleva {days} días sin avanzar"
                    if waiting
                    else f"Sin respuesta ni movimiento hace {days} días"
                ),
            }
        )
    return sorted(rows, key=lambda r: -r["days"])


def timeline(run: str, events: list[dict], extra: list[dict] | None = None) -> list[dict]:
    rows = [e for e in events if e["run"] == run] + [e for e in extra or [] if e["run"] == run]
    return sorted(rows, key=lambda e: e["fecha"])


def audit_csv(events: list[dict]) -> str:
    out = io.StringIO()
    writer = csv.writer(out)
    writer.writerow(["run", "fecha", "canal", "tipo", "evento", "detalle", "origen"])
    for e in events:
        writer.writerow(
            [e["run"], e["fecha"], e["canal"], e["tipo"], e["evento"], e["detalle"], e["origen"]]
        )
    return out.getvalue()
