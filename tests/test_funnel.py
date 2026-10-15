import copy
import sqlite3
from datetime import date

import pytest

from src.app.ruta import casos, config
from src.app.ruta.colador import Funnel
from src.app.ruta.contacto import Contact, generate_contacts, load_contacts, save_contacts
from src.app.ruta.datos import cargar_perfiles

RUN = "100000001-5"
REFERENCE = date(2026, 10, 8)


@pytest.fixture
def profile():
    raw = copy.deepcopy(cargar_perfiles()[RUN])
    raw["registro_civil"]["fecha_nacimiento"] = "1956-10-08"
    raw["rsh"].update(info_pfp_disponible=True, pfp_percentil=50)
    raw["residencia"].update(
        resultado="cumple", anios_residencia_desde_20=30, anios_residencia_ultimos_5=5
    )
    raw["prevision"]["pafe_estimada"] = 0
    raw["pensiones_beneficios"] = []
    return raw


@pytest.fixture
def contact():
    return Contact(
        RUN,
        "persona@example.com",
        "SIM-TEL-001",
        "Empresa ficticia",
        "Metropolitana de Santiago",
        "Santiago",
        "Santiago",
    )


@pytest.fixture
def engine(tmp_path, profile, contact, monkeypatch):
    path = tmp_path / "cases.db"
    monkeypatch.setattr(config, "DB_PATH", path)
    funnel = Funnel(path)
    funnel.initialize({RUN: profile}, {RUN: contact})
    return funnel


def test_initialization_is_idempotent_and_does_not_send_twice(engine, profile, contact):
    first = engine.snapshot()
    assert first["funnel"][0]["attempts"] == 1
    assert first["people"][0]["next_at"] == "2026-10-15T09:00:00"
    assert engine.initialize({RUN: profile}, {RUN: contact}) == first
    assert casos.obtener_caso(RUN)["autorizacion"] == 0


def test_clock_boundaries_and_three_calls_in_five_days(engine):
    engine.respond(RUN, "opened")
    assert engine.advance(6)["people"][0]["stage"] == 1
    state = engine.advance(1)
    assert state["people"][0]["stage"] == 2
    assert state["funnel"][1]["attempts"] == 1
    assert engine.advance(2)["funnel"][1]["attempts"] == 2
    state = engine.advance(3)
    assert state["funnel"][1]["attempts"] == 3
    assert state["people"][0]["stage"] == 3
    assert engine.advance(6)["people"][0]["stage"] == 3
    final = engine.advance(1)
    assert final["people"][0]["stage"] == 4
    assert final["people"][0]["next_at"] is None
    assert final["totals"]["in_person"] == 1
    assert engine.advance(50)["events"] == final["events"]
    work_message = next(
        event["detail"]["message"]
        for event in final["events"]
        if event["stage"] == 3 and event["kind"] == "attempt"
    )
    assert "PGU" not in work_message and "$" not in work_message and RUN not in work_message


@pytest.mark.parametrize("response", ["started", "declined"])
def test_terminal_response_cancels_all_future_contact(engine, response):
    state = engine.respond(RUN, response)
    assert state["people"][0]["status"] == response
    assert state["people"][0]["alert_level"] == 0
    assert engine.respond(RUN, response) == state
    assert engine.advance(100)["events"] == state["events"]
    if response == "declined":
        assert casos.obtener_caso(RUN)["invitacion"] == "rechazado"
    with pytest.raises(ValueError):
        engine.respond(RUN, "opened")


def test_missing_channels_skip_immediately_and_log_reason(tmp_path, profile):
    contact = Contact(RUN, "", "", "", "RM", "Santiago", "Santiago")
    engine = Funnel(tmp_path / "missing.db")
    state = engine.initialize({RUN: profile}, {RUN: contact})
    assert state["people"][0]["stage"] == 4
    assert len([event for event in state["events"] if event["kind"] == "skipped"]) == 3
    assert not [event for event in state["events"] if event["kind"] == "attempt"]


def test_existing_acceptance_and_authorization_are_not_started_progress(engine):
    casos.responder_invitacion(RUN, True, "Web ChileAtiende")
    casos.autorizar(RUN, True, "Web ChileAtiende")
    state = engine.advance(7)
    assert state["people"][0]["stage"] == 1
    assert state["people"][0]["status"] == "contacted"
    assert state["totals"]["started"] == 0


