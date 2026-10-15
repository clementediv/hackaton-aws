import pytest

from src.app.ruta import demo_auth
from src.app.ruta.datos import cargar_perfiles


def test_demo_login_resolves_formatted_run_and_rejects_bad_credentials():
    profiles = cargar_perfiles()
    run, profile = next(iter(profiles.items()))
    formatted = profile["registro_civil"]["run_formateado"]
    assert demo_auth.normalize_run(formatted) == run
    assert demo_auth.authenticate(formatted, "demo2026", profiles) == run
    for password in ("incorrecta", "contraseña", ""):
        with pytest.raises(ValueError):
            demo_auth.authenticate(run, password, profiles)
    with pytest.raises(ValueError):
        demo_auth.authenticate(run, "demo2026", set())
    for value in ("", "sin-rut", "12.345.678-0"):
        with pytest.raises(ValueError):
            demo_auth.normalize_run(value)


def test_login_gate_wrong_password_and_logout_do_not_grant_consent(tmp_path, monkeypatch):
    import importlib
    from pathlib import Path

    from streamlit.testing.v1 import AppTest

    app_dir = Path(__file__).resolve().parents[1] / "src/app"
    monkeypatch.syspath_prepend(str(app_dir))
    ui_config = importlib.import_module("ruta.config")
    monkeypatch.setattr(ui_config, "DB_PATH", tmp_path / "login.db")
    app = AppTest.from_file(str(app_dir / "app.py"), default_timeout=30).run()
    app.button(key="home_government_access").click().run()
    assert not app.exception
    run = app.selectbox(key="gov_demo_example").value
    app.text_input(key="gov_login_rut").set_value(run)
    app.text_input(key="gov_login_password").set_value("incorrecta")
    next(button for button in app.button if button.label == "Ingresar a Mi Gobierno").click().run()
    assert not app.exception
    assert app.error
    assert "government_login_run" not in app.session_state
    assert not app.chat_input
    app.text_input(key="gov_login_password").set_value("demo2026")
    next(button for button in app.button if button.label == "Ingresar a Mi Gobierno").click().run()
    assert not app.exception
    assert app.session_state["government_person"] == run
    ui_cases = importlib.import_module("ruta.casos")
    assert not ui_cases.obtener_caso(run)["autorizacion"]
    app.button(key="government_logout").click().run()
    assert "government_login_run" not in app.session_state
    assert not app.chat_input
