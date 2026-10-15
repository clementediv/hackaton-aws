"""Readable officer workspace over the existing local funnel, without AWS calls."""

from pathlib import Path

from .colador import Funnel
from .contacto import generate_contacts

STATUS = {
    "active": "Por contactar",
    "contacted": "Espera orientación",
    "started": "Trámite iniciado",
    "declined": "Declinó",
}


DEMO_DB = Path(__file__).resolve().parents[1] / "funnel-demo-ejecutivos.db"


def demo_snapshot(profiles, path=None):
    path = Path(path or DEMO_DB)
    engine = Funnel(path)
    if not engine.snapshot()["clock"]:
        engine.initialize(
            profiles, generate_contacts(profiles, territory="metropolitana"), simulate=True
        )
        engine.advance(19, simulate=True)
    return engine.snapshot()


def next_action(person):
    if person["status"] == "contacted":
        return "Orientar y acordar el próximo paso"
    if person["status"] == "started":
        return "Acompañar el avance de su trámite"
    if person["status"] == "declined":
        return "Respetar su decisión; no contactar"
    return {
        1: "Esperar respuesta al correo",
        2: "Gestionar contacto telefónico",
        3: "Coordinar contacto con la persona",
        4: "Priorizar atención en terreno",
    }[person["stage"]]


def case_rows(state, *, search="", status="Todos", commune="Todas las comunas"):
    needle = search.strip().casefold()
    rows = []
    for p in state["people"]:
        if status != "Todos" and STATUS[p["status"]] != status:
            continue
        if commune != "Todas las comunas" and p["contact"]["commune"] != commune:
            continue
        if needle and needle not in f"{p['name']} {p['run']}".casefold():
            continue
        rows.append(
            {
                "run": p["run"],
                "name": p["name"],
                "commune": p["contact"]["commune"],
                "status": STATUS[p["status"]],
                "next_action": next_action(p),
            }
        )
    order = {"Espera orientación": 0, "Por contactar": 1, "Trámite iniciado": 2, "Declinó": 3}
    return sorted(rows, key=lambda row: (order[row["status"]], row["name"], row["run"]))