@pytest.mark.parametrize("step", ["G1", "J2"])
def test_formal_request_step_in_shared_case_stops_funnel(engine, step):
    casos.completar_paso(RUN, step, "Sucursal ChileAtiende")
    state = engine.advance(20)
    assert state["people"][0]["status"] == "started"
    assert state["funnel"][1]["attempts"] == 0


def test_rejection_in_shared_case_is_respected(engine):
    casos.responder_invitacion(RUN, False, "Web ChileAtiende")
    state = engine.advance(20)
    assert state["people"][0]["status"] == "declined"
    assert state["totals"]["in_person"] == 0


def test_existing_demo_reset_clears_funnel_without_leaving_orphan_contacts(engine):
    casos.reiniciar()
    state = engine.snapshot()
    assert state["clock"] is None
    assert not state["people"] and not state["events"]


@pytest.mark.parametrize("days", [-1, 1.5, True])
def test_invalid_clock_advance_does_not_change_state(engine, days):
    before = engine.snapshot()
    with pytest.raises(ValueError):
        engine.advance(days)
    assert engine.snapshot() == before


def test_seeded_simulation_is_persistent_and_independent_of_tick_size(tmp_path):
    profiles = cargar_perfiles()
    contacts = generate_contacts(profiles, seed=72)
    first, second = Funnel(tmp_path / "one.db"), Funnel(tmp_path / "two.db")
    for engine in (first, second):
        engine.initialize(profiles, contacts, seed=72, simulate=True)
    state = first.advance(19, simulate=True)
    second.advance(7, simulate=True)
    second.advance(5, simulate=True)
    repeated = second.advance(7, simulate=True)
    assert state == repeated
    assert Funnel(tmp_path / "one.db").snapshot() == state
    totals = state["totals"]
    assert totals["detected"] == sum(
        totals[k] for k in ("active", "contacted", "started", "declined")
    )
    reached = [row["reached"] for row in state["funnel"]]
    assert reached == sorted(reached, reverse=True)
    assert totals["started"] > 0 and totals["in_person"] > 0
    assert all(event["detail"]["simulated"] for event in state["events"])
    with sqlite3.connect(first.db_path) as con:
        assert con.execute("SELECT SUM(autorizacion) FROM casos").fetchone()[0] == 0


def test_missing_contact_rolls_back_whole_initialization(tmp_path, profile):
    engine = Funnel(tmp_path / "rollback.db")
    with pytest.raises(ValueError, match="Falta contacto"):
        engine.initialize({RUN: profile}, {})
    assert engine.snapshot()["clock"] is None
    assert not engine.snapshot()["people"]


def test_new_signal_is_added_without_restarting_or_duplicating_contacts(
    engine, profile, contact, monkeypatch
):
    from src.app.ruta import reglas

    diagnosis = reglas.diagnosticar(profile)
    diagnosis.razon_invitacion = "Un nuevo hito para la misma persona"
    monkeypatch.setattr(reglas, "diagnosticar", lambda *args: diagnosis)
    first = engine.initialize({RUN: profile}, {RUN: contact})
    assert first["funnel"][0]["attempts"] == 1
    assert len([event for event in first["events"] if event["kind"] == "signal"]) == 1
    assert engine.initialize({RUN: profile}, {RUN: contact}) == first


def test_campaign_seed_cannot_be_changed_silently(engine, profile, contact):
    before = engine.snapshot()
    with pytest.raises(ValueError, match="otra semilla"):
        engine.initialize({RUN: profile}, {RUN: contact}, seed=2)
    assert engine.snapshot() == before


def test_contact_csv_is_reproducible_non_contactable_and_not_overwritten(tmp_path):
    profiles = cargar_perfiles()
    contacts = generate_contacts(profiles)
    assert contacts == generate_contacts(dict(reversed(list(profiles.items()))))
    assert all(contact.synthetic for contact in contacts.values())
    assert all(not c.email or c.email.endswith("@example.com") for c in contacts.values())
    assert all(not c.phone or c.phone.startswith("+56 9 0000 ") for c in contacts.values())
    assert all(
        not c.employer
        for run, c in contacts.items()
        if not (profiles[run].get("situacion_laboral") or {}).get("trabaja_actualmente")
    )
    path = tmp_path / "contacto.csv"
    save_contacts(path, contacts)
    assert load_contacts(path) == contacts
    with pytest.raises(FileExistsError):
        save_contacts(path, contacts)
