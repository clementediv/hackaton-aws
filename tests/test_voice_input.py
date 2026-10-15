import pytest

pytest.importorskip("streamlit")

from src.app import voice  # noqa: E402


def test_voice_submit_is_consumed_once_and_blank_input_is_not_sent(monkeypatch):
    monkeypatch.setattr(voice.st, "toggle", lambda *args, **kwargs: False)
    state = {}
    monkeypatch.setattr(voice.st, "session_state", state)
    monkeypatch.setattr(
        voice, "_component", lambda **kwargs: {"id": "first", "text": "  ¿Qué es PGU?  "}
    )
    assert voice.voice_input("chat") == "¿Qué es PGU?"
    assert voice.voice_input("chat") is None
    monkeypatch.setattr(voice, "_component", lambda **kwargs: {"id": "second", "text": " "})
    assert voice.voice_input("chat") is None
    monkeypatch.setattr(
        voice, "_component", lambda **kwargs: {"id": "third", "text": "Otra pregunta"}
    )
    assert voice.voice_input("chat") == "Otra pregunta"


def test_invalid_component_values_cannot_submit_messages(monkeypatch):
    monkeypatch.setattr(voice.st, "toggle", lambda *args, **kwargs: False)
    monkeypatch.setattr(voice.st, "session_state", {})
    for value in (None, "texto", {}, {"id": [], "text": "test"}, {"id": "id", "text": []}):
        monkeypatch.setattr(voice, "_component", lambda result=value, **kwargs: result)
        assert voice.voice_input("chat") is None


def test_spoken_text_keeps_source_names_without_reading_markdown_and_urls():
    text = voice.spoken_text(
        "**Podrías solicitarla.** Fuente: [ChileAtiende](https://www.chileatiende.gob.cl/fichas/102077)"
    )
    assert text == "Podrías solicitarla. Fuente: ChileAtiende"


def test_government_chat_resets_public_memory_and_voice_when_consent_changes(monkeypatch):
    from pathlib import Path

    from streamlit.testing.v1 import AppTest

    monkeypatch.syspath_prepend(str(Path(__file__).resolve().parents[1] / "src/app"))
    app = AppTest.from_string(
        "import streamlit as st\n"
        "import ui_persona\n"
        "from ruta import asistente, reglas\n"
        "from ruta.datos import cargar_perfiles\n"
        "from ruta.rutas import generar_ruta, estado_pasos, proximo_paso\n"
        "d = reglas.diagnosticar(cargar_perfiles()['100000010-4'])\n"
        "route = generar_ruta(d)\n"
        "states = estado_pasos(route, set())\n"
        "authorized = st.session_state.setdefault('test_authorized', True)\n"
        "ctx = asistente.construir_contexto(d, route, states, proximo_paso(route, states), authorized)\n"
        "ui_persona._asistente(d, d.run, 'Web ChileAtiende', ctx, sidebar=True)\n",
        default_timeout=30,
    ).run()
    assert not app.exception
    assert app.toggle[0].label == "Leer respuestas en voz alta"
    app.toggle[0].set_value(True).run()
    assert app.toggle[0].value
    app.session_state["general_chat_100000010-4"] = [{"rol": "user", "texto": "Un tema público"}]
    app.session_state["test_authorized"] = False
    app.run()
    assert not app.exception
    assert not app.toggle[0].value
    assert app.session_state["general_chat_100000010-4"] == []


def test_compact_voice_uses_composer_mic_without_separate_toggle(monkeypatch):
    def unexpected_toggle(*args, **kwargs):
        pytest.fail("El modo compacto no muestra el interruptor de voz separado")

    received = []
    monkeypatch.setattr(voice.st, "toggle", unexpected_toggle)
    monkeypatch.setattr(voice, "_component", lambda **kwargs: received.append(kwargs))
    assert voice.voice_input("public", compact=True) is None
    assert received[0]["compact"] is True
    assert received[0]["read_aloud"] is False
