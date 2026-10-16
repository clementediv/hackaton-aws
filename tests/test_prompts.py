import boto3
import pytest
from botocore.stub import Stubber

from src.agent.bedrock import BedrockClient, BedrockSettings
from src.agent.prompts import SYSTEM_PROMPT, build_tool_config


def test_missing_evaluation_does_not_allow_requirements_from_memory():
    paragraph = SYSTEM_PROMPT.split("Sin una evaluación disponible")[1].split("\n\n")[0]
    assert "no expliques requisitos ni\nmontos de memoria" in paragraph
    assert "perfil, autorización o herramienta" in paragraph
    assert "próximo paso" in paragraph


def test_only_registered_handlers_are_exposed():
    config = build_tool_config(["consultar_perfil", "leer_caso", "consultar_perfil"])
    assert [entry["toolSpec"]["name"] for entry in config["tools"]] == [
        "consultar_perfil",
        "leer_caso",
    ]


@pytest.mark.parametrize("names", [[], ["inventar_beneficio"], ["leer_caso", "unknown"]])
def test_incomplete_or_unknown_registry_fails(names):
    with pytest.raises(ValueError):
        build_tool_config(names)


def test_changing_a_config_does_not_contaminate_later_requests():
    first = build_tool_config(["consultar_perfil"])
    first["tools"][0]["toolSpec"]["inputSchema"]["json"]["properties"]["case"] = {}
    second = build_tool_config(["consultar_perfil"])
    assert set(second["tools"][0]["toolSpec"]["inputSchema"]["json"]["properties"]) == {"run"}


def test_all_specs_can_be_sent_to_converse_without_aws():
    runtime = boto3.Session(
        aws_access_key_id="testing",
        aws_secret_access_key="testing",
        region_name="us-east-1",
    ).client("bedrock-runtime")
    config = build_tool_config(
        [
            "consultar_perfil",
            "evaluar_pgu",
            "calcular_hitos",
            "buscar_beneficios",
            "leer_caso",
            "guardar_caso",
        ]
    )
    response = {
        "output": {"message": {"role": "assistant", "content": [{"text": "Hola"}]}},
        "stopReason": "end_turn",
        "usage": {"inputTokens": 1, "outputTokens": 1, "totalTokens": 2},
        "metrics": {"latencyMs": 1},
    }
    messages = [{"role": "user", "content": [{"text": "Quiero orientación"}]}]
    system = [{"text": SYSTEM_PROMPT}]
    settings = BedrockSettings()
    with Stubber(runtime) as stubber:
        stubber.add_response(
            "converse",
            response,
            {
                "modelId": settings.model_id,
                "messages": messages,
                "system": system,
                "toolConfig": config,
            },
        )
        assert (
            BedrockClient(settings, runtime).converse(messages, system=system, toolConfig=config)
            == response
        )
        stubber.assert_no_pending_responses()
