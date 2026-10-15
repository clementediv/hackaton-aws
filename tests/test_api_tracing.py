from src.api import handler, tracing


def test_inert_without_endpoint(monkeypatch):
    monkeypatch.delenv("PHOENIX_COLLECTOR_ENDPOINT", raising=False)
    monkeypatch.setattr(tracing, "_provider", None)
    assert tracing.setup_tracing() is None
    with tracing.span("test") as current:
        assert current is None


def test_idempotent_and_flush_failure(monkeypatch):
    class Provider:
        def force_flush(self, **kwargs):
            raise RuntimeError("export unavailable")

    provider = Provider()
    monkeypatch.setattr(tracing, "_provider", provider)
    assert tracing.setup_tracing() is provider
    assert tracing.setup_tracing() is provider
    # A failed exporter cannot replace even the unauthorized response.
    assert handler.on_http({"headers": {}}, None)["statusCode"] == 401


def test_instrumentation_captures_sonnet_converse(monkeypatch):
    import boto3
    import pytest
    from botocore.stub import Stubber

    bedrock = pytest.importorskip("openinference.instrumentation.bedrock")
    sdk = pytest.importorskip("opentelemetry.sdk.trace")
    from opentelemetry.sdk.trace.export import SimpleSpanProcessor
    from opentelemetry.sdk.trace.export.in_memory_span_exporter import InMemorySpanExporter

    monkeypatch.delenv("AWS_PROFILE", raising=False)
    provider = sdk.TracerProvider()
    exporter = InMemorySpanExporter()
    provider.add_span_processor(SimpleSpanProcessor(exporter))
    instrumentor = bedrock.BedrockInstrumentor()
    instrumentor.instrument(tracer_provider=provider)
    try:
        client = boto3.client(
            "bedrock-runtime",
            region_name="us-east-1",
            aws_access_key_id="testing",
            aws_secret_access_key="testing",
        )
        with Stubber(client) as stub:
            stub.add_response(
                "converse",
                {
                    "output": {"message": {"role": "assistant", "content": [{"text": "OK"}]}},
                    "stopReason": "end_turn",
                    "usage": {"inputTokens": 1, "outputTokens": 1, "totalTokens": 2},
                    "metrics": {"latencyMs": 1},
                },
            )
            client.converse(
                modelId="us.anthropic.claude-sonnet-5",
                messages=[{"role": "user", "content": [{"text": "OK"}]}],
            )
        assert any(s.name == "bedrock.converse" for s in exporter.get_finished_spans())
    finally:
        instrumentor.uninstrument()
        provider.shutdown()
