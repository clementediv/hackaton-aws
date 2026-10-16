import pytest

from src.agent.bedrock import BedrockClient, BedrockSettings
from src.app.ruta import asistente, chatbot


def test_progressive_render_preserves_text_without_adding_a_cursor():
    from src.app.chat_feedback import render_text_stream

    rendered = []

    class Target:
        def markdown(self, text):
            rendered.append(text)

    chunks = ["Hola. ", "Consulta la [fuente](https://example.com)."]
    result = render_text_stream(Target(), iter(chunks))
    assert rendered == [chunks[0], "".join(chunks)]
    assert result == "".join(chunks)


def test_stream_yields_first_fragment_before_consuming_the_answer(monkeypatch):
    source = "https://www.ventanillaunicasocial.gob.cl/ficha/95/pension-garantizada-universal"
    monkeypatch.setattr(
        chatbot, "context_for", lambda *args: f"URL: {source}\nPGU: aporte estatal."
    )
    consumed = []

    class Runtime:
        def converse_stream(self, **kwargs):
            assert kwargs["modelId"] == BedrockSettings().model_id
            assert kwargs["messages"][-1]["content"] == [{"text": "¿Qué es la PGU?"}]

            def events():
                for text in ["La PGU ", "es un beneficio."]:
                    consumed.append(text)
                    yield {"contentBlockDelta": {"delta": {"text": text}}}

            return {"stream": events()}

    stream = chatbot.answer_general(
        "¿Qué es la PGU?", client=BedrockClient(BedrockSettings(), Runtime()), stream=True
    )
    assert consumed == []
    assert next(stream) == "La PGU "
    assert consumed == ["La PGU "]
    rest = "".join(stream)
    assert "es un beneficio." in rest
    assert source in rest


def test_stream_failure_before_first_fragment_uses_template(monkeypatch):
    monkeypatch.setattr(asistente.config, "BEDROCK_MODEL_ID", "configured")
    monkeypatch.setattr(asistente.time, "sleep", lambda _: None)

    def failed(*args, **kwargs):
        raise RuntimeError("offline")
        yield

    monkeypatch.setattr(chatbot, "answer_general", failed)
    chunks, engine = asistente.responder_publico("¿Qué es la PGU?", [], stream=True)
    assert engine == "plantillas"
    assert "Pensión Garantizada Universal" in "".join(chunks)


def test_midstream_failure_propagates_and_closes_stream():
    class Events:
        closed = False

        def __iter__(self):
            yield {"contentBlockDelta": {"delta": {"text": "Inicio"}}}
            yield {"modelStreamErrorException": {"message": "interrupted"}}

        def close(self):
            self.closed = True

    events = Events()

    class Client:
        def converse_stream(self, *args, **kwargs):
            return {"stream": events}

    chunks = chatbot.answer_general("hola", client=Client(), stream=True)
    assert next(chunks) == "Inicio"
    with pytest.raises(RuntimeError):
        next(chunks)
    assert events.closed
