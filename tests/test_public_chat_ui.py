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
