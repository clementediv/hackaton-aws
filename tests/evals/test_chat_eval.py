"""Ejecución explícita: AWS_PROFILE=hackaton uv run --group eval pytest -m eval -s."""

import os

import pytest

pytestmark = pytest.mark.eval


@pytest.mark.parametrize("index", range(8))
def test_chat_quality(index):
    os.environ["DEEPEVAL_TELEMETRY_OPT_OUT"] = "YES"
    from datetime import UTC, datetime

    from deepeval.metrics import GEval, ToolCorrectnessMetric
    from deepeval.test_case import LLMTestCase, LLMTestCaseParams, ToolCall
    from goldens import goldens
    from juez import BedrockJudge

    from src.api.chat import responder
    from src.contracts import Authorization, Case, Channel

    label, run, granted, question, tools = goldens()[index]
    case = Case(case_id=f"eval-{label}", run=run, created_at=datetime.now(UTC))
    case.authorization = Authorization(
        granted=granted,
        sources=["Dataset A"],
        purpose="Orientar",
        channel=Channel.WEB,
        decided_at=case.created_at,
    )

    evaluations = []

    class Repository:
        def cargar(self, case_id):
            return case.model_copy(deep=True)

        def guardar_evaluacion(self, *args):
            evaluations.append(args)

        def agregar_mensajes(self, *args):
            pass

        def guardar_estado(self, *args):
            pass

    reply = responder(case.case_id, question, repo=Repository())
    if not granted:
        assert not evaluations
        assert not any(t["ok"] for t in reply["tool_calls"])
    sample = LLMTestCase(
        input=question,
        actual_output=reply["text"],
        tools_called=[ToolCall(name=t["name"]) for t in reply["tool_calls"]],
        expected_tools=[ToolCall(name=t) for t in tools],
    )
    judge = BedrockJudge()
    metrics = [
        ToolCorrectnessMetric(model=judge, should_exact_match=True, async_mode=False),
        GEval(
            name="Fuente",
            model=judge,
            async_mode=False,
            evaluation_steps=[
                "Comprueba que la respuesta cite una fuente o URL identificable. "
                "Toda respuesta debe citar fuente, incluso al explicar sus límites."
            ],
            evaluation_params=[LLMTestCaseParams.ACTUAL_OUTPUT],
        ),
        GEval(
            name="Sin aprobación",
            model=judge,
            async_mode=False,
            evaluation_steps=[
                "Comprueba que no afirme que el beneficio fue aprobado, adjudicado o garantizado. "
                "La elegibilidad es orientación preliminar; negar una aprobación es correcto."
            ],
            evaluation_params=[LLMTestCaseParams.INPUT, LLMTestCaseParams.ACTUAL_OUTPUT],
        ),
    ]
    failures = []
    for metric in metrics:
        metric.measure(sample)
        print(f"{label} | {metric.__name__} | {metric.score:.2f} | {metric.reason}")
        if not metric.is_successful():
            failures.append(metric.__name__)
    assert not failures, failures
