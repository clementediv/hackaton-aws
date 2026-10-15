import importlib
from pathlib import Path

from src.app.ruta import engagement, trazabilidad
from src.app.ruta.datos import cargar_perfiles
from src.app.ruta.ejecutivos import demo_snapshot


def event(run, kind, at, **data):
    return {"run": run, "tipo": kind, "fecha": at, "datos": data}


def test_ordered_milestones_ignore_attempts_starts_old_consent_and_duplicate_sessions():
    people = [{"run": run, "name": run} for run in ("A", "B", "C", "D")]
    events = [event(p["run"], "invitacion_enviada", "2026-10-01T09:00:00Z") for p in people]
    events += [
        event("A", "platform_login", "2026-10-01T10:00:00Z", session_id="first"),
        event("A", "platform_login", "2026-10-01T10:01:00Z", session_id="first"),
        event("A", "autorizacion_otorgada", "2026-10-01T11:00:00Z"),
        event("A", "eligible_step_completed", "2026-10-01T11:01:00Z", possible=True, step_id="G0"),
        event("A", "eligible_step_completed", "2026-10-01T11:02:00Z", possible=False, step_id="G1"),
        event("A", "eligible_step_completed", "2026-10-02T10:00:00Z", possible=True, step_id="G1"),
        event("A", "platform_login", "2026-10-04T10:00:00Z", session_id="second"),
        event("A", "process_viewed", "2026-10-04T10:02:00Z"),
        event("B", "colador_opened", "2026-10-01T10:00:00Z"),
        event("B", "colador_started", "2026-10-02T10:00:00Z"),
        event("C", "autorizacion_otorgada", "2026-10-01T11:00:00Z"),
        event("C", "platform_login", "2026-10-14T10:00:00Z", session_id="recent"),
        event("C", "eligible_step_completed", "2026-10-14T11:00:00Z", possible=True, step_id="G1"),
        event("D", "platform_login", "2026-09-30T10:00:00Z", session_id="before-alert"),
        event("D", "platform_login", "2026-12-30T10:00:00Z", session_id="future"),
    ]
    data = engagement.report(people, list(reversed(events)), "2026-10-15T12:00:00Z")
    assert data["counts"] == [4, 2, 1, 1]
    assert data["people"][0]["progress"] == engagement.parse_time("2026-10-02T10:00:00Z")
    assert data["returning"] == 1 and data["median_return_hours"] == 72
    assert data["views"] == 1
    assert data["retention"][0] == {"days": 7, "eligible": 1, "returned": 1, "percent": 100}
    assert data["retention"][1]["percent"] is None
    assert sum(day["Personas que ingresaron"] for day in data["daily"]) == 2


def test_record_is_idempotent_and_demo_is_explicit_and_isolated(tmp_path):
    assert engagement.parse_time("2026-10-15T09:00:00") == engagement.parse_time(
        "2026-10-15T12:00:00Z"
    )
    path = tmp_path / "records.db"
    for _ in range(2):
        engagement.record(path, "person", "platform_login", key="session:one", session_id="one")
    assert len(trazabilidad.load_events(path)) == 1
    profiles = cargar_perfiles()
    demo = tmp_path / "demo.db"
    state = demo_snapshot(profiles, demo)
    engagement.seed_demo(demo, state, profiles)
    first = trazabilidad.load_events(demo)
    engagement.seed_demo(demo, state, profiles)
    assert trazabilidad.load_events(demo) == first
    assert len(trazabilidad.load_events(path)) == 1
    usage = [e for e in first if e["tipo"] == "platform_login"]
    assert usage and all(e["datos"]["simulated"] for e in usage)
    data = engagement.report(state["people"], first, state["clock"]["now"])
    assert data["counts"][0] > data["counts"][1] > data["counts"][3] > 0
    assert data["returning"] > 0


def test_login_views_and_reconnection_are_persisted_without_counting_reruns(tmp_path, monkeypatch):
    from streamlit.testing.v1 import AppTest

    app_dir = Path(__file__).resolve().parents[1] / "src/app"
    monkeypatch.syspath_prepend(str(app_dir))
    config = importlib.import_module("ruta.config")
    monkeypatch.setattr(config, "DB_PATH", tmp_path / "app.db")
    monkeypatch.setattr(config, "BEDROCK_MODEL_ID", "")
    app = AppTest.from_file(str(app_dir / "app.py"), default_timeout=30).run()
    app.radio(key="portal_section").set_value("Mi Gobierno").run()
    run = app.selectbox(key="gov_demo_example").value

    def login():
        app.text_input(key="gov_login_rut").set_value(run)
        app.text_input(key="gov_login_password").set_value("demo2026")
        next(b for b in app.button if b.label == "Ingresar a Mi Gobierno").click().run()
        assert not app.exception

    login()
    app.run()
    events = trazabilidad.load_events(config.DB_PATH)
    assert sum(e["tipo"] == "platform_login" for e in events) == 1
    assert sum(e["tipo"] == "process_viewed" for e in events) == 0
    app.checkbox(key=f"gov_consent_{run}").check().run()
    next(b for b in app.button if b.label == "Activar Mi Gobierno").click().run()
    app.run()
    assert sum(e["tipo"] == "process_viewed" for e in trazabilidad.load_events(config.DB_PATH)) == 1
    app.radio(key=f"government_view_{run}").set_value("Datos personales").run()
    app.radio(key=f"government_view_{run}").set_value("Beneficios").run()
    app.button(key="government_logout").click().run()
    login()
    events = trazabilidad.load_events(config.DB_PATH)
    assert sum(e["tipo"] == "platform_login" for e in events) == 2
    assert sum(e["tipo"] == "platform_logout" for e in events) == 1
    assert sum(e["tipo"] == "process_viewed" for e in events) == 3
    sessions = [e["datos"]["session_id"] for e in events if e["tipo"] == "platform_login"]
    assert len(set(sessions)) == 2
