"""CESFAM front desk and referrals to the officer (20-arquitectura/cesfam-derivacion.md)."""

import importlib
from pathlib import Path
from types import SimpleNamespace

import pytest

from src.app.ruta import casos, config, derivaciones

APP_DIR = Path(__file__).resolve().parents[1] / "src/app"
FIELD = {
    "run": "1-9",
    "beneficio_id": "pgu",
    "beneficio": "PGU",
    "estado": "terreno",
    "estado_texto": "Asignado a equipo en terreno",
    "nombre": "Ana",
}


@pytest.fixture
def db(tmp_path, monkeypatch):
    monkeypatch.setattr(config, "DB_PATH", tmp_path / "cases.db")


def _ficha(documents=None, authorized=False):
    return SimpleNamespace(
        identity={"name": "Ana Pérez", "age": 66, "formatted_run": "1.234.567-8"},
        pgu={"result": "elegible", "reason": "Cumple los requisitos."},
        case={"invitation": "invitado", "invitation_channel": "WhatsApp", "authorized": authorized},
        funnel={"stage_label": "Presencial", "attempts": 5},
        documents=documents,
        next_step={"titulo": "Solicitar la PGU", "donde": "IPS / ChileAtiende"},
    )


def test_maximum_alert_comes_from_the_funnel_or_aws():
    assert derivaciones.max_alert({"level": 4}, []).startswith("No respondió a ningún canal")
    assert "PGU" in derivaciones.max_alert({"level": 0}, [FIELD])
    assert derivaciones.max_alert({"level": 3}, [{**FIELD, "estado": "email_enviado"}]) is None
    assert derivaciones.max_alert(None, []) is None


def test_summary_lists_documents_only_with_consent():
    rows = {r["label"]: r["value"] for r in derivaciones.summarize(_ficha(), [FIELD], "motivo")}
    assert rows["Documentos"] == "Sin autorización para revisarlos"
    assert rows["Alerta"] == "motivo"
    assert rows["Próximo paso"] == "Solicitar la PGU (IPS / ChileAtiende)"
    assert rows["Detección AWS"] == "PGU: Asignado a equipo en terreno"
    docs = [{"kind": "Cédula de identidad"}]
    rows = {r["label"]: r["value"] for r in derivaciones.summarize(_ficha(docs, True), [], "")}
    assert rows["Documentos"] == "1 adjuntos: Cédula de identidad"
    assert rows["Autorización de datos"] == "Vigente"
    assert "Alerta" not in rows and "Detección AWS" not in rows


def test_summary_for_people_only_on_aws():
    rows = derivaciones.summarize(None, [FIELD], "motivo")
    assert rows[0] == {"label": "Persona", "value": "Ana · RUN 1-9"}


def test_one_pending_referral_per_person_and_attending_closes_it(db):
    summary = [{"label": "Alerta", "value": "x"}]
    ref_id = derivaciones.refer("1-9", "CESFAM", "x", summary)
    assert ref_id and derivaciones.refer("1-9", "CESFAM", "x", summary) is None
    assert [r["run"] for r in derivaciones.pending()] == ["1-9"]
    assert derivaciones.pending()[0]["summary"] == summary
    assert derivaciones.attend(ref_id, "ejecutivo@example.com", "Sucursal ChileAtiende") == "1-9"
    assert derivaciones.attend(ref_id, "otro", "Sucursal ChileAtiende") is None
    assert derivaciones.pending() == []
    assert derivaciones.for_run("1-9")[0]["attended_by"] == "ejecutivo@example.com"
    events = [e["tipo"] for e in casos.obtener_caso("1-9")["eventos"]]
    assert events == ["derivacion", "derivacion_atendida"]
    assert derivaciones.refer("1-9", "CESFAM", "y", summary)  # a new one after attending
    casos.reiniciar()
    assert derivaciones.for_run("1-9") == []


def test_funnel_max_runs_without_a_funnel(db):
    assert derivaciones.funnel_max_runs() == []


def _executive_app(monkeypatch, tmp_path, contacts_by_run):
    pytest.importorskip("streamlit", reason="Instalar el grupo app para verificar la UI")
    from streamlit.testing.v1 import AppTest

    monkeypatch.syspath_prepend(str(APP_DIR))
    app_config = importlib.import_module("ruta.config")
    monkeypatch.setattr(app_config, "DB_PATH", tmp_path / "ui-cesfam.db")
    monkeypatch.setattr(app_config, "BEDROCK_MODEL_ID", "")
    ui_aws = importlib.import_module("ui_aws")
    monkeypatch.setattr(ui_aws, "person_contacts", lambda run: contacts_by_run.get(run, []))
    monkeypatch.setattr(ui_aws, "field_runs", lambda: list(contacts_by_run))
    app = AppTest.from_file(str(APP_DIR / "app.py"), default_timeout=60).run()
    app.button(key="open_executive").click().run()
    app.text_input(key="staff_login_email").set_value("ejecutivo.rm@example.com")
    app.text_input(key="staff_login_password").set_value("Ejecutivo2026!")
    next(b for b in app.button if b.label == "Ingresar como ejecutivo").click().run()
    app.radio(key="executive_section").set_value("Punto CESFAM").run()
    assert not app.exception
    return app


def _alive_run() -> str:
    datos = importlib.import_module("ruta.datos")
    reglas = importlib.import_module("ruta.reglas")
    return next(r for r, p in datos.cargar_perfiles().items() if reglas.diagnosticar(p).vivo)


def test_cesfam_refers_and_the_officer_attends(monkeypatch, tmp_path):
    pytest.importorskip("streamlit")
    monkeypatch.syspath_prepend(str(APP_DIR))
    run = _alive_run()
    app = _executive_app(monkeypatch, tmp_path, {run: [{**FIELD, "run": run}]})
    assert any(run in c.value for c in app.caption)  # demo examples
    app.text_input(key="cesfam_run").set_value(run).run()
    shown = [e.value for e in [*app.markdown, *app.caption, *app.info, *app.success]]
    assert any("Derivar a ChileAtiende" in v for v in shown)
    # The CESFAM never sees the reason, the benefit or its state.
    assert not any("Sin respuesta al email" in v or "terreno" in v for v in shown)
    app.button(key="cesfam_refer").click().run()
    assert "Caso derivado" in app.success[0].value
    refs = importlib.import_module("ruta.derivaciones")
    assert [r["run"] for r in refs.pending()] == [run]

    app.radio(key="executive_section").set_value("Atención del caso").run()
    assert any("Derivaciones pendientes" in e.label for e in app.expander)
    next(b for b in app.button if b.label == "Atender").click().run()
    assert not app.exception
    assert app.selectbox(key="atencion_persona").value.startswith(run)
    assert refs.pending() == []
    assert refs.for_run(run)[0]["attended_by"] == "ejecutivo.rm@example.com"


def test_cesfam_without_alert(monkeypatch, tmp_path):
    pytest.importorskip("streamlit")
    monkeypatch.syspath_prepend(str(APP_DIR))
    run = _alive_run()
    app = _executive_app(monkeypatch, tmp_path, {})
    app.text_input(key="cesfam_run").set_value(run).run()
    assert app.success[0].value == "Sin avisos de ChileAtiende para esta persona."
    app.text_input(key="cesfam_run").set_value("12.345.678-0").run()
    assert "dígito verificador" in app.error[0].value
