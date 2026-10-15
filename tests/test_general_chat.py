import json

from src.app.ruta import asistente, chatbot, config


def test_public_bedrock_has_no_profile_or_previous_history():
    class Client:
        def converse(self, messages, **options):
            request = json.dumps({"messages": messages, **options})
            assert "toolConfig" not in options
            assert "100000010-4" not in request
            assert "ANTECEDENTE_PRIVADO" not in request
            assert messages == [{"role": "user", "content": [{"text": "¿Qué es la PGU?"}]}]
            return {
                "output": {"message": {"content": [{"text": "Es un aporte mensual del Estado."}]}}
            }

    text = chatbot.answer_general("¿Qué es la PGU?", client=Client())
    assert config.FUENTE_PGU in text


def test_public_question_uses_bedrock_without_passing_context(monkeypatch):
    monkeypatch.setattr(config, "BEDROCK_MODEL_ID", "us.anthropic.claude-sonnet-5")
    received = []

    def public(question):
        received.append(question)
        return "Explicación general de PGU con fuente"

    monkeypatch.setattr(chatbot, "answer_general", public)
    context = {"autorizado": False, "nombre": "Raúl", "run": "100000010-4", "hitos": {}}
    reply, engine = asistente.responder(
        "¿Qué es la PGU?", context, [{"rol": "assistant", "texto": "ANTECEDENTE_PRIVADO"}]
    )
    assert engine == "bedrock"
    assert received == ["¿Qué es la PGU?"]
    assert reply == "Explicación general de PGU con fuente"


def test_public_bedrock_failure_keeps_relevant_explanation(monkeypatch):
    monkeypatch.setattr(config, "BEDROCK_MODEL_ID", "us.anthropic.claude-sonnet-5")

    def fail(question):
        raise RuntimeError("private internal error")

    monkeypatch.setattr(chatbot, "answer_general", fail)
    reply, engine = asistente.responder("¿Qué es la PGU?", {"autorizado": False, "hitos": {}}, [])
    assert "Pensión Garantizada Universal" in reply
    assert "fecha de nacimiento" not in reply
    assert "private internal error" not in reply
    assert engine == "plantillas"


def test_separate_public_chat_preserves_public_history_and_uses_shared_client(monkeypatch):
    monkeypatch.setattr(config, "BEDROCK_MODEL_ID", "us.anthropic.claude-sonnet-5")
    history = [
        {"rol": "assistant", "texto": "Hola, ¿en qué te ayudo?"},
        {"rol": "user", "texto": "¿Qué es la PGU?"},
        {"rol": "assistant", "texto": "Es un beneficio del Estado."},
    ]

    class Client:
        def converse(self, messages, **options):
            assert messages[0]["role"] == "user"
            assert "¿Qué es la PGU?" in json.dumps(messages, ensure_ascii=False)
            assert "temperature" not in options["inferenceConfig"]
            assert "toolConfig" not in options
            return {"output": {"message": {"content": [{"text": "El IPS revisa los requisitos."}]}}}

    monkeypatch.setattr(chatbot.BedrockClient, "from_env", lambda: Client())
    text, engine = asistente.responder_publico("¿Quién lo revisa?", history)
    assert engine == "bedrock"
    assert "IPS" in text
