"""OTLP opcional; los fallos de observabilidad no interrumpen el servicio."""

import os
from contextlib import nullcontext

_provider = None


def setup_tracing():
    global _provider
    if _provider is not None or not os.environ.get("PHOENIX_COLLECTOR_ENDPOINT"):
        return _provider
    try:
        from openinference.instrumentation.bedrock import BedrockInstrumentor
        from opentelemetry import trace
        from opentelemetry.exporter.otlp.proto.http.trace_exporter import OTLPSpanExporter
        from opentelemetry.sdk.resources import Resource
        from opentelemetry.sdk.trace import TracerProvider
        from opentelemetry.sdk.trace.export import BatchSpanProcessor

        endpoint = os.environ["PHOENIX_COLLECTOR_ENDPOINT"].rstrip("/")
        if not endpoint.endswith("/v1/traces"):
            endpoint += "/v1/traces"
        key = os.environ.get("PHOENIX_API_KEY", "")
        if secret := os.environ.get("PHOENIX_API_KEY_SECRET_ARN"):
            import boto3

            key = boto3.client("secretsmanager").get_secret_value(SecretId=secret)["SecretString"]
        provider = TracerProvider(
            resource=Resource.create(
                {
                    "service.name": "ca-chat",
                    "openinference.project.name": os.getenv("PHOENIX_PROJECT", "ca-chat"),
                }
            )
        )
        exporter = OTLPSpanExporter(
            endpoint=endpoint, timeout=2, headers={"authorization": f"Bearer {key}"} if key else {}
        )
        provider.add_span_processor(BatchSpanProcessor(exporter))
        BedrockInstrumentor().instrument(tracer_provider=provider)
        trace.set_tracer_provider(provider)
        _provider = provider
    except Exception:
        return None
    return _provider


def span(name, **attributes):
    provider = setup_tracing()
    if provider is None:
        return nullcontext(None)
    return provider.get_tracer("ca-chat").start_as_current_span(name, attributes=attributes)


def flush():
    try:
        if _provider is not None:
            _provider.force_flush(timeout_millis=2000)
    except Exception:
        pass
