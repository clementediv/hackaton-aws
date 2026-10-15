import importlib
from pathlib import Path

import pytest

from src.app.ruta import casos, config, government
from src.app.ruta import reglas as rules
from src.app.ruta.datos import cargar_perfiles


def test_pgu_actions_respect_all_dataset_results():
    for profile in cargar_perfiles().values():
        d = rules.diagnosticar(profile)
        _, action, allowed = government.pgu_action(d)
        assert (action == "Cobrar beneficio") == (d.vivo and d.pgu.resultado == rules.ELEGIBLE)
        if d.pgu.resultado in (rules.NO_ELEGIBLE, rules.FUTURO, rules.EXCLUIDO):
            assert not allowed
        route = government.benefit_route(d, "PGU")
        ids = {step.id for step in route}
        assert all(set(step.depende_de) <= ids for step in route)
        assert not any(step.tramite == "Jubilación" for step in route)


def test_personal_data_requires_consent_and_uploads_do_not_change_eligibility(
    tmp_path, monkeypatch
):
    monkeypatch.setattr(config, "DB_PATH", tmp_path / "personal.db")
    run, profile = next(iter(cargar_perfiles().items()))
    original = rules.diagnosticar(profile).to_dict()
    with pytest.raises(PermissionError):
        government.save_profile(run, {"monthly_income": 0})
    with pytest.raises(PermissionError):
        government.list_documents(run)
    casos.responder_invitacion(run, True, "Web")
    casos.autorizar(run, True, "Web")
    government.save_profile(run, {"monthly_income": 500000, "unexpected": "ignore"})
    assert government.load_profile(run) == {"monthly_income": 500000}
    government.save_document(run, "Registro Social de Hogares", "../../rsh.pdf", b"%PDF-1.7 demo")
    assert government.list_documents(run)[0]["name"] == "rsh.pdf"
    assert "content" not in government.list_documents(run)[0]
    assert rules.diagnosticar(profile).to_dict() == original
    with pytest.raises(ValueError):
        government.save_document(run, "Antecedentes", "fake.pdf", b"not a pdf")
    with pytest.raises(ValueError):
        government.save_document(
            run, "Antecedentes", "large.pdf", b"%PDF-" + b"a" * government.MAX_DOCUMENT_BYTES
        )
    casos.autorizar(run, False, "Web")
    with pytest.raises(PermissionError):
        government.load_profile(run)
    government.delete_personal_data(run)
    casos.autorizar(run, True, "Web")
    assert government.list_documents(run) == []
    assert government.load_profile(run) == {}


