"""Aggregated institutional reporting from the existing campaign and usage ledger."""

from collections import Counter
from datetime import UTC, datetime

from . import engagement

STATUSES = {
    "active": "Por contactar",
    "contacted": "Espera orientación",
    "started": "Trámite iniciado",
    "declined": "Declinó",
}
STAGES = ("Con alerta fechada", "Ingresaron", "Autorizaron", "Avance declarado")
SOURCE = "Campaña local del portal de ejecutivos y registro de eventos de Mi Gobierno (SQLite)."
LIMITATION = (
    "El avance es declarado por la persona y no acredita una solicitud presentada, "
    "un beneficio otorgado ni una resolución del organismo. El cumplimiento del próximo "
    "paso válido dentro del plazo (meta ≥75%) aún no está medido."
)


def commune_of(person):
    return person.get("contact", {}).get("commune") or "Sin comuna informada"


def build_report(state, events, *, audience, institution, communes=None, demo=False, now=None):
    """No personal identifiers leave this function. Counts always use unique people."""
    generated = now or datetime.now(UTC)
    cutoff = state.get("clock", {}).get("now") if demo else generated.isoformat()
    people = list({p["run"]: p for p in state["people"]}.values())
    if communes is not None:
        people = [p for p in people if commune_of(p) in communes]
    usage = engagement.report(people, events, cutoff)
    statuses = Counter(p.get("status") for p in people)
    usage_by_run = {row["run"]: row for row in usage["people"]}
    territory = []
    for commune in sorted({commune_of(p) for p in people}):
        group = [p for p in people if commune_of(p) == commune]
        counts = Counter(p.get("status") for p in group)
        territory.append(
            {
                "commune": commune,
                "people": len(group),
                "pending": counts["active"],
                "guidance": counts["contacted"],
                "started": counts["started"],
                "progress": sum(
                    bool(usage_by_run.get(p["run"], {}).get("progress")) for p in group
                ),
                "declined": counts["declined"],
            }
        )
    findings = []
    if statuses["active"]:
        priority = max(territory, key=lambda row: (row["pending"], row["guidance"]))
        findings.append(
            f"Priorizar contacto. Personas sin respuesta confirmada: {statuses['active']}. "
            f"Mayor concentración: {priority['commune']} (pendientes: {priority['pending']})."
        )
    if statuses["contacted"]:
        findings.append(
            "Organizar acompañamiento. Personas que respondieron sin inicio registrado: "
            f"{statuses['contacted']}. La respuesta detiene el escalamiento de canales."
        )
    if statuses["started"]:
        findings.append(
            f"Dar continuidad. Personas con inicio en el colador: {statuses['started']}. "
            "Ese estado no acredita una solicitud presentada."
        )
    if statuses["declined"]:
        findings.append(
            f"Respetar decisiones. Personas que declinaron: {statuses['declined']}; "
            "no reactivar contactos."
        )
    if not people:
        findings.append("No hay casos en el territorio seleccionado; no se calculan porcentajes.")
    return {
        "audience": audience,
        "institution": institution.strip() or audience,
        "demo": demo,
        "generated": generated.isoformat(),
        "cutoff": usage["reference"].replace(tzinfo=UTC).isoformat(),
        "scope": sorted(communes) if communes is not None else ["Todas las comunas de la campaña"],
        "total": len(people),
        "pending": statuses["active"],
        "guidance": statuses["contacted"],
        "started": statuses["started"],
        "declined": statuses["declined"],
        "other": sum(v for k, v in statuses.items() if k not in STATUSES),
        "stages": dict(zip(STAGES, usage["counts"], strict=True)),
        "progress": usage["counts"][3],
        "returning": usage["returning"],
        "territory": territory,
        "findings": findings,
        "source": SOURCE,
        "limitation": LIMITATION,
    }
