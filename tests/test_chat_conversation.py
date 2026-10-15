import pytest

from src.app.ruta import asistente, config
from src.app.ruta.conversation import BOUNDARY_REPLY, ConversationalClient


@pytest.mark.parametrize("question", ["eres un idiota", "no sirves", "asdfghjkl", "???"])
def test_boundary_reply_is_standard_across_turns_without_fake_diagnosis(monkeypatch, question):
    monkeypatch.setattr(config, "BEDROCK_MODEL_ID", "")
    ctx = {"autorizado": False, "hitos": {}}
    first, _ = asistente.responder(question, ctx, [])
    history = [{"rol": "user", "texto": question}, {"rol": "assistant", "texto": first}]
    second, _ = asistente.responder(question, ctx, history)
    assert first == second == BOUNDARY_REPLY
    assert "fecha de nacimiento" not in first + second
    assert "necesito que autorices" not in first + second


def test_frustration_does_not_hide_a_real_question(monkeypatch):
    monkeypatch.setattr(config, "BEDROCK_MODEL_ID", "")
    reply, _ = asistente.responder("Qué mierda es la PGU?", {"autorizado": False, "hitos": {}}, [])
    assert "Pensión Garantizada Universal" in reply
    assert "qué estuvo mal" not in reply


def test_conversational_wrapper_preserves_trusted_context_and_tool_config():
    class Client:
        def converse(self, messages, **options):
            assert options["system"][0] == {"text": "consentimiento obligatorio"}
            assert "No repitas" in options["system"][-1]["text"]
            assert options["toolConfig"] == {"tools": ["leer_caso"]}
            return {"ok": True}

    system = [{"text": "consentimiento obligatorio"}]
    assert ConversationalClient(Client()).converse(
        [], system=system, toolConfig={"tools": ["leer_caso"]}
    ) == {"ok": True}
    assert len(system) == 1


def test_general_history_is_explicit_and_separate_from_revoked_personal_chat(monkeypatch):
    from src.app.ruta import chatbot

    monkeypatch.setattr(config, "BEDROCK_MODEL_ID", "us.anthropic.claude-sonnet-5")
    public = [
        {"rol": "user", "texto": "¿Qué es PGU?"},
        {"rol": "assistant", "texto": "Un beneficio del Estado."},
    ]

    def general(question, *, public_history):
        assert public_history is public
        assert "DATO_PRIVADO" not in str(public_history)
        return "Seguimos con la explicación general."

    monkeypatch.setattr(chatbot, "answer_general", general)
    result, engine = asistente.responder(
        "No entiendo esa sigla",
        {"autorizado": False},
        [{"rol": "assistant", "texto": "DATO_PRIVADO"}],
        public_history=public,
    )
    assert engine == "bedrock"
    assert "Seguimos" in result


@pytest.mark.parametrize(
    "question",
    ["eres un idiota", "asdfghjkl", "???", "Cuéntame un chiste", "¿Quién ganará el mundial?"],
)
@pytest.mark.parametrize("authorized", [False, True])
def test_boundary_is_identical_in_both_chats_without_invoking_bedrock(
    monkeypatch, question, authorized
):
    from src.app.ruta import chatbot

    monkeypatch.setattr(config, "BEDROCK_MODEL_ID", "us.anthropic.claude-sonnet-5")

    def forbidden(*args, **kwargs):
        pytest.fail("El cortafuegos estándar no debe depender del modelo ni consultar datos")

    monkeypatch.setattr(chatbot, "answer_general", forbidden)
    monkeypatch.setattr(asistente, "_bedrock", forbidden)
    context = {"autorizado": authorized}
    assert asistente.responder(question, context, [])[0] == BOUNDARY_REPLY
    assert asistente.responder_publico(question, [])[0] == BOUNDARY_REPLY


def test_frustration_about_the_real_task_does_not_trigger_boundary(monkeypatch):
    monkeypatch.setattr(config, "BEDROCK_MODEL_ID", "")
    text, _ = asistente.responder(
        "No entiendo qué es la PGU", {"autorizado": False, "hitos": {}}, []
    )
    assert text != BOUNDARY_REPLY
    assert "Pensión Garantizada Universal" in text
