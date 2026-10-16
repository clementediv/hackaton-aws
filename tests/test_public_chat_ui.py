import importlib
from pathlib import Path


def test_public_chat_replies_and_starts_a_new_conversation(monkeypatch):
    from streamlit.testing.v1 import AppTest

    monkeypatch.syspath_prepend(str(Path(__file__).resolve().parents[1] / "src/app"))
    config = importlib.import_module("ruta.config")
    monkeypatch.setattr(config, "BEDROCK_MODEL_ID", "")
    app = AppTest.from_string(
        "import streamlit as st\n"
        "import portal\n"
        "st.session_state['portal_home_page'] = "
        "st.Page(lambda: None, title='Inicio', default=True)\n"
        "portal.render_chat_page()",
        default_timeout=30,
    ).run()
    assert not app.exception
    app.chat_input[0].set_value("hola").run()
    assert not app.exception
    assert len(app.chat_message) == 2
    assert app.session_state["public_chat_history"][0]["texto"] == "hola"
    app.button(key="public_chat_reset").click().run()
    assert not app.exception
    assert app.session_state["public_chat_history"] == []
    assert not app.chat_message


def test_personal_pgu_review_does_not_leak_into_public_model_history(monkeypatch):
    from streamlit.testing.v1 import AppTest

    monkeypatch.syspath_prepend(str(Path(__file__).resolve().parents[1] / "src/app"))
    cases = importlib.import_module("ruta.casos")
    assistant = importlib.import_module("ruta.asistente")
    rules = importlib.import_module("ruta.reglas")
    profiles = importlib.import_module("ruta.datos").cargar_perfiles()
    run = next(run for run, profile in profiles.items()
               if rules.diagnosticar(profile).pgu.resultado == rules.ANTECEDENTE_FALTANTE)
    case = {"autorizacion": True, "completados": set()}
    monkeypatch.setattr(cases, "obtener_caso", lambda _: case)
    monkeypatch.setattr(assistant.time, "sleep", lambda _: None)
    received = []

    def public(question, history, **kwargs):
        received.append(history)
        return iter(["Explicación pública"]), "plantillas"

    monkeypatch.setattr(assistant, "responder_publico", public)
    app = AppTest.from_string(
        "import streamlit as st\nimport portal\n"
        f"st.session_state['government_login_run'] = {run!r}\n"
        "st.session_state['portal_home_page'] = st.Page(lambda: None, default=True)\n"
        "portal.render_chat_page()", default_timeout=30,
    ).run()
    app.chat_input[0].set_value("Quiero revisar si soy apto para la PGU").run()
    assert not app.exception
    assert received == []
    assert "Antecedentes que faltan" in app.session_state["public_chat_history"][-1]["texto"]
    app.chat_input[-1].set_value("¿Qué es la PGU?").run()
    assert not app.exception
    assert received == [[]]
    case["autorizacion"] = False
    app.run()
    assert not app.exception
    assert all(m.get("scope") != "personal" for m in app.session_state["public_chat_history"])
