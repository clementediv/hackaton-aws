"""Use the shared tool-use agent with the Streamlit route as trusted context."""

from datetime import UTC, datetime

from src.agent.bedrock import BedrockClient
from src.agent.loop import Agent
from src.agent.tools import ToolRegistry
from src.contracts import Authorization, Case, Channel, Message, MessageRole

from . import config


def answer(question: str, context: dict, history: list[dict], *, client=None) -> str:
    if not context.get("autorizado"):
        raise PermissionError("El chatbot requiere autorización antes de leer tu ruta.")
    now = datetime.now(UTC)
    case = Case(
        case_id=f"streamlit-{context['run']}",
        run=context["run"],
        created_at=now,
        authorization=Authorization(
            granted=True,
            sources=["Dataset A sintético"],
            purpose="Orientación y seguimiento del trámite autorizado en la app",
            channel=Channel.WEB,
            decided_at=now,
        ),
    )
    for message in history[-6:]:
        case.messages.append(
            Message(
                role=(MessageRole.AGENT if message["rol"] == "assistant" else MessageRole.PERSON),
                channel=Channel.WEB,
                text=message["texto"],
                created_at=now,
            )
        )
    registry = ToolRegistry()
    registry.register(
        "leer_caso",
        lambda trusted, args: {
            "case_id": trusted.case.case_id,
            "context": context,
            "source": "Ruta determinista del MVP sobre dataset A sintético",
            "fuente_url": config.FUENTE_PGU,
            "sources_verified": False,
        },
    )
    agent = Agent(
        client=client or BedrockClient.from_env(),
        tools=registry,
        reference_date=config.FECHA_REFERENCIA,
    )
    return agent.run_turn(case, question).text


def answer_general(question: str, *, client=None) -> str:
    """Public guidance: only current question and public facts go to Bedrock.

    No Case, RUN, profile tools, context or previous conversation is supplied.
    Personalized requests still go through answer() and its consent guard.
    """
    from src.agent.prompts import SYSTEM_PROMPT

    public_context = (
        "Modo de información general, sin acceso a antecedentes personales ni herramientas. "
        "Responde directamente a la pregunta en español sencillo y breve. "
        "No saludes de nuevo en cada respuesta ni repitas una invitación. "
        "No evalúes elegibilidad, montos ni fechas personales; explica que eso requiere "
        "autorizar antecedentes cuando la persona pida revisar su caso. "
        "Hechos públicos: PGU significa Pensión Garantizada Universal; es un beneficio "
        "económico mensual del Estado para personas de 65 años o más que cumplen "
        "los requisitos; el IPS revisa su cumplimiento. "
        "La AFP administra ahorros previsionales. SCOMP permite consultar y comparar "
        "ofertas de montos de pensión. El RSH reúne información de los hogares. "
        f"Cita la fuente pertinente: PGU {config.FUENTE_PGU}; "
        f"pensiones {config.FUENTES['spensiones']}; RSH {config.FUENTES['rsh']}. "
        "No inventes requisitos, montos, trámites iniciados ni decisiones institucionales."
    )
    result = (client if client is not None else BedrockClient.from_env()).converse(
        [{"role": "user", "content": [{"text": question}]}],
        system=[{"text": SYSTEM_PROMPT}, {"text": public_context}],
        inferenceConfig={"maxTokens": 600},
    )
    text = "\n".join(
        c["text"] for c in result["output"]["message"]["content"] if "text" in c
    ).strip()
    if not text:
        raise ValueError("Bedrock devolvió una respuesta vacía")
    if "https://" not in text:
        text += f"\n\nFuente: {config.FUENTE_PGU}"
    return text
