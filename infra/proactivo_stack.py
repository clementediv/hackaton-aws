"""DynamoDB + Lambda + SES stack for proactive benefit detection.

Keys and indexes mirror src/proactivo/esquema.py. Fixed resource names keep
the CLI (scripts/proactivo.py) simple; this is a demo stack (DESTROY policy).
"""

import shutil
from pathlib import Path

from aws_cdk import CfnOutput, Duration, RemovalPolicy, Stack
from aws_cdk import aws_dynamodb as ddb
from aws_cdk import aws_events as events
from aws_cdk import aws_events_targets as targets
from aws_cdk import aws_iam as iam
from aws_cdk import aws_lambda as lambda_
from aws_cdk import aws_lambda_event_sources as sources
from aws_cdk import aws_logs as logs
from aws_cdk import aws_ses as ses
from constructs import Construct

ROOT = Path(__file__).resolve().parents[1]
BUILD = Path(__file__).resolve().parent / "build" / "lambda"

NAMES = {
    "personas": "ca-personas",
    "beneficios": "ca-beneficios",
    "contactos": "ca-contactos",
    "historial": "ca-historial",
}


def lambda_asset() -> lambda_.Code:
    """Ship only src/proactivo (boto3 comes with the runtime)."""
    shutil.rmtree(BUILD, ignore_errors=True)
    shutil.copytree(
        ROOT / "src" / "proactivo",
        BUILD / "proactivo",
        ignore=shutil.ignore_patterns("__pycache__", "carga.py"),
    )
    return lambda_.Code.from_asset(str(BUILD))


class ProactivoStack(Stack):
    def __init__(self, scope: Construct, construct_id: str, **kwargs) -> None:
        super().__init__(scope, construct_id, **kwargs)
        email = self.node.try_get_context("email") or "curibeo@utem.cl"
        sender = self.node.try_get_context("remitente") or email
        role_arn = self.node.try_get_context("lambda_role_arn")
        wait_email = str(self.node.try_get_context("espera_email_min") or 5)
        wait_sms = str(self.node.try_get_context("espera_sms_min") or 5)

        def table(key, pk, sk=None, **extra):
            return ddb.Table(
                self,
                key.capitalize(),
                table_name=NAMES[key],
                partition_key=ddb.Attribute(name=pk, type=ddb.AttributeType.STRING),
                sort_key=ddb.Attribute(name=sk, type=ddb.AttributeType.STRING) if sk else None,
                billing_mode=ddb.BillingMode.PAY_PER_REQUEST,
                removal_policy=RemovalPolicy.DESTROY,
                **extra,
            )

        people = table("personas", "run", stream=ddb.StreamViewType.NEW_AND_OLD_IMAGES)
        catalog = table("beneficios", "beneficio_id")
        contacts = table("contactos", "run", "beneficio_id")
        history = table("historial", "run", "sk")
        for name, pk, sk in (
            ("cola-siguiente", "cola", "siguiente_accion_en"),
            ("estado-detectado", "estado", "detectado_en"),
        ):
            contacts.add_global_secondary_index(
                index_name=name,
                partition_key=ddb.Attribute(name=pk, type=ddb.AttributeType.STRING),
                sort_key=ddb.Attribute(name=sk, type=ddb.AttributeType.STRING),
            )

        # Sandbox SES: deploying sends a verification email to this inbox.
        ses.EmailIdentity(self, "Casilla", identity=ses.Identity.email(email))
        if sender != email:
            ses.EmailIdentity(self, "Remitente", identity=ses.Identity.email(sender))

        code = lambda_asset()
        env = {
            "TABLA_PERSONAS": people.table_name,
            "TABLA_BENEFICIOS": catalog.table_name,
            "TABLA_CONTACTOS": contacts.table_name,
            "TABLA_HISTORIAL": history.table_name,
            "REMITENTE": sender,
            "EMAILS_REALES": email,
            "ESPERA_EMAIL_MIN": wait_email,
            "ESPERA_SMS_MIN": wait_sms,
        }
        role = iam.Role.from_role_arn(self, "RolExistente", role_arn) if role_arn else None

        def function(name, handler, timeout=60, extra_env=None):
            fn = lambda_.Function(
                self,
                name,
                function_name=f"ca-{name}",
                runtime=lambda_.Runtime.PYTHON_3_12,
                handler=f"proactivo.handlers.{handler}",
                code=code,
                timeout=Duration.seconds(timeout),
                memory_size=256,
                environment=env | (extra_env or {}),
                role=role,
                log_group=logs.LogGroup(
                    self,
                    f"Logs{name}",
                    log_group_name=f"/aws/lambda/ca-{name}",
                    retention=logs.RetentionDays.ONE_WEEK,
                    removal_policy=RemovalPolicy.DESTROY,
                ),
            )
            if role is None:
                people.grant_read_data(fn)
                catalog.grant_read_data(fn)
                contacts.grant_read_write_data(fn)
                history.grant_read_write_data(fn)
                fn.add_to_role_policy(
                    iam.PolicyStatement(
                        actions=["ses:SendEmail", "ses:SendRawEmail"],
                        resources=[
                            self.format_arn(service="ses", resource="identity", resource_name="*")
                        ],
                    )
                )
            return fn

        responder = function("respuesta", "on_http")
        url = responder.add_function_url(auth_type=lambda_.FunctionUrlAuthType.NONE)
        links = {"URL_RESPUESTA": url.url}

        detector = function("detector", "on_person_change", extra_env=links)
        detector.add_event_source(
            sources.DynamoEventSource(
                people,
                starting_position=lambda_.StartingPosition.LATEST,
                batch_size=25,
                bisect_batch_on_error=True,
                retry_attempts=3,
                report_batch_item_failures=True,
            )
        )

        escalator = function("escalador", "on_escalate", extra_env=links)
        events.Rule(
            self,
            "CadaMinuto",
            schedule=events.Schedule.rate(Duration.minutes(1)),
            targets=[targets.LambdaFunction(escalator)],
        )

        daily = function("revision-diaria", "on_daily", timeout=600, extra_env=links)
        events.Rule(
            self,
            "Diaria",
            # 08:00 in Chile (UTC-3 in October).
            schedule=events.Schedule.cron(minute="0", hour="11"),
            targets=[targets.LambdaFunction(daily)],
        )

        CfnOutput(self, "UrlRespuesta", value=url.url)
        for key, t in (("Personas", people), ("Contactos", contacts), ("Historial", history)):
            CfnOutput(self, f"Tabla{key}", value=t.table_name)
