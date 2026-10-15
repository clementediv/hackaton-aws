"""Stack aislado del chatbot: API key, throttling y bundle Linux."""

import shutil
import subprocess
from pathlib import Path

from aws_cdk import ArnFormat, CfnOutput, Duration, RemovalPolicy, Stack
from aws_cdk import aws_apigatewayv2 as apigw
from aws_cdk import aws_apigatewayv2_authorizers as authorizers
from aws_cdk import aws_apigatewayv2_integrations as integrations
from aws_cdk import aws_dynamodb as ddb
from aws_cdk import aws_iam as iam
from aws_cdk import aws_lambda as lambda_
from aws_cdk import aws_logs as logs
from aws_cdk import aws_secretsmanager as secrets
from constructs import Construct

ROOT = Path(__file__).resolve().parents[1]
BUILD = ROOT / "infra/build/chat"


def lambda_asset():
    shutil.rmtree(BUILD, ignore_errors=True)
    BUILD.mkdir(parents=True)
    subprocess.run(
        [
            "uv",
            "export",
            "--frozen",
            "--no-dev",
            "--group",
            "api",
            "--no-emit-project",
            "--format",
            "requirements-txt",
            "--output-file",
            str(BUILD.parent / "chat-requirements.txt"),
        ],
        cwd=ROOT,
        check=True,
        capture_output=True,
    )
    subprocess.run(
        [
            "uv",
            "pip",
            "install",
            "--target",
            str(BUILD),
            "--python-platform",
            "x86_64-manylinux2014",
            "--python-version",
            "3.12",
            "--only-binary",
            ":all:",
            "-r",
            str(BUILD.parent / "chat-requirements.txt"),
        ],
        cwd=ROOT,
        check=True,
        capture_output=True,
    )
    native = list((BUILD / "pydantic_core").glob("*cpython-312*x86_64*linux*.so"))
    if not native or any("darwin" in p.name or p.suffix == ".dylib" for p in BUILD.rglob("*")):
        raise RuntimeError("Bundle no compatible con Lambda Linux x86_64")
    (BUILD / "src").mkdir()
    shutil.copy2(ROOT / "src/__init__.py", BUILD / "src/__init__.py")
    for package in ("api", "agent", "contracts", "tools", "cases"):
        shutil.copytree(
            ROOT / "src" / package,
            BUILD / "src" / package,
            ignore=shutil.ignore_patterns("__pycache__"),
        )
    (BUILD / "src/app/ruta").mkdir(parents=True)
    for name in ("__init__.py", "config.py", "reglas.py", "fechas.py"):
        shutil.copy2(ROOT / "src/app/ruta" / name, BUILD / "src/app/ruta" / name)
    shutil.copy2(ROOT / "src/app/__init__.py", BUILD / "src/app/__init__.py")
    shutil.copytree(
        ROOT / "data/raw/dataset_A_participantes", BUILD / "data/raw/dataset_A_participantes"
    )
    dataset = (BUILD / "src/tools/profiles.py").resolve().parents[2] / (
        "data/raw/dataset_A_participantes/perfiles.json"
    )
    if not dataset.is_file():
        raise RuntimeError("Dataset fuera del layout esperado")
    return lambda_.Code.from_asset(str(BUILD))


