"""Humo T19: turno real, spans Converse anidados y colector Phoenix local.

AWS_PROFILE=hackaton PHOENIX_COLLECTOR_ENDPOINT=http://localhost:6006 \
uv run --group api python scripts/verificar_chat_tracing.py
"""

from datetime import UTC, datetime

from opentelemetry.sdk.trace.export import SimpleSpanProcessor
from opentelemetry.sdk.trace.export.in_memory_span_exporter import InMemorySpanExporter

from src.api.chat import responder
from src.api.tracing import flush, setup_tracing
from src.contracts import Authorization, Case, Channel


class MemoryRepository:
    def __init__(self):
        self.case = Case(
            case_id="phoenix-verification", run="100000001-5", created_at=datetime.now(UTC)
        )
        self.case.authorization = Authorization(
            granted=True,
            sources=["Dataset A sintético"],
            purpose="Orientación",
            channel=Channel.WEB,
            decided_at=self.case.created_at,
        )

    def cargar(self, case_id):
        return self.case.model_copy(deep=True)

    def guardar_evaluacion(self, *args):
        pass

    def agregar_mensajes(self, *args):
        pass

    def guardar_estado(self, case):
        self.case = case


def main():
    provider = setup_tracing()
    assert provider is not None, "Falta PHOENIX_COLLECTOR_ENDPOINT"
    exporter = InMemorySpanExporter()
    provider.add_span_processor(SimpleSpanProcessor(exporter))
    repo = MemoryRepository()
    reply = responder(
        repo.case.case_id,
        "Consulta leer_caso y explícame mi orientación PGU. Cita tu fuente.",
        repo=repo,
    )
    flush()
    spans = exporter.get_finished_spans()
    assert any(s.name == "bedrock.converse" and s.parent for s in spans)
    assert any(s.name == "chat.turn" for s in spans)
    print("Herramientas:", reply["tool_calls"])
    print("Spans:", [(s.name, bool(s.parent)) for s in spans])
    print("Trace ID:", format(spans[-1].context.trace_id, "032x"))


if __name__ == "__main__":
    main()
