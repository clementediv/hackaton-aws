import json

from test_cases_repo import repo as cases_repo  # noqa: F401

from src.agent.loop import LIMIT_REPLY
from src.api.chat import responder
from src.contracts import Authorization, Channel


class ScriptedClient:
    def __init__(self, responses):
        self.responses = responses
        self.requests = []

    def converse(self, messages, **options):
        self.requests.append(json.loads(json.dumps(messages)))
        return self.responses.pop(0)


def answer(text):
    return {
        "stopReason": "end_turn",
        "output": {"message": {"role": "assistant", "content": [{"text": text}]}},
    }


def tool():
    return {
        "stopReason": "tool_use",
        "output": {
            "message": {
                "role": "assistant",
                "content": [{"toolUse": {"toolUseId": "read", "name": "leer_caso", "input": {}}}],
            }
        },
    }


def test_two_turns_persist_and_evaluate(cases_repo):
    repo = cases_repo
    case = repo.crear("100000001-5")
    case.authorization = Authorization(
        granted=True,
        sources=["Dataset A"],
        purpose="Orientar",
        channel=Channel.WEB,
        decided_at=case.created_at,
    )
    repo.guardar_estado(case)
    first = ScriptedClient([tool(), answer("Fuente: ChileAtiende. Orientación preliminar.")])
    responder(case.case_id, "Me llamo Rosa", client=first, repo=repo)
    second = ScriptedClient([answer("Rosa, seguimos.")])
    responder(case.case_id, "¿Recuerdas mi nombre?", client=second, repo=repo)
    assert "Rosa" in json.dumps(second.requests[0])
    assert len(repo.cargar(case.case_id).messages) == 4
    assert repo.cargar_evaluacion(case.case_id)["sources_verified"] is False


def test_no_permission_returns_tool_error(cases_repo):
    repo = cases_repo
    case = repo.crear("100000001-5")
    client = ScriptedClient([tool(), answer("Necesito tu autorización.")])
    responder(case.case_id, "Evalúame", client=client, repo=repo)
    assert "permission_denied" in json.dumps(client.requests[1])
    assert repo.cargar_evaluacion(case.case_id) is None


def test_limit_still_persists(cases_repo):
    repo = cases_repo
    case = repo.crear("100000001-5")
    client = ScriptedClient([tool() for _ in range(6)])
    reply = responder(case.case_id, "Ayuda", client=client, repo=repo)
    assert reply["hit_iteration_limit"]
    assert repo.cargar(case.case_id).messages[-1].text == LIMIT_REPLY
    assert len(repo.cargar(case.case_id).messages) == 2
