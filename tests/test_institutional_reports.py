import importlib
import json
from datetime import UTC, datetime
from io import BytesIO
from pathlib import Path

import pytest
from pypdf import PdfReader

from src.app.ruta.institutional_pdf import generate_pdf
from src.app.ruta.institutional_reports import build_report

NOW = datetime(2026, 10, 16, 12, tzinfo=UTC)


def person(run, commune, status):
    return {
        "run": run,
        "name": f"NOMBRE_PRIVADO_{run}",
        "status": status,
        "contact": {"commune": commune, "email": "privado@example.com"},
    }


def event(run, kind, date, **detail):
    return {"run": run, "tipo": kind, "fecha": date, "datos": detail}


def fixture_report(communes=None):
    people = [
        person("RUN_PRIVADO_A", "Santiago", "active"),
        person("RUN_PRIVADO_B", "Santiago", "contacted"),
        person("RUN_PRIVADO_C", "Ñuñoa", "declined"),
        person("RUN_PRIVADO_D", "Ñuñoa", "started"),
    ]
    events = [event(p["run"], "invitacion_enviada", "2026-10-01T09:00:00Z") for p in people]
    events += [
        event("RUN_PRIVADO_B", "platform_login", "2026-10-01T10:00:00Z", session_id="1"),
        event("RUN_PRIVADO_B", "autorizacion_otorgada", "2026-10-01T11:00:00Z"),
        event(
            "RUN_PRIVADO_B",
            "eligible_step_completed",
            "2026-10-01T12:00:00Z",
            possible=True,
            step_id="G1",
        ),
        event("RUN_PRIVADO_A", "platform_login", "2027-10-01T10:00:00Z", session_id="future"),
    ]
    state = {"people": people + [people[0]], "clock": {"now": NOW.isoformat()}}
    return build_report(
        state,
        events,
        audience="Municipalidad",
        institution="Municipalidad de prueba",
        communes=communes,
        demo=True,
        now=NOW,
    )


def test_unique_counts_and_territorial_scope_use_real_ledger():
    data = fixture_report()
    assert data["total"] == 4
    assert [data[key] for key in ("pending", "guidance", "started", "declined")] == [1, 1, 1, 1]
    assert list(data["stages"].values()) == [4, 1, 1, 1]
    assert sum(row["people"] for row in data["territory"]) == data["total"]
    assert sum(row["progress"] for row in data["territory"]) == data["progress"]
    scoped = fixture_report(["Ñuñoa"])
    assert scoped["total"] == 2 and scoped["progress"] == 0
    assert scoped["pending"] == 0 and scoped["started"] == scoped["declined"] == 1
    assert len(scoped["territory"]) == 1
    assert any("no reactivar" in finding for finding in scoped["findings"])
    serialized = json.dumps(data)
    assert "RUN_PRIVADO" not in serialized and "NOMBRE_PRIVADO" not in serialized
    assert "privado@example.com" not in serialized


def test_missing_events_never_become_inferred_progress_and_unknown_territory_is_explicit():
    state = {"people": [person("PRIVATE", None, "started")], "clock": None}
    data = build_report(state, [], audience="Ministerio", institution="", now=NOW)
    assert data["started"] == 1 and list(data["stages"].values()) == [0, 0, 0, 0]
    assert data["territory"][0]["commune"] == "Sin comuna informada"
    assert data["institution"] == "Ministerio" and data["cutoff"] == NOW.isoformat()


@pytest.mark.parametrize("communes", [None, [], ["No existe"]])
def test_pdf_is_readable_and_preserves_scope_sources_and_no_personal_identifiers(communes):
    data = fixture_report(communes)
    pdf = generate_pdf(data)
    assert pdf.startswith(b"%PDF-")
    reader = PdfReader(BytesIO(pdf))
    content = "\n".join(page.extract_text() for page in reader.pages)
    for expected in (
        "Municipalidad de prueba",
        "Datos de ejemplo",
        "Alcance y fuentes",
        "Mi Gobierno",
        "no acredita",
        "Página 1",
    ):
        assert expected in content
    assert "RUN_PRIVADO" not in content and "NOMBRE_PRIVADO" not in content
    assert all(label not in content.upper() for label in ("MVP", "PROTOTIPO", "SIMULADO"))
    assert "privado@example.com" not in content
    if communes is None:
        assert "Ñuñoa" in content and "Santiago" in content
    else:
        assert "Sin casos" in content


def test_long_territorial_pdf_paginates_and_escapes_recipient():
    data = fixture_report()
    data["institution"] = "Ministerio <Equipo & Gestión>"
    data["territory"] = [
        dict(data["territory"][0], commune=f"Comuna de prueba número {i}") for i in range(80)
    ]
    reader = PdfReader(BytesIO(generate_pdf(data)))
    assert len(reader.pages) >= 3
    content = "\n".join(page.extract_text() for page in reader.pages)
    assert "Ministerio <Equipo & Gestión>" in content
    assert "Comuna de prueba número 79" in " ".join(content.split())
    assert all(f"Página {i}" in page.extract_text() for i, page in enumerate(reader.pages, 1))


