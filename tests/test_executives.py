import importlib
import json
from pathlib import Path

import pytest

from src.app.ruta.datos import cargar_perfiles
from src.app.ruta.despliegue import _unproject, automatic_campaign_area
from src.app.ruta.ejecutivos import case_rows, demo_snapshot


def point(x):
    longitude, latitude = _unproject(x, 0)
    return dict(
        latitude=latitude, longitude=longitude, weight=1, commune="Santiago", synthetic=True
    )


def test_automatic_area_scales_to_team_and_omits_small_groups():
    locations = [point(i * 10) for i in range(8)]
    locations += [point(2600 + i * 10) for i in range(8)]
    small = automatic_campaign_area(locations, staff=1)["properties"]
    large = automatic_campaign_area(locations, staff=2)["properties"]
    assert small["radius_m"] == 750 and small["people"] == 8
    assert large["radius_m"] == 1500 and large["people"] == 16
    assert large["automatic"] and large["target_people"] == 16
    assert automatic_campaign_area(locations[:4]) is None
    assert automatic_campaign_area([point(i * 10000) for i in range(5)]) is None
    for staff in (0, 21, True, 1.5):
        with pytest.raises(ValueError):
            automatic_campaign_area(locations, staff=staff)


def test_demo_preserves_state_and_filters_without_private_profile_data(tmp_path):
    path = tmp_path / "staff.db"
    state = demo_snapshot(cargar_perfiles(), path)
    assert demo_snapshot(cargar_perfiles(), path) == state
    totals = state["totals"]
    assert totals["detected"] == sum(
        totals[k] for k in ("active", "contacted", "started", "declined")
    )
    rows = case_rows(state, status="Espera orientación")
    assert len(rows) == totals["contacted"] > 0
    assert all(row["next_action"] == "Orientar y acordar el próximo paso" for row in rows)
    selected = rows[0]
    assert case_rows(state, search=selected["run"], commune=selected["commune"]) == [selected]
    assert case_rows(state, search="DOES-NOT-EXIST") == []
    assert "Respetar" in case_rows(state, status="Declinó")[0]["next_action"]
    assert all(set(row) == {"run", "name", "commune", "status", "next_action"} for row in rows)
    assert "monthly_income" not in json.dumps(rows)


def test_staff_portal_navigation_filters_and_automatic_campaign(tmp_path, monkeypatch):
    from streamlit.testing.v1 import AppTest

    app_dir = Path(__file__).resolve().parents[1] / "src/app"
    monkeypatch.syspath_prepend(str(app_dir))
    monkeypatch.setenv("STAFF_DEMO_DB", str(tmp_path / "staff.db"))
    config = importlib.import_module("ruta.config")
    monkeypatch.setattr(config, "DB_PATH", tmp_path / "application.db")
    app = AppTest.from_file(str(app_dir / "app.py"), default_timeout=30).run()
    app.button(key="open_staff_header").click().run()
    assert not app.exception
    assert app.radio[1].options == ["Seguimiento de casos", "Campañas en terreno", "Trazabilidad"]
    app.selectbox(key="staff_status").set_value("Espera orientación").run()
    assert set(app.dataframe[0].value["Situación"]) == {"Espera orientación"}
    app.text_input(key="staff_search").set_value("DOES-NOT-EXIST").run()
    assert any("coincidan" in info.value for info in app.info)
    app.radio[1].set_value("Campañas en terreno").run()
    assert not app.exception
    assert [field.label for field in app.number_input] == ["Personal disponible"]
    assert not app.slider
    assert app.get("deck_gl_json_chart")
    app.number_input(key="staff_team").set_value(4).run()
    assert not app.exception
    app.selectbox(key="staff_source").set_value("Casos de la aplicación").run()
    assert not app.exception
    assert any("aún no tiene casos" in info.value for info in app.info)
    app.radio(key="portal_section").set_value("Inicio").run()
    assert not app.exception
    assert not app.session_state.filtered_state.get("portal_staff_workspace")


def test_staff_deep_link_opens_new_workspace(tmp_path, monkeypatch):
    from streamlit.testing.v1 import AppTest

    app_dir = Path(__file__).resolve().parents[1] / "src/app"
    monkeypatch.syspath_prepend(str(app_dir))
    monkeypatch.setenv("STAFF_DEMO_DB", str(tmp_path / "deep.db"))
    app = AppTest.from_file(str(app_dir / "app.py"), default_timeout=30)
    app.query_params["vista"] = "ejecutivos"
    app.run()
    assert not app.exception
    assert app.session_state["portal_staff_workspace"]
