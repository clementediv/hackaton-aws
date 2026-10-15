"""Unified beneficiary record and single contact source shared by every view.

`contact_for` returns the contact the funnel actually used when the person is in
the campaign; otherwise the same synthetic layer the funnel would generate.
Mi Gobierno, the funnel and the record therefore never show different channels.
"""

import json
import sqlite3
from dataclasses import asdict, dataclass, field, fields
from pathlib import Path

from . import casos, config, government
from . import reglas as rules
from .colador import ACTIVE, STAGES
from .contacto import Contact, generate_contacts
from .rutas import estado_pasos, generar_ruta, proximo_paso

DEMO_TERRITORY = "metropolitana"
SOURCE_FUNNEL = "Usado por el colador de contacto"
SOURCE_LAYER = "Capa de contacto sintética"
_CONTACT_FIELDS = {f.name for f in fields(Contact)}


@dataclass
class Ficha:
    run: str
    identity: dict
    contact: Contact
    contact_source: str
    case: dict
    pgu: dict
    retirement: dict
    route: list[dict]
    next_step: dict | None
    funnel: dict | None
    alert: dict
    documents: list[dict] | None = None
    declaration: dict | None = None
    events: list[dict] = field(default_factory=list)


def _funnel_rows(run: str, db_path: Path) -> tuple[sqlite3.Row | None, list[dict]]:
    if not db_path.exists():
        return None, []
    con = sqlite3.connect(db_path)
    con.row_factory = sqlite3.Row
    try:
        exists = con.execute(
            "SELECT 1 FROM sqlite_master WHERE type='table' AND name='funnel_people'"
        ).fetchone()
        if not exists:
            return None, []
        person = con.execute("SELECT * FROM funnel_people WHERE run=?", (run,)).fetchone()
        events = [
            {**dict(row), "detail": json.loads(row["detail"])}
            for row in con.execute(
                "SELECT at, stage, kind, detail FROM funnel_events WHERE run=? ORDER BY at, id",
                (run,),
            )
        ]
        return person, events
    finally:
        con.close()


def contact_for(run: str, profile: dict, db_path: Path | None = None) -> tuple[Contact, str]:
    """The single contact source: funnel snapshot first, synthetic layer otherwise."""
    person, _ = _funnel_rows(run, Path(db_path or config.DB_PATH))
    if person is not None:
        stored = json.loads(person["contact"])
        return Contact(**{k: v for k, v in stored.items() if k in _CONTACT_FIELDS}), SOURCE_FUNNEL
    return generate_contacts({run: profile}, territory=DEMO_TERRITORY)[run], SOURCE_LAYER


def alert_level(funnel: dict | None) -> dict:
    """Benefit alert from the funnel stage; only unanswered people at stage 4 are maximum."""
    if not funnel or funnel["status"] != ACTIVE:
        return {"level": 0, "label": "Sin alerta de contacto"}
    if funnel["stage"] == max(STAGES):
        return {"level": funnel["stage"], "label": "NIVEL MÁXIMO · no respondió a ningún canal"}
    return {
        "level": funnel["stage"],
        "label": f"Nivel {funnel['stage']} · en contacto por {funnel['stage_label']}",
    }


def build(diagnosis: rules.Diagnostico, profile: dict, db_path: Path | None = None) -> Ficha:
    run = diagnosis.run
    path = Path(db_path or config.DB_PATH)
    civil = profile["registro_civil"]
    case = casos.obtener_caso(run)
    authorized = bool(case["autorizacion"])

    contact, source = contact_for(run, profile, path)
    person, funnel_events = _funnel_rows(run, path)
    funnel = None
    if person is not None:
        funnel = {
            "stage": person["stage"],
            "stage_label": STAGES[person["stage"]],
            "status": person["status"],
            "attempts": person["attempts"],
            "reason": person["reason"],
            "events": funnel_events,
        }

    route = generar_ruta(diagnosis)
    states = estado_pasos(route, case["completados"])
    upcoming = proximo_paso(route, states)

    return Ficha(
        run=run,
        identity={
            "name": diagnosis.nombre,
            "formatted_run": civil["run_formateado"],
            "birth_date": civil["fecha_nacimiento"],
            "age": diagnosis.hitos.edad,
            "sex": diagnosis.hitos.sexo,
            "alive": diagnosis.vivo,
            "segment": diagnosis.segmento,
        },
        contact=contact,
        contact_source=source,
        case={
            "invitation": case["invitacion"],
            "invitation_channel": case["canal_invitacion"],
            "authorized": authorized,
            "authorized_at": case["fecha_autorizacion"],
        },
        pgu={
            "result": diagnosis.pgu.resultado,
            "reason": diagnosis.pgu.motivo,
            "estimated_amount": diagnosis.pgu.monto_estimado,
            "requirements": [asdict(req) for req in diagnosis.pgu.requisitos],
        },
        retirement={
            "result": diagnosis.jubilacion.resultado,
            "reason": diagnosis.jubilacion.motivo,
        },
        route=[{**step.to_dict(), "state": states[step.id]} for step in route],
        next_step=upcoming.to_dict() if upcoming else None,
        funnel=funnel,
        alert=alert_level(funnel),
        # Personal uploads and declarations are only read with current consent.
        documents=government.list_documents(run) if authorized else None,
        declaration=government.load_profile(run) if authorized else None,
        events=case["eventos"],
    )
