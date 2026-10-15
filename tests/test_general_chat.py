import json

import pytest

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


@pytest.mark.parametrize(
    "question",
    [
        "puedo tener yo la pgu?",
        "¿Puedo recibir la PGU?",
        "¿Tengo derecho a la PGU?",
        "¿Podría solicitarla?",
        "¿Me corresponde?",
        "¿Califico para este beneficio?",
    ],
)
def test_personal_eligibility_requires_consent_with_concrete_next_step(monkeypatch, question):
    monkeypatch.setattr(config, "BEDROCK_MODEL_ID", "us.anthropic.claude-sonnet-5")

    def forbidden(*args, **kwargs):
        pytest.fail("No evaluar ni enviar datos personales sin permiso")

    monkeypatch.setattr(chatbot, "answer_general", forbidden)
    context = {"autorizado": False, "nombre": "Raúl", "hitos": {}}
    text, engine = asistente.responder(question, context, [])
    assert "autorices" in text
    assert "Activar Mi Gobierno" in text
    assert "Aún no puedo confirmar" in text
    assert "¿Qué parte te gustaría entender?" not in text
    assert engine == "plantillas"


def test_authorized_personal_question_reaches_agent_with_calculated_context(monkeypatch):
    monkeypatch.setattr(config, "BEDROCK_MODEL_ID", "us.anthropic.claude-sonnet-5")
    context = {"autorizado": True, "pgu": {"resultado_orientativo": "elegible"}}

    def agent(question, ctx, history):
        assert question == "puedo tener yo la pgu?"
        assert ctx is context
        return (
            "Según tu evaluación preliminar, podrías solicitarla. La decisión corresponde al IPS."
        )

    monkeypatch.setattr(asistente, "_bedrock", agent)
    text, engine = asistente.responder("puedo tener yo la pgu?", context, [])
    assert "podrías solicitarla" in text
    assert engine == "bedrock"


def test_general_followup_is_not_limited_to_fixed_keywords(monkeypatch):
    monkeypatch.setattr(config, "BEDROCK_MODEL_ID", "us.anthropic.claude-sonnet-5")
    monkeypatch.setattr(chatbot, "answer_general", lambda q: "Explicación pertinente")
    text, engine = asistente.responder(
        "No entiendo la diferencia con una pensión", {"autorizado": False, "hitos": {}}, []
    )
    assert engine == "bedrock"
    assert text == "Explicación pertinente"


@pytest.mark.parametrize("question", [
    "Hola", "¿Quién eres?", "¿Qué puedes hacer?", "¿Cómo me puedes ayudar?",
    "¿Eres una IA?", "¿Me puedes ayudar con trámites?",
])
def test_public_assistant_explains_identity_and_actual_capabilities(monkeypatch, question):
    monkeypatch.setattr(config, "BEDROCK_MODEL_ID", "")
    reply, engine = asistente.responder_publico(question, [])
    assert engine == "plantillas"
    if question == "Hola":
        assert reply == "¡Hola! Te ayudo con trámites y beneficios. ¿Qué necesitas?"
        return
    assert reply == (
        "Soy el asistente de IA de ChileAtiende. "
        "Te ayudo con trámites, beneficios y los documentos que necesitas."
    )


def test_bedrock_receives_assistant_identity_and_benefit_limits():
    class Client:
        def converse(self, messages, **options):
            instructions = options["system"][1]["text"]
            assert "asistente de inteligencia artificial de ChileAtiende" in instructions
            assert "solo la evaluación personalizada de PGU" in instructions
            assert "Mi Gobierno y autorizar antecedentes" in instructions
            return {"output": {"message": {"content": [{"text": "Soy el asistente de IA."}]}}}

    assert "asistente de IA" in chatbot.answer_general("¿Quién eres?", client=Client())
