"""Referrals to a ChileAtiende officer, with a case summary computed by code.

A simulated CESFAM front desk only learns whether to refer the person; the
summary travels to the officer, never to the CESFAM. Referrals live in the same
SQLite database as the cases. Design: 20-arquitectura/cesfam-derivacion.md.
"""

import json
import sqlite3
from contextlib import contextmanager
from datetime import datetime

from . import casos, config
from .colador import ACTIVE, STAGES

SCHEMA = """
CREATE TABLE IF NOT EXISTS derivaciones (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    run TEXT NOT NULL,
    origin TEXT NOT NULL,
    reason TEXT NOT NULL,
    summary TEXT NOT NULL,
    created_at TEXT NOT NULL,
    status TEXT NOT NULL DEFAULT 'pendiente',
    attended_by TEXT,
    attended_at TEXT
);
"""
PENDING, ATTENDED = "pendiente", "atendida"
AWS_FIELD_STATE = "terreno"  # email and SMS unanswered: the field team has it
REFERRAL_EVENT, ATTENDED_EVENT = "derivacion", "derivacion_atendida"


def _now() -> str:
    return datetime.now().isoformat(timespec="seconds")


@contextmanager
def _conn():
    con = sqlite3.connect(config.DB_PATH)
    con.row_factory = sqlite3.Row
    try:
        con.executescript(SCHEMA)
        yield con
        con.commit()
    finally:
        con.close()


def max_alert(alert: dict | None, aws_contacts: list[dict]) -> str | None:
    """Internal reason for a maximum alert, or None: the funnel reached its last
    stage without an answer, or an AWS contact went to the field team."""
    reasons = []
    if alert and alert.get("level") == max(STAGES):
        reasons.append("No respondió a ningún canal del colador (email, llamada ni trabajo).")
    field = sorted(
        {
            c.get("beneficio") or c["beneficio_id"]
            for c in aws_contacts
            if c.get("estado") == AWS_FIELD_STATE
        }
    )
    if field:
        reasons.append(
            "Sin respuesta al email ni al SMS de la detección automática: " + ", ".join(field) + "."
        )
    return " ".join(reasons) or None


def funnel_max_runs() -> list[str]:
    """People the app's funnel left at its last stage without an answer."""
    con = sqlite3.connect(config.DB_PATH)
    try:
        if not con.execute(
            "SELECT 1 FROM sqlite_master WHERE type='table' AND name='funnel_people'"
        ).fetchone():
            return []
        rows = con.execute(
            "SELECT run FROM funnel_people WHERE stage=? AND status=? ORDER BY run",
            (max(STAGES), ACTIVE),
        )
        return [r[0] for r in rows]
    finally:
        con.close()


def summarize(ficha, aws_contacts: list[dict], reason: str = "") -> list[dict]:
    """The officer's case summary as label/value rows; `ficha` is None for people
    who only exist on AWS. Documents are listed only with current consent."""
    rows = []

    def add(label: str, value) -> None:
        if value:
            rows.append({"label": label, "value": str(value)})

    if ficha is not None:
        who = ficha.identity
        add("Persona", f"{who['name']} · {who['age']} años · RUN {who['formatted_run']}")
    elif aws_contacts:
        add("Persona", f"{aws_contacts[0].get('nombre', '')} · RUN {aws_contacts[0]['run']}")
    add("Alerta", reason)
    if ficha is not None:
        pgu = ficha.pgu
        add("PGU", f"{pgu['result'].replace('_', ' ')} — {pgu['reason']}")
        case = ficha.case
        channel = f" por {case['invitation_channel']}" if case["invitation_channel"] else ""
        add("Invitación", f"{case['invitation'].replace('_', ' ')}{channel}")
        if ficha.funnel:
            f = ficha.funnel
            add("Colador", f"etapa {f['stage_label']}, {f['attempts']} intentos")
        add("Autorización de datos", "Vigente" if case["authorized"] else "Sin autorización")
        if ficha.documents is None:
            add("Documentos", "Sin autorización para revisarlos")
        else:
            kinds = ", ".join(d["kind"] for d in ficha.documents)
            add(
                "Documentos",
                f"{len(ficha.documents)} adjuntos: {kinds}" if kinds else "Sin documentos adjuntos",
            )
        if ficha.next_step:
            add("Próximo paso", f"{ficha.next_step['titulo']} ({ficha.next_step['donde']})")
    add(
        "Detección AWS",
        "; ".join(
            f"{c.get('beneficio') or c['beneficio_id']}: {c.get('estado_texto') or c.get('estado')}"
            for c in aws_contacts
        ),
    )
    return rows


def _row(row: sqlite3.Row) -> dict:
    item = dict(row)
    item["summary"] = json.loads(item["summary"])
    return item


def refer(run: str, origin: str, reason: str, summary: list[dict]) -> int | None:
    """Create a referral; None when that RUN already has one pending."""
    with _conn() as con:
        if con.execute(
            "SELECT 1 FROM derivaciones WHERE run=? AND status=?", (run, PENDING)
        ).fetchone():
            return None
        ref_id = con.execute(
            "INSERT INTO derivaciones(run, origin, reason, summary, created_at) VALUES (?,?,?,?,?)",
            (run, origin, reason, json.dumps(summary, ensure_ascii=False), _now()),
        ).lastrowid
    casos.registrar_evento(run, origin, REFERRAL_EVENT, {"motivo": reason})
    return ref_id


def pending() -> list[dict]:
    with _conn() as con:
        rows = con.execute(
            "SELECT * FROM derivaciones WHERE status=? ORDER BY created_at, id", (PENDING,)
        )
        return [_row(r) for r in rows]


def for_run(run: str) -> list[dict]:
    """A person's referrals, newest first."""
    with _conn() as con:
        rows = con.execute("SELECT * FROM derivaciones WHERE run=? ORDER BY id DESC", (run,))
        return [_row(r) for r in rows]


def attend(ref_id: int, officer: str, channel: str) -> str | None:
    """Mark a pending referral as attended; returns its RUN (None if it was not pending)."""
    with _conn() as con:
        row = con.execute(
            "SELECT run FROM derivaciones WHERE id=? AND status=?", (ref_id, PENDING)
        ).fetchone()
        if row is None:
            return None
        con.execute(
            "UPDATE derivaciones SET status=?, attended_by=?, attended_at=? WHERE id=?",
            (ATTENDED, officer, _now(), ref_id),
        )
    casos.registrar_evento(row["run"], channel, ATTENDED_EVENT, {"ejecutivo": officer})
    return row["run"]
