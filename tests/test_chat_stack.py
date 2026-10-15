import importlib.util
from pathlib import Path

import pytest

cdk = pytest.importorskip("aws_cdk")
from aws_cdk import assertions, aws_lambda  # noqa: E402

spec = importlib.util.spec_from_file_location(
    "chat_stack", Path(__file__).resolve().parents[1] / "infra/chat_stack.py"
)
chat_stack = importlib.util.module_from_spec(spec)
spec.loader.exec_module(chat_stack)


def test_chat_stack_security_and_persistence(monkeypatch):
    monkeypatch.setattr(
        chat_stack,
        "lambda_asset",
        lambda: aws_lambda.Code.from_inline("def on_http(event, context): return {}"),
    )
    stack = chat_stack.ChatStack(cdk.App(), "TestChat", env=cdk.Environment(region="us-east-1"))
    template = assertions.Template.from_stack(stack)
    template.has_resource_properties(
        "AWS::DynamoDB::Table",
        {
            "TableName": "ca-casos",
            "BillingMode": "PAY_PER_REQUEST",
            "GlobalSecondaryIndexes": assertions.Match.array_with(
                [assertions.Match.object_like({"IndexName": "por-run"})]
            ),
        },
    )
    template.has_resource_properties(
        "AWS::Lambda::Function",
        {
            "FunctionName": "ca-chat",
            "Environment": {
                "Variables": assertions.Match.object_like(
                    {
                        "DATA_DIR": "/var/task/data/raw/dataset_A_participantes",
                        "FECHA_REFERENCIA": "2026-10-08",
                        "TABLA_CASOS": assertions.Match.any_value(),
                        "BEDROCK_MODEL_ID": "us.anthropic.claude-sonnet-5",
                        "PHOENIX_COLLECTOR_ENDPOINT": "",
                        "PHOENIX_API_KEY_SECRET_ARN": assertions.Match.any_value(),
                    }
                )
            },
        },
    )
    template.has_resource_properties(
        "AWS::ApiGatewayV2::Stage",
        {"DefaultRouteSettings": {"ThrottlingRateLimit": 2, "ThrottlingBurstLimit": 4}},
    )
    routes = template.find_resources("AWS::ApiGatewayV2::Route")
    assert routes and all(r["Properties"]["AuthorizationType"] == "CUSTOM" for r in routes.values())
