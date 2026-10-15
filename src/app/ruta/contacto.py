"""Reproducible, non-contactable demo contacts; never changes the raw dataset."""

import csv
import hashlib
import random
import unicodedata
from dataclasses import asdict, dataclass
from pathlib import Path

# Small illustrative selection, not a population distribution or geocoder.
# Reference: SUBDERE, Códigos Únicos Territoriales.
TERRITORIES = (
    ("Metropolitana de Santiago", "Santiago", "Santiago"),
    ("Valparaíso", "Valparaíso", "Valparaíso"),
    ("Biobío", "Concepción", "Concepción"),
    ("La Araucanía", "Cautín", "Temuco"),
    ("Los Lagos", "Llanquihue", "Puerto Montt"),
    ("Tarapacá", "Iquique", "Iquique"),
)

# Deliberately uneven demo distribution; not census/RSH population estimates.
METROPOLITAN_COMMUNES = (
    ("Santiago", "Maipú", -33.510, -70.758, 23),
    ("Cordillera", "Puente Alto", -33.608, -70.575, 21),
    ("Santiago", "La Florida", -33.536, -70.582, 15),
    ("Santiago", "Santiago", -33.448, -70.660, 13),
    ("Maipo", "San Bernardo", -33.593, -70.704, 12),
    ("Santiago", "Pudahuel", -33.437, -70.767, 8),
    ("Santiago", "Quilicura", -33.363, -70.733, 6),
    ("Santiago", "Recoleta", -33.402, -70.642, 4),
)


def stable_random(seed: int, *parts: object) -> random.Random:
    key = "|".join(map(str, (seed, *parts)))
    return random.Random(int.from_bytes(hashlib.sha256(key.encode()).digest()[:8], "big"))


@dataclass(frozen=True)
class Contact:
    run: str
    email: str
    phone: str
    employer: str
    region: str
    province: str
    commune: str
    synthetic: bool = True
    address: str = ""
    latitude: float | None = None
    longitude: float | None = None
    location_source: str = ""


FICTITIOUS_PHONE_PREFIX = "+56 9 0000 "


def _ascii_token(text: str) -> str:
    plain = unicodedata.normalize("NFKD", text).encode("ascii", "ignore").decode()
    return "".join(ch for ch in plain.split()[0].lower() if ch.isalnum()) if plain.split() else ""


def demo_email(profile: dict, run: str) -> str:
    """Readable fictitious address on the reserved example.com domain."""
    civil = profile.get("registro_civil") or {}
    name = _ascii_token(civil.get("nombres", ""))
    surname = _ascii_token(civil.get("apellido_paterno", ""))
    local = ".".join(part for part in (name, surname) if part) or f"persona.{run}"
    return f"{local}@example.com"


def demo_phone(run: str) -> str:
    """Readable fictitious mobile; the 0000 block marks it as non-contactable demo data."""
    digits = "".join(ch for ch in run.split("-")[0] if ch.isdigit())
    return f"{FICTITIOUS_PHONE_PREFIX}{digits[-4:].rjust(4, '0')}"


def generate_contacts(
    profiles: dict[str, dict], seed: int = 20261008, *, territory="national"
) -> dict[str, Contact]:
    if territory not in {"national", "metropolitana"}:
        raise ValueError("Territorio de simulación no reconocido.")
    contacts = {}
    for run, profile in sorted(profiles.items()):
        rng = stable_random(seed, run, "contact")
        location = rng.choice(TERRITORIES)
        if territory == "metropolitana":
            province, commune, *_ = stable_random(seed, run, "rm-territory").choices(
                METROPOLITAN_COMMUNES, weights=[row[4] for row in METROPOLITAN_COMMUNES]
            )[0]
            location = "Metropolitana de Santiago", province, commune
        works = bool((profile.get("situacion_laboral") or {}).get("trabaja_actualmente"))
        location_details = {}
        if territory == "metropolitana":
            from .geografia import simulated_location

            location_details = simulated_location(run, location[2], seed)
        contacts[run] = Contact(
            run=run,
            email=demo_email(profile, run) if rng.random() >= 0.15 else "",
            phone=demo_phone(run) if rng.random() >= 0.1 else "",
            employer=f"Empleador ficticio {rng.randrange(1, 20)}" if works else "",
            region=location[0],
            province=location[1],
            commune=location[2],
            **location_details,
        )
    return contacts


def save_contacts(path: Path, contacts: dict[str, Contact]) -> None:
    """Exclusive creation: never overwrite a contact file supplied by a person."""
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("x", encoding="utf-8", newline="") as stream:
        writer = csv.DictWriter(stream, fieldnames=list(Contact.__dataclass_fields__))
        writer.writeheader()
        writer.writerows(asdict(contact) for _, contact in sorted(contacts.items()))


def load_contacts(path: Path) -> dict[str, Contact]:
    contacts = {}
    with path.open(encoding="utf-8", newline="") as stream:
        for row in csv.DictReader(stream):
            row["synthetic"] = str(row["synthetic"]).lower() == "true"
            for key in ("latitude", "longitude"):
                if key in row:
                    row[key] = float(row[key]) if row[key] else None
            contact = Contact(**row)
            if contact.run in contacts:
                raise ValueError("RUN duplicado en contactos.")
            contacts[contact.run] = contact
    return contacts
