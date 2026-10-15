"""Build `Personas` items from dataset A plus a few demo people.

Dataset contacts come from the shared synthetic layer (data/synthetic/
contacto.csv, @example.com and 0000 phones): they are never really sent.
Only demo people carry the verified inbox, so the star demo emails arrive.
"""

import csv
from datetime import date, timedelta
from pathlib import Path

from .reglas import add_years

ROOT = Path(__file__).resolve().parents[2]
PROFILES = ROOT / "data/raw/dataset_A_participantes/perfiles.json"
CONTACTS = ROOT / "data/synthetic/contacto.csv"


def load_contacts(path: Path = CONTACTS) -> dict[str, dict]:
    with path.open(encoding="utf-8", newline="") as stream:
        return {row["run"]: row for row in csv.DictReader(stream)}


def from_dataset(profile: dict, contact: dict | None = None) -> dict:
    civil = profile["registro_civil"]
    item = {
        "run": profile["run"],
        "nombre": f"{civil['nombres']} {civil['apellido_paterno']}",
        "fecha_nacimiento": civil["fecha_nacimiento"],
        "sexo": civil["sexo"],
        "estado_civil": civil["estado_civil"],
        # The dataset only says whether there are children.
        "num_hijos": 1 if civil["tiene_hijos"] else 0,
        "fallecido": civil["estado"] == "fallecido",
        "accidente_laboral": False,
        "beneficios_vigentes": sorted(
            {
                "pgu"
                for b in profile.get("pensiones_beneficios") or []
                if b.get("tipo_beneficio") == "PGU" and b["estado"] == "vigente"
            }
        ),
        "sintetico": True,
        "origen": "dataset A",
    }
    if rsh := profile.get("rsh"):
        item["ingreso_hogar"] = sum(
            rsh[k]
            for k in ("ingreso_trabajo_hogar", "ingreso_pensiones_hogar", "ingreso_capital_hogar")
        )
        if rsh.get("cse_tramo") is not None:
            item["tramo_rsh"] = rsh["cse_tramo"]
        if rsh.get("info_pfp_disponible") and rsh.get("pfp_percentil") is not None:
            item["percentil_pfp"] = rsh["pfp_percentil"]
    # Same base pension as src/app/ruta/reglas.py: current pensions, else estimated PAFE.
    pensions = [
        b["monto"]
        for b in profile.get("pensiones_beneficios") or []
        if b["tipo_registro"] == "pension" and b["estado"] == "vigente"
    ]
    fund = profile.get("prevision") or {}
    item["pension_base"] = sum(pensions) if pensions else int(fund.get("pafe_estimada") or 0)
    if residence := profile.get("residencia"):
        item["residencia_cumple"] = residence["resultado"] == "cumple"
    if job := profile.get("situacion_laboral"):
        item["trabaja"] = bool(job["trabaja_actualmente"])
    if contact:
        item |= {
            "email": contact["email"],
            "telefono": contact["phone"],
            "comuna": contact["commune"],
        }
    return {k: v for k, v in item.items() if v not in (None, "")}


def run_with_check_digit(number: int) -> str:
    digits = str(number)
    total = sum(int(d) * (2 + i % 6) for i, d in enumerate(reversed(digits)))
    rest = 11 - total % 11
    return f"{digits}-{'0' if rest == 11 else 'K' if rest == 10 else rest}"


def _born(today: date, age: int) -> str:
    """Born so that the person is `age` now and turns age+1 in ~6 months:
    outside every anticipation window, so nothing fires until the demo edits it."""
    return add_years(today + timedelta(days=180), -(age + 1)).isoformat()


def demo_people(email: str, today: date) -> list[dict]:
    """One person per life event of the demo. Each one already receives the
    electricity subsidy when its RSH bracket qualifies, so the insert is quiet."""
    base = {
        "email": email,
        "accidente_laboral": False,
        "fallecido": False,
        "residencia_cumple": True,
        "sintetico": True,
        "origen": "demo",
        "comuna": "Santiago",
        "pension_base": 0,
    }
    rows = [
        # (number, name, age, sex, extra) — event in the comment
        (90000001, "Camila Demo", 17, "F", {"trabaja": True, "tramo_rsh": 40}),  # cumple 18
        (90000002, "Jorge Demo", 64, "M", {"trabaja": False, "tramo_rsh": 40, "percentil_pfp": 50}),
        (90000003, "Paula Demo", 30, "F", {"trabaja": True, "tramo_rsh": 50}),  # tiene un hijo
        (90000004, "Marcelo Demo", 35, "M", {"trabaja": True, "tramo_rsh": 60}),  # se casa
        (90000005, "Pedro Demo", 40, "M", {"trabaja": True, "tramo_rsh": 90}),  # accidente
        (90000006, "Ana Demo", 45, "F", {"trabaja": True, "tramo_rsh": 90}),  # baja su tramo RSH
    ]
    people = []
    for number, name, age, sex, extra in rows:
        run = run_with_check_digit(number)
        person = (
            base
            | extra
            | {
                "run": run,
                "nombre": name,
                "fecha_nacimiento": _born(today, age),
                "sexo": sex,
                "estado_civil": "soltero",
                "num_hijos": 0,
                "telefono": f"+56 9 0000 {str(number)[-4:]}",
            }
        )
        person["beneficios_vigentes"] = ["subsidio_electrico"] if person["tramo_rsh"] <= 80 else []
        people.append(person)
    return people
