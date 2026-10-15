"""Turnos con memoria DynamoDB y evaluación determinista autorizada."""

from dataclasses import asdict

from src.agent.bedrock import BedrockClient
from src.agent.loop import Agent
from src.agent.tools import ToolRegistry
from src.api.evaluacion import config, evaluar
from src.cases.repositorio import CaseRepository
from src.contracts import Channel


def responder(case_id, texto, canal=Channel.WEB, *, client=None, repo=None):
    repo = repo if repo is not None else CaseRepository()
    case = repo.cargar(case_id)
    registry = ToolRegistry()

    def read_case(ctx, args):
        if not ctx.case.can_read_profile:
            raise PermissionError("No hay autorización vigente para consultar la evaluación.")
        evaluation = evaluar(ctx.case)
        repo.guardar_evaluacion(case_id, evaluation)
        return {"case_id": case_id, "evaluation": evaluation}

    registry.register("leer_caso", read_case)
    count = len(case.messages)
    agent = Agent(
        client=client if client is not None else BedrockClient.from_env(),
        tools=registry,
        reference_date=config.FECHA_REFERENCIA,
    )
    reply = agent.run_turn(case, texto, channel=Channel(canal))
    repo.agregar_mensajes(case_id, case.messages[count:])
    repo.guardar_estado(case)
    return asdict(reply)
