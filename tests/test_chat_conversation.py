import pytest

from src.app.ruta import asistente, config
from src.app.ruta.conversation import ABUSE_REPLY, BOUNDARY_REPLY, ConversationalClient


@pytest.mark.parametrize("question", ["eres un idiota", "no sirves", "asdfghjkl", "???"])
def test_boundary_reply_is_standard_across_turns_without_fake_diagnosis(monkeypatch, question):
    monkeypatch.setattr(config, "BEDROCK_MODEL_ID", "")
    ctx = {"autorizado": False, "hitos": {}}
    first, _ = asistente.responder(question, ctx, [])
    history = [{"rol": "user", "texto": question}, {"rol": "assistant", "texto": first}]
    second, _ = asistente.responder(question, ctx, history)
    expected = ABUSE_REPLY if question in {"eres un idiota", "no sirves"} else BOUNDARY_REPLY
    assert first == second == expected
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
    expected = ABUSE_REPLY if question == "eres un idiota" else BOUNDARY_REPLY
    assert asistente.responder(question, context, [])[0] == expected
    assert asistente.responder_publico(question, [])[0] == expected


@pytest.mark.parametrize(
    "question",
    ["eres una imerda", "ERES UNA MIERDA!!!", "eres una merda", "eres una basura", "no sirves"],
)
@pytest.mark.parametrize("authorized", [False, True])
@pytest.mark.parametrize("model", ["", "configured-model"])
def test_abuse_never_retrieves_previous_benefit_or_invokes_model(
    monkeypatch, question, authorized, model
):
    from src.app.ruta import chatbot

    monkeypatch.setattr(config, "BEDROCK_MODEL_ID", model)
    monkeypatch.setattr(asistente, "WORD_DELAY_SECONDS", 0)

    def forbidden(*args, **kwargs):
        pytest.fail("Un insulto sin consulta no debe buscar beneficios ni invocar el modelo")

    monkeypatch.setattr(asistente, "grounded_fallback", forbidden)
    monkeypatch.setattr(asistente, "_bedrock", forbidden)
    monkeypatch.setattr(chatbot, "answer_general", forbidden)
    history = [
        {"rol": "user", "texto": "¿Qué es la PGU?"},
        {"rol": "assistant", "texto": "La Pensión Garantizada Universal es un beneficio."},
    ]
    assert asistente.responder(question, {"autorizado": authorized}, history) == (
        ABUSE_REPLY, "plantillas"
    )
    assert asistente.responder_publico(question, history) == (ABUSE_REPLY, "plantillas")
    chunks, engine = asistente.responder_publico(question, history, stream=True)
    assert engine == "plantillas"
    assert "".join(chunks) == ABUSE_REPLY


@pytest.mark.parametrize("question", ["Qué imerda es la PGU?", "Qué mierda es la PGU?"])
def test_abuse_typo_does_not_block_a_real_benefit_question(monkeypatch, question):
    monkeypatch.setattr(config, "BEDROCK_MODEL_ID", "")
    reply, _ = asistente.responder_publico(question, [])
    assert reply not in {ABUSE_REPLY, BOUNDARY_REPLY}
    assert "Pensión Garantizada Universal" in reply


def test_frustration_about_the_real_task_does_not_trigger_boundary(monkeypatch):
    monkeypatch.setattr(config, "BEDROCK_MODEL_ID", "")
    text, _ = asistente.responder(
        "No entiendo qué es la PGU", {"autorizado": False, "hitos": {}}, []
    )
    assert text != BOUNDARY_REPLY
    assert "Pensión Garantizada Universal" in text


@pytest.mark.parametrize(
    "reference",
    [
        "Fuente: ChileAtiende — https://www.chileatiende.gob.cl/",
        "**Fuente:** [Ficha PGU](https://www.chileatiende.gob.cl/fichas/102077)",
        "La PGU es un beneficio. Fuente de orientación del MVP (no verificada): https://www.chileatiende.gob.cl/fichas/102077",
    ],
)
def test_references_are_an_invitation_without_losing_link_or_verification(reference):
    from src.app.ruta.conversation import friendly_sources

    reply = friendly_sources(reference)
    assert "Si quieres saber más, puedes revisar" in reply
    assert "https://www.chileatiende.gob.cl/" in reply
    assert "Fuente:" not in reply and "Fuente de orientación" not in reply
    if "no verificada" in reference:
        assert "no verificada" in reply
    assert friendly_sources(reply) == reply
