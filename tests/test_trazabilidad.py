import csv
import importlib
import io
from pathlib import Path

import pytest

from src.app.ruta import casos, config, trazabilidad
from src.app.ruta.datos import cargar_perfiles
from src.app.ruta.ejecutivos import demo_snapshot


@pytest.fixture(scope="module")
def campaign(tmp_path_factory):
    path = tmp_path_factory.mktemp("traza") / "campaign.db"
    return demo_snapshot(cargar_perfiles(), path), path


def test_every_funnel_event_is_recorded_with_date_channel_and_type(campaign):
    state, path = campaign
    events = trazabilidad.load_events(path)
    quality = trazabilidad.quality(events)
    assert quality["eventos"] == len(state["events"])  # mirrored one-to-one
    assert quality["porcentaje"] == 100
    assert quality["casos"] == len(state["people"])
    assert all(e["origen"] == trazabilidad.LOCAL_SOURCE for e in events)
    assert "Intento de contacto" in {e["evento"] for e in events}


def test_kpi_table_says_what_is_recorded_and_what_is_missing(campaign):
    state, path = campaign
    rows = {
        r["Indicador"]: r
        for r in trazabilidad.kpi_evidence(state["people"], trazabilidad.load_events(path))
    }
    assert set(rows) == {
        "Contacto efectivo",
        "Acepta el acompañamiento",
        "Próximo paso válido dentro del plazo",
        "Continuidad entre canales",
    }
    next_step = rows["Próximo paso válido dentro del plazo"]
    assert next_step["Meta"] == "Al menos 75%" and next_step["Registro"] == "Parcial"
    detected = state["totals"]["detected"]
    confirmed = state["totals"]["confirmed_contacts"]
    assert rows["Contacto efectivo"]["Casos con evidencia (demo)"] == (
        f"{confirmed} de {detected} casos"
    )
    started = state["totals"]["started"]
    assert next_step["Casos con evidencia (demo)"] == f"{started} de {detected} casos"


def test_case_steps_and_authorization_are_traced(tmp_path, monkeypatch):
    monkeypatch.setattr(config, "DB_PATH", tmp_path / "app.db")
    casos.invitar(["100000001-5"], "Web ChileAtiende")
    casos.responder_invitacion("100000001-5", True, "WhatsApp")
    casos.autorizar("100000001-5", True, "WhatsApp")
    casos.completar_paso("100000001-5", "G1", "Sucursal ChileAtiende", "Solicitar PGU")
    events = trazabilidad.load_events(tmp_path / "app.db")
    assert [e["evento"] for e in events] == [
        "Invitación enviada",
        "Aceptó el acompañamiento",
        "Autorizó el uso de sus datos",
        "Completó un paso del trámite",
    ]
    assert events[-1]["detalle"] == "Solicitar PGU"
    rows = trazabilidad.kpi_evidence([], events)
    assert all(r["Casos con evidencia (demo)"] == "1 de 1 casos" for r in rows)


def test_follow_up_flags_open_cases_without_movement(campaign):
    state, path = campaign
    events = trazabilidad.load_events(path)
    now = state["clock"]["now"]
    stale = trazabilidad.follow_up(state["people"], events, now, stale_days=7)
    status = {p["run"]: p["status"] for p in state["people"]}
    assert stale and all(status[r["run"]] in ("active", "contacted") for r in stale)
    assert [r["days"] for r in stale] == sorted((r["days"] for r in stale), reverse=True)
    assert all(r["days"] >= 7 for r in stale)
    assert len(trazabilidad.follow_up(state["people"], events, now, stale_days=30)) <= len(stale)


def test_timeline_merges_aws_history_and_exports_csv(campaign):
    state, path = campaign
    events = trazabilidad.load_events(path)
    run = state["people"][0]["run"]
    aws = trazabilidad.aws_events(
        [
            {
                "run": run,
                "sk": "2030-01-01T10:00:00.000000#000001#abc",
                "evento": "email_enviado",
                "evento_texto": "Email enviado",
                "canal": "email",
                "detalle": {"asunto": "Prepare su trámite"},
            }
        ]
    )
    rows = trazabilidad.timeline(run, events, aws)
    assert rows[-1]["origen"] == trazabilidad.AWS_SOURCE
    assert rows[-1]["detalle"] == "Prepare su trámite"
    assert [r["fecha"] for r in rows] == sorted(r["fecha"] for r in rows)
    exported = list(csv.reader(io.StringIO(trazabilidad.audit_csv(events))))
    assert exported[0] == ["run", "fecha", "canal", "tipo", "evento", "detalle", "origen"]
    assert len(exported) == len(events) + 1


def test_missing_database_has_no_events(tmp_path):
    assert trazabilidad.load_events(tmp_path / "nope.db") == []


def test_staff_portal_shows_traceability(tmp_path, monkeypatch):
    st = pytest.importorskip("streamlit", reason="Instalar el grupo app para verificar la UI")
    from streamlit.testing.v1 import AppTest

    st.cache_data.clear()
    app_dir = Path(__file__).resolve().parents[1] / "src/app"
    monkeypatch.syspath_prepend(str(app_dir))
    monkeypatch.setenv("STAFF_DEMO_DB", str(tmp_path / "staff.db"))
    staff = importlib.import_module("ui_ejecutivos")
    # The officer login (if present) is covered by its own tests.
    monkeypatch.setattr(staff, "require_login", lambda: True, raising=False)
    aws = importlib.import_module("ruta.aws_contactos")
    monkeypatch.setattr(aws, "check", lambda dynamodb=None: (False, "Sin AWS en la prueba."))
    app = AppTest.from_file(str(app_dir / "app.py"), default_timeout=60)
    app.query_params["vista"] = "ejecutivos"
    app.run()
    sections = next(r for r in app.radio if r.label == "Secciones de gestión")
    sections.set_value("Trazabilidad").run()
    assert not app.exception
    indicators = app.dataframe[0].value["Indicador"].tolist()
    assert "Próximo paso válido dentro del plazo" in indicators
    assert any("Sin AWS en la prueba." in c.value for c in app.caption)
    html = " ".join(h.proto.body for h in app.get("html"))
    assert "no es posible demostrar que la meta de 75%" in html
