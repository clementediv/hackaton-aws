"""Next valid step within the deadline (20-arquitectura/kpi-proximo-paso.md)."""

import importlib
from datetime import datetime
from pathlib import Path

import pytest

from src.app.ruta import casos, config, kpi, trazabilidad

APP_DIR = Path(__file__).resolve().parents[1] / "src/app"
NOW = datetime(2026, 12, 31, 12)


def ev(run, tipo, fecha, **datos):
    return {"run": run, "tipo": tipo, "fecha": fecha + "+00:00", "datos": datos}


def by_run(events, now=NOW):
    return {r["run"]: r for r in kpi.outcomes(events, now)}


def test_accepting_or_starting_is_not_a_step():
    rows = by_run(
        [
            ev("A", "invitacion_enviada", "2026-10-01T10:00:00"),
            ev("A", "invitacion_aceptada", "2026-10-01T11:00:00"),
            ev("A", "paso_completado", "2026-10-02T10:00:00", paso="G0"),
            ev("A", "colador_started", "2026-10-03T10:00:00"),
            ev(
                "B", "invitacion_enviada", "2026-10-01T10:00:00"
            ),  # never answered: not in the cohort
        ]
    )
    assert set(rows) == {"A"}
    assert rows["A"]["estado"] == kpi.EXPIRED


def test_on_time_late_and_open():
    rows = by_run(
        [
            ev("A", "invitacion_aceptada", "2026-10-01T11:00:00"),
            ev(
                "A", "paso_completado", "2026-10-20T10:00:00", paso="G1", titulo="Actualizar el RSH"
            ),
            ev("B", "colador_answered", "2026-10-01T11:00:00"),
            ev("B", "paso_completado", "2026-11-15T10:00:00", paso="G1"),
            ev("C", "invitacion_aceptada", "2026-12-20T11:00:00"),
        ]
    )
    assert rows["A"]["estado"] == kpi.ON_TIME and rows["A"]["paso_titulo"] == "Actualizar el RSH"
    assert rows["B"]["estado"] == kpi.LATE
    assert rows["C"]["estado"] == kpi.OPEN and not rows["C"]["plazo_cumplido"]


def test_declared_progress_needs_a_possible_benefit():
    rows = by_run(
        [
            ev("A", "invitacion_aceptada", "2026-10-01T11:00:00"),
            ev("A", "eligible_step_completed", "2026-10-02T10:00:00", step_id="G1", possible=False),
            ev("B", "invitacion_aceptada", "2026-10-01T11:00:00"),
            ev("B", "eligible_step_completed", "2026-10-02T10:00:00", step_id="G1", possible=True),
        ]
    )
    assert rows["A"]["estado"] == kpi.EXPIRED
    assert rows["B"]["estado"] == kpi.ON_TIME


def test_final_decline_leaves_the_cohort_and_reopening_restarts_the_deadline():
    rows = by_run(
        [
            ev("A", "invitacion_aceptada", "2026-10-01T11:00:00"),
            ev("A", "invitacion_rechazada", "2026-10-02T11:00:00"),
            ev("B", "invitacion_rechazada", "2026-10-01T11:00:00"),
            ev("B", "invitacion_aceptada", "2026-12-15T11:00:00"),
        ]
    )
    assert set(rows) == {"B"}
    assert rows["B"]["contacto"] == datetime(2026, 12, 15, 11)


def test_reopened_step_stops_counting():
    rows = by_run(
        [
            ev("A", "invitacion_aceptada", "2026-10-01T11:00:00"),
            ev("A", "paso_completado", "2026-10-02T10:00:00", paso="G1"),
            ev("A", "paso_reabierto", "2026-10-03T10:00:00", paso="G1"),
        ]
    )
    assert rows["A"]["estado"] == kpi.EXPIRED


def test_kpi_only_over_people_whose_deadline_passed():
    events = [
        ev("A", "invitacion_aceptada", "2026-10-01T11:00:00"),
        ev("A", "paso_completado", "2026-10-02T10:00:00", paso="G1"),
        ev("B", "invitacion_aceptada", "2026-10-01T11:00:00"),
        ev("C", "invitacion_aceptada", "2026-12-20T11:00:00"),
        ev("C", "paso_completado", "2026-12-21T10:00:00", paso="G1"),
    ]
    result = kpi.summary(kpi.outcomes(events, NOW))
    assert result["plazo_cumplido"] == 2 and result["kpi"] == 0.5
    assert result["provisional"] == pytest.approx(2 / 3)
    early = kpi.summary(kpi.outcomes(events[:3], datetime(2026, 10, 5)))  # A and B only
    assert early["kpi"] is None and early["cohorte"] == 2 and early["provisional"] == 0.5


def test_measured_on_the_case_log(tmp_path, monkeypatch):
    monkeypatch.setattr(config, "DB_PATH", tmp_path / "cases.db")
    casos.invitar(["1-9"], "WhatsApp")
    casos.responder_invitacion("1-9", True, "WhatsApp")
    casos.completar_paso("1-9", "G1", "WhatsApp", "Actualizar el RSH")
    rows = kpi.outcomes(
        trazabilidad.load_events(config.DB_PATH), kpi.reference_time(config.DB_PATH)
    )
    assert [(r["run"], r["estado"]) for r in rows] == [("1-9", kpi.ON_TIME)]


def test_measurement_view(tmp_path, monkeypatch):
    pytest.importorskip("streamlit", reason="Instalar el grupo app para verificar la UI")
    from streamlit.testing.v1 import AppTest

    monkeypatch.syspath_prepend(str(APP_DIR))
    app_config = importlib.import_module("ruta.config")
    monkeypatch.setattr(app_config, "DB_PATH", tmp_path / "ui-kpi.db")
    monkeypatch.setattr(app_config, "BEDROCK_MODEL_ID", "")
    app_cases = importlib.import_module("ruta.casos")
    app_cases.responder_invitacion("1-9", True, "WhatsApp")
    app = AppTest.from_file(str(APP_DIR / "app.py"), default_timeout=60).run()
    app.button(key="open_executive").click().run()
    app.text_input(key="staff_login_email").set_value("ejecutivo.rm@example.com")
    app.text_input(key="staff_login_password").set_value("Ejecutivo2026!")
    next(b for b in app.button if b.label == "Ingresar como ejecutivo").click().run()
    app.radio(key="executive_section").set_value("Medición").run()
    assert not app.exception
    metrics = {m.label: m.value for m in app.metric}
    assert metrics["⭐ Próximo paso dentro del plazo"] == "Sin medir"
    assert app.dataframe[0].value.iloc[0]["Estado"] == kpi.LABELS[kpi.OPEN]
