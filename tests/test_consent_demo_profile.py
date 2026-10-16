import importlib
from pathlib import Path

import pytest

from src.app.ruta import demo_auth
from src.app.ruta.datos import cargar_perfiles
from src.app.ruta.demo_profiles import CONSENT_DEMO_RUN, load_citizen_profiles
from src.app.ruta.pgu_review import review_pgu
from src.tools.profiles import normalize_run


@pytest.mark.parametrize("login", ["123456789", "12345678-9", "12.345.678-9"])
def test_extra_demo_account_keeps_normal_run_validation_strict(login):
    profiles = load_citizen_profiles()
    assert demo_auth.authenticate(login, "demo2026", profiles) == CONSENT_DEMO_RUN
    with pytest.raises(ValueError):
        demo_auth.authenticate(login, "incorrecta", profiles)
    with pytest.raises(ValueError):
        demo_auth.authenticate(login, "demo2026", cargar_perfiles())
    with pytest.raises(ValueError):
        demo_auth.normalize_run(login)
    with pytest.raises(ValueError):
        normalize_run("12345678-9")


def test_extra_profile_does_not_modify_dataset_and_works_in_authorized_chat():
    assert len(cargar_perfiles()) == 500
    assert CONSENT_DEMO_RUN not in cargar_perfiles()
    profiles = load_citizen_profiles()
    profiles[CONSENT_DEMO_RUN]["registro_civil"]["nombres"] = "Changed"
    assert load_citizen_profiles()[CONSENT_DEMO_RUN]["registro_civil"]["nombres"] == "Persona"
    text = review_pgu(CONSENT_DEMO_RUN, {"autorizacion": True}, load_citizen_profiles)
    assert "Faltan antecedentes" in text
    assert "Registro Social de Hogares" in text
    assert "No encontré" not in text


def test_new_demo_account_requests_consent_on_every_login(tmp_path, monkeypatch):
    from streamlit.testing.v1 import AppTest

    app_dir = Path(__file__).resolve().parents[1] / "src/app"
    monkeypatch.syspath_prepend(str(app_dir))
    config = importlib.import_module("ruta.config")
    cases = importlib.import_module("ruta.casos")
    monkeypatch.setattr(config, "DB_PATH", tmp_path / "consent-demo.db")
    monkeypatch.setattr(config, "BEDROCK_MODEL_ID", "")
    app = AppTest.from_file(str(app_dir / "app.py"), default_timeout=30).run()
    app.button(key="home_government_access").click().run()

    def login():
        app.text_input(key="gov_login_rut").set_value("123456789")
        app.text_input(key="gov_login_password").set_value("demo2026")
        next(b for b in app.button if b.label == "Ingresar a Mi Gobierno").click().run()
        assert not app.exception
        assert app.session_state["government_login_run"] == CONSENT_DEMO_RUN
        assert not cases.obtener_caso(CONSENT_DEMO_RUN)["autorizacion"]
        assert not app.checkbox(key=f"gov_consent_{CONSENT_DEMO_RUN}").value
        assert next(b for b in app.button if b.label == "Activar Mi Gobierno").disabled
        assert any("Autoriza el uso de tus datos" in m.value for m in app.markdown)
        assert not any("gov-requirement-card" in e.proto.body for e in app.get("html"))
        assert not app.session_state.filtered_state.get("gov_login_password")

    login()
    app.checkbox(key=f"gov_consent_{CONSENT_DEMO_RUN}").check().run()
    next(b for b in app.button if b.label == "Activar Mi Gobierno").click().run()
    assert not app.exception
    assert cases.obtener_caso(CONSENT_DEMO_RUN)["autorizacion"]
    assert any("gov-requirement-card" in e.proto.body for e in app.get("html"))
    app.radio(key=f"government_view_{CONSENT_DEMO_RUN}").set_value("Datos personales").run()
    assert not app.exception
    app.button(key="government_logout").click().run()
    login()
