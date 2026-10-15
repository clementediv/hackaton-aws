import importlib
from pathlib import Path

import pytest

from src.app.ruta import casos, config, ficha
from src.app.ruta import reglas as rules
from src.app.ruta.colador import Funnel
from src.app.ruta.contacto import FICTITIOUS_PHONE_PREFIX, generate_contacts
from src.app.ruta.datos import cargar_perfiles


@pytest.fixture
def db(tmp_path, monkeypatch):
    path = tmp_path / "ficha.db"
    monkeypatch.setattr(config, "DB_PATH", path)
    return path


def test_contacts_are_readable_fictitious_and_keep_missing_channels():
    contacts = generate_contacts(cargar_perfiles(), territory=ficha.DEMO_TERRITORY)
    emails = [c.email for c in contacts.values()]
    phones = [c.phone for c in contacts.values()]
    assert all(not e or (e.endswith("@example.com") and e.isascii()) for e in emails)
    assert all(not p or p.startswith(FICTITIOUS_PHONE_PREFIX) for p in phones)
    # The funnel needs people without channels to exercise skipped stages.
    assert 0 < emails.count("") < len(emails)
    assert 0 < phones.count("") < len(phones)


def test_every_view_reads_the_same_contact(db):
    profiles = cargar_perfiles()
    layer = generate_contacts(profiles, territory=ficha.DEMO_TERRITORY)
    run = next(r for r, c in layer.items() if not c.email)
    contact, source = ficha.contact_for(run, profiles[run], db)
    assert (contact, source) == (layer[run], ficha.SOURCE_LAYER)
    assert contact.email == ""  # Mi Gobierno must show "Sin información", not an invented address


def test_funnel_contact_wins_once_the_person_is_in_the_campaign(db):
    profiles = cargar_perfiles()
    contacts = generate_contacts(profiles, territory=ficha.DEMO_TERRITORY)
    Funnel(db).initialize(profiles, contacts)
    run = next(r for r, p in profiles.items() if rules.diagnosticar(p).invitar)
    contact, source = ficha.contact_for(run, profiles[run], db)
    assert source == ficha.SOURCE_FUNNEL
    assert contact == contacts[run]


def test_record_gates_personal_data_and_reports_alert(db):
    profiles = cargar_perfiles()
    Funnel(db).initialize(profiles, generate_contacts(profiles, territory=ficha.DEMO_TERRITORY))
    run = next(r for r, p in profiles.items() if rules.diagnosticar(p).invitar)
    record = ficha.build(rules.diagnosticar(profiles[run]), profiles[run], db)
    assert record.documents is None and record.declaration is None
    # People without email skip straight to the call stage; the alert follows the stage.
    assert record.funnel["stage"] >= 1
    assert record.alert["level"] == record.funnel["stage"]
    assert record.route and all("state" in step for step in record.route)

    casos.responder_invitacion(run, True, "Web")
    casos.autorizar(run, True, "Web")
    record = ficha.build(rules.diagnosticar(profiles[run]), profiles[run], db)
    assert record.documents == [] and record.declaration == {}


def test_maximum_alert_only_for_unanswered_stage_four():
    assert ficha.alert_level(None)["level"] == 0
    assert ficha.alert_level({"stage": 4, "status": "active", "stage_label": "Presencial"})[
        "label"
    ].startswith("NIVEL MÁXIMO")
    assert (
        ficha.alert_level({"stage": 4, "status": "declined", "stage_label": "Presencial"})["level"]
        == 0
    )


def test_record_view_renders(tmp_path, monkeypatch):
    pytest.importorskip("streamlit", reason="Instalar el grupo app para verificar la UI")
    from streamlit.testing.v1 import AppTest

    app_dir = Path(__file__).resolve().parents[1] / "src/app"
    monkeypatch.syspath_prepend(str(app_dir))
    app_config = importlib.import_module("ruta.config")
    monkeypatch.setattr(app_config, "DB_PATH", tmp_path / "ui-ficha.db")
    monkeypatch.setattr(app_config, "BEDROCK_MODEL_ID", "")
    monkeypatch.setenv("FUNNEL_DEMO_DB", str(tmp_path / "lab.db"))
    app = AppTest.from_file(str(app_dir / "app.py"), default_timeout=30).run()
    app.radio(key="portal_section").set_value("Vista ejecutivo").run()
    app.radio(key="executive_section").set_value("Ficha del beneficiario").run()
    assert not app.exception
    assert any("Ficha del beneficiario" in h.value for h in app.header)


def test_every_portal_tab_renders(tmp_path, monkeypatch):
    pytest.importorskip("streamlit", reason="Instalar el grupo app para verificar la UI")
    from streamlit.testing.v1 import AppTest

    app_dir = Path(__file__).resolve().parents[1] / "src/app"
    monkeypatch.syspath_prepend(str(app_dir))
    app_config = importlib.import_module("ruta.config")
    monkeypatch.setattr(app_config, "DB_PATH", tmp_path / "ui-tabs.db")
    monkeypatch.setattr(app_config, "BEDROCK_MODEL_ID", "")
    monkeypatch.setenv("FUNNEL_DEMO_DB", str(tmp_path / "lab.db"))
    portal = importlib.import_module("portal")
    app = AppTest.from_file(str(app_dir / "app.py"), default_timeout=60).run()
    tabs = app.radio(key="portal_section")
    assert list(tabs.options) == portal.CITIZEN_SECTIONS + portal.OFFICE_SECTIONS
    assert list(tabs.options) == [
        "Inicio", "Mi Gobierno", "Ayuda para tus trámites", "Vista ejecutivo"
    ]
    for section in portal.CITIZEN_SECTIONS + portal.OFFICE_SECTIONS:
        app.radio(key="portal_section").set_value(section).run()
        assert not app.exception, section
    for tool in portal.EXECUTIVE_SECTIONS:
        app.radio(key="executive_section").set_value(tool).run()
        assert not app.exception, tool
    app.radio(key="portal_section").set_value("Inicio").run()
    assert not any(r.key == "executive_section" for r in app.radio)
    app.radio(key="portal_section").set_value("Vista ejecutivo").run()
    assert not app.exception