def test_officer_can_filter_and_download_same_snapshot(tmp_path, monkeypatch):
    from streamlit.testing.v1 import AppTest

    app_dir = Path(__file__).resolve().parents[1] / "src/app"
    monkeypatch.syspath_prepend(str(app_dir))
    monkeypatch.setenv("STAFF_DEMO_DB", str(tmp_path / "campaign.db"))
    config = importlib.import_module("ruta.config")
    monkeypatch.setattr(config, "DB_PATH", tmp_path / "app.db")
    captured = []
    pdf_module = importlib.import_module("ruta.institutional_pdf")
    original = pdf_module.generate_pdf

    def capture(data):
        captured.append(data)
        return original(data)

    monkeypatch.setattr(pdf_module, "generate_pdf", capture)
    app = AppTest.from_file(str(app_dir / "app.py"), default_timeout=30).run()
    app.button(key="open_staff_header").click().run()
    assert not app.get("download_button")
    app.text_input(key="staff_login_email").set_value("ejecutivo.rm@example.com")
    auth = importlib.import_module("ruta.staff_auth")
    app.text_input(key="staff_login_password").set_value(auth.DEMO_PASSWORD)
    next(b for b in app.button if b.label == "Ingresar como ejecutivo").click().run()
    app.radio(key="staff_view").set_value("Campañas en terreno").run()
    app.number_input(key="staff_team").set_value(3).run()
    campaign_map = json.loads(app.get("deck_gl_json_chart")[0].proto.json)
    app.radio(key="staff_view").set_value("Reportería institucional").run()
    assert app.number_input(key="staff_team").value == 3
    report_map = json.loads(app.get("deck_gl_json_chart")[0].proto.json)
    assert report_map == campaign_map
    assert not app.exception
    assert app.get("download_button") and captured[-1]["demo"]
    commune = app.multiselect(key="institutional_communes").options[0]
    app.multiselect(key="institutional_communes").set_value([commune]).run()
    assert not app.exception
    assert captured[-1]["scope"] == [commune]
    assert len(captured[-1]["territory"]) == 1
    assert app.dataframe[0].value["Personas"].sum() == captured[-1]["total"]
    app.selectbox(key="institutional_audience").set_value("Ministerio").run()
    assert captured[-1]["audience"] == "Ministerio"
    app.multiselect(key="institutional_communes").set_value([]).run()
    assert not app.exception and captured[-1]["total"] == 0
    assert any("No hay casos" in info.value for info in app.info)

    app.selectbox(key="staff_source").set_value("Casos de la aplicación").run()
    assert not app.exception and captured[-1]["total"] == 0
    assert captured[-1]["demo"] is False and app.get("download_button")


def test_heatmap_reuses_published_pending_groups_and_respects_commune_filter(tmp_path):
    from src.app.ruta.datos import cargar_perfiles
    from src.app.ruta.ejecutivos import demo_snapshot
    from src.app.ruta.geografia import inside_commune

    profiles = cargar_perfiles()
    state = demo_snapshot(profiles, tmp_path / "geo.db")
    data = build_report(
        state, [], audience="Ministerio", institution="Prueba", demo=True, profiles=profiles
    )
    heat = data["heatmap"]
    assert heat["mapped"] == len(heat["points"]) > 0
    assert all(row["people"] >= 5 for row in heat["communes"])
    commune = heat["communes"][0]["commune"]
    scoped = build_report(
        state,
        [],
        audience="Municipalidad",
        institution=commune,
        demo=True,
        profiles=profiles,
        communes=[commune],
    )
    assert all(
        inside_commune(commune, p["latitude"], p["longitude"]) for p in scoped["heatmap"]["points"]
    )
    assert scoped["heatmap"]["communes"] == [heat["communes"][0]]
    assert set(scoped["heatmap"]["points"][0]) == {"latitude", "longitude", "weight"}
    serialized = json.dumps(data)
    assert all(person["run"] not in serialized for person in state["people"])
    terminal = {**state, "people": [dict(p, status="declined") for p in state["people"]]}
    empty = build_report(terminal, [], audience="Ministerio", institution="Prueba", demo=True)
    assert empty["heatmap"]["mapped"] == 0
    reader = PdfReader(BytesIO(generate_pdf(data)))
    assert len(reader.pages) == 3 and len(reader.pages[1].images) >= 1
    assert "Biblioteca del Congreso Nacional" in reader.pages[1].extract_text()
    assert "Pendientes de atención en terreno" in reader.pages[1].extract_text()