class ChatStack(Stack):
    def __init__(self, scope: Construct, construct_id: str, **kwargs):
        super().__init__(scope, construct_id, **kwargs)
        table = ddb.Table(
            self,
            "Casos",
            table_name="ca-casos",
            partition_key=ddb.Attribute(name="pk", type=ddb.AttributeType.STRING),
            sort_key=ddb.Attribute(name="sk", type=ddb.AttributeType.STRING),
            billing_mode=ddb.BillingMode.PAY_PER_REQUEST,
            removal_policy=RemovalPolicy.DESTROY,
        )
        table.add_global_secondary_index(
            index_name="por-run",
            partition_key=ddb.Attribute(name="run", type=ddb.AttributeType.STRING),
            sort_key=ddb.Attribute(name="created_at", type=ddb.AttributeType.STRING),
        )
        key = secrets.Secret(
            self,
            "ApiKey",
            secret_name="ca-chat-api-key",
            generate_secret_string=secrets.SecretStringGenerator(
                password_length=40, exclude_punctuation=True
            ),
        )
        key.apply_removal_policy(RemovalPolicy.DESTROY)
        role_arn = self.node.try_get_context("lambda_role_arn")
        role = iam.Role.from_role_arn(self, "RolExistente", role_arn) if role_arn else None
        code = lambda_asset()
        phoenix = secrets.Secret(self, "PhoenixKey", secret_name="ca-chat-phoenix-key")
        phoenix.apply_removal_policy(RemovalPolicy.DESTROY)
        fn = lambda_.Function(
            self,
            "Chat",
            function_name="ca-chat",
            runtime=lambda_.Runtime.PYTHON_3_12,
            architecture=lambda_.Architecture.X86_64,
            handler="src.api.handler.on_http",
            code=code,
            role=role,
            timeout=Duration.seconds(28),
            memory_size=512,
            environment={
                "API_KEY_SECRET_ARN": key.secret_arn,
                "TABLA_CASOS": table.table_name,
                "BEDROCK_MODEL_ID": "us.anthropic.claude-sonnet-5",
                "DATA_DIR": "/var/task/data/raw/dataset_A_participantes",
                "FECHA_REFERENCIA": "2026-10-08",
                "PHOENIX_COLLECTOR_ENDPOINT": self.node.try_get_context("phoenix_endpoint") or "",
                "PHOENIX_API_KEY_SECRET_ARN": phoenix.secret_arn,
            },
            log_group=logs.LogGroup(
                self,
                "Logs",
                log_group_name="/aws/lambda/ca-chat",
                retention=logs.RetentionDays.ONE_WEEK,
                removal_policy=RemovalPolicy.DESTROY,
            ),
        )
        key.grant_read(fn)
        phoenix.grant_read(fn)
        table.grant_read_write_data(fn)
        fn.add_to_role_policy(
            iam.PolicyStatement(
                actions=["bedrock:InvokeModel"],
                resources=[
                    self.format_arn(
                        service="bedrock",
                        resource="inference-profile",
                        resource_name="us.anthropic.claude-sonnet-5",
                        arn_format=ArnFormat.SLASH_RESOURCE_NAME,
                    ),
                    *[
                        self.format_arn(
                            service="bedrock",
                            region=region,
                            account="",
                            resource="foundation-model",
                            resource_name="anthropic.claude-sonnet-5",
                            arn_format=ArnFormat.SLASH_RESOURCE_NAME,
                        )
                        for region in ("us-east-1", "us-east-2", "us-west-2")
                    ],
                ],
            )
        )
        auth_fn = lambda_.Function(
            self,
            "Authorizer",
            function_name="ca-chat-auth",
            runtime=lambda_.Runtime.PYTHON_3_12,
            handler="src.api.handler.authorize",
            code=code,
            environment={"API_KEY_SECRET_ARN": key.secret_arn},
            role=role,
            timeout=Duration.seconds(10),
            log_group=logs.LogGroup(
                self,
                "AuthLogs",
                log_group_name="/aws/lambda/ca-chat-auth",
                retention=logs.RetentionDays.ONE_WEEK,
                removal_policy=RemovalPolicy.DESTROY,
            ),
        )
        key.grant_read(auth_fn)
        api = apigw.HttpApi(
            self,
            "Api",
            api_name="ca-chat",
            default_authorizer=authorizers.HttpLambdaAuthorizer(
                "ApiKeyAuthorizer",
                auth_fn,
                response_types=[authorizers.HttpLambdaResponseType.SIMPLE],
                identity_source=["$request.header.x-api-key"],
                results_cache_ttl=Duration.seconds(0),
            ),
            default_integration=integrations.HttpLambdaIntegration("ChatIntegration", fn),
        )
        stage = api.default_stage.node.default_child
        stage.default_route_settings = apigw.CfnStage.RouteSettingsProperty(
            throttling_rate_limit=2, throttling_burst_limit=4
        )
        CfnOutput(self, "Url", value=api.api_endpoint)
        CfnOutput(self, "ApiKeySecret", value=key.secret_name)