def test_government_consent_profile_steps_and_revocation(tmp_path, monkeypatch):
    from streamlit.testing.v1 import AppTest

    app_dir = Path(__file__).resolve().parents[1] / "src/app"
    monkeypatch.syspath_prepend(str(app_dir))
    ui_config = importlib.import_module("ruta.config")
    monkeypatch.setattr(ui_config, "DB_PATH", tmp_path / "gov-ui.db")
    monkeypatch.setattr(ui_config, "BEDROCK_MODEL_ID", "")
    app = AppTest.from_file(str(app_dir / "app.py"), default_timeout=30).run()
    app.button(key="header_government").click().run()
    assert not app.exception
    assert len(app.chat_input) == 0
    demo_run = app.selectbox(key="gov_demo_example").value
    app.text_input(key="gov_login_rut").set_value(demo_run)
    app.text_input(key="gov_login_password").set_value("demo2026")
    next(button for button in app.button if button.label == "Ingresar a Mi Gobierno").click().run()
    assert not app.exception
    assert app.session_state["government_login_run"] == demo_run
    assert not app.session_state.filtered_state.get("gov_login_password", "")
    assert not any(button.label == "Cobrar beneficio" for button in app.button)
    app.chat_input[0].set_value("¿Qué es la PGU?").run()
    assert not app.exception
    histories = [
        value for key, value in app.session_state.filtered_state.items() if key.startswith("chat-")
    ]
    assert any(
        any(message["texto"] == "¿Qué es la PGU?" for message in history) for history in histories
    )
    next(
        item for item in app.checkbox if item.label.startswith("Acepto el acompañamiento")
    ).check().run()
    next(button for button in app.button if button.label == "Activar Mi Gobierno").click().run()
    assert not app.exception
    run = app.session_state["government_person"]
    assert app.session_state[f"government_view_{run}"] == "Beneficios"
    assert any(item.placeholder == "Pregúntale al asistente de trámites" for item in app.chat_input)
    assert not any(item.label == "Profesión" for item in app.text_input)
    assert len([button for button in app.button if button.label == "Ver datos faltantes"]) == 3
    app.button(key="gov_check_fuas").click().run()
    assert not app.exception
    assert any("comprobante de inscripción" in element.value for element in app.markdown)
    assert len([button for button in app.button if button.label == "Cobrar beneficio"]) == 1
    assert not any(element.value == "**Sistema de salud**" for element in app.markdown)
    app.radio(key=f"government_view_{run}").set_value("Datos personales").run()
    assert len(app.chat_input) == 0
    assert any(section.label.replace("\u00a0", " ") == "03. Documentos" for section in app.expander)
    assert (
        len(
            [
                section
                for section in app.expander
                if section.label.startswith(("02.", "03.", "04.", "05."))
            ]
        )
        == 4
    )
    app.toggle(key=f"gov_restricted_{run}").set_value(True).run()
    assert not app.exception
    assert any(element.value == "**Sistema de salud**" for element in app.markdown)
    next(item for item in app.text_input if item.label == "Profesión").set_value("Administración")
    income = next(
        item for item in app.number_input if item.label == "Ingresos mensuales del hogar ($)"
    )
    income.set_value(350000)
    next(button for button in app.button if button.label == "Guardar mi información").click().run()
    assert not app.exception
    run = app.session_state["government_person"]
    ui_gov = importlib.import_module("ruta.government")
    assert ui_gov.load_profile(run)["monthly_income"] == 350000
    assert ui_gov.load_profile(run)["profession"] == "Administración"
    app.radio(key=f"government_view_{run}").set_value("Beneficios").run()
    app.button(key="gov_pgu_action").click().run()
    assert not app.exception
    assert any("paso a paso" in heading.value for heading in app.subheader)
    assert any(button.label == "Ya completé este paso" for button in app.button)
    next(button for button in app.button if button.label == "Ya completé este paso").click().run()
    assert not app.exception
    ui_cases = importlib.import_module("ruta.casos")
    assert "G0" in ui_cases.obtener_caso(run)["completados"]
    next(button for button in app.button if button.label == "← Volver a Mi Gobierno").click().run()
    ui_gov.save_document(run, "Cédula de identidad", "demo.pdf", b"%PDF-1.4 demo")
    app.run()
    # The same stored document appears in both PGU and FUAS, without uploading twice.
    assert len([item for item in app.text if item.value == "demo.pdf"]) == 2
    app.radio(key=f"government_view_{run}").set_value("Datos personales").run()
    assert len([item for item in app.text if item.value == "demo.pdf"]) == 1
    next(
        button for button in app.button if button.label.startswith("Revocar autorización")
    ).click().run()
    assert not app.exception
    assert ui_cases.obtener_caso(run)["autorizacion"]
    assert len(ui_gov.list_documents(run)) == 1
    assert ui_gov.load_profile(run)["monthly_income"] == 350000
    app.button(key=f"gov_revoke_cancel_{run}").click().run()
    assert ui_cases.obtener_caso(run)["autorizacion"]
    assert len(ui_gov.list_documents(run)) == 1
    app.button(key=f"gov_revoke_{run}").click().run()
    app.button(key=f"gov_revoke_confirm_{run}").click().run()
    assert not app.exception
    assert not ui_cases.obtener_caso(run)["autorizacion"]
    assert not any(button.label == "Cobrar beneficio" for button in app.button)
    ui_cases.autorizar(run, True, "Web")
    assert ui_gov.list_documents(run) == []
    assert ui_gov.load_profile(run) == {}
    app.button(key="government_logout").click().run()
    assert not app.exception
    assert "government_login_run" not in app.session_state
    assert any(item.label == "RUN" for item in app.text_input)
