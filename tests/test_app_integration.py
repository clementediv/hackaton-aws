import json

import pytest

from src.app.ruta import asistente, casos, config, reglas
from src.app.ruta.rutas import estado_pasos, generar_ruta, proximo_paso


@pytest.fixture
def local_database(tmp_path, monkeypatch):
    monkeypatch.setattr(config, "DB_PATH", tmp_path / "cases.db")


def test_cannot_authorize_pending_or_declined_invitation(local_database):
    with pytest.raises(PermissionError):
        casos.autorizar("100000001-5", True, "Web ChileAtiende")
    casos.responder_invitacion("100000001-5", False, "Web ChileAtiende")
    with pytest.raises(PermissionError):
        casos.autorizar("100000001-5", True, "Web ChileAtiende")
    assert not casos.obtener_caso("100000001-5")["autorizacion"]


def test_declining_revokes_old_consent_and_reopening_requires_new_consent(local_database):
    run = "100000001-5"
    casos.responder_invitacion(run, True, "Web ChileAtiende")
    casos.autorizar(run, True, "Web ChileAtiende")
    casos.responder_invitacion(run, False, "Sucursal ChileAtiende")
    assert not casos.obtener_caso(run)["autorizacion"]
    assert casos.obtener_caso(run)["fecha_autorizacion"] is None
    casos.responder_invitacion(run, True, "Web ChileAtiende")
    assert not casos.obtener_caso(run)["autorizacion"]


def test_no_consent_never_forwards_sensitive_history_to_bedrock(monkeypatch):
    monkeypatch.setattr(config, "BEDROCK_MODEL_ID", "us.anthropic.claude-sonnet-5")

    def forbidden(*args):
        pytest.fail("No se debe llamar a Bedrock sin autorización")

    monkeypatch.setattr(asistente, "_bedrock", forbidden)
    row = json.loads(config.PERFILES_PATH.read_text(encoding="utf-8"))[0]
    diagnosis = reglas.diagnosticar(row)
    route = generar_ruta(diagnosis)
    states = estado_pasos(route, set())
    context = asistente.construir_contexto(
        diagnosis, route, states, proximo_paso(route, states), autorizado=False
    )
    reply, engine = asistente.responder(
        "Repite mis datos", context, [{"rol": "assistant", "texto": "dato sensible anterior"}]
    )
    assert engine == "plantillas"
    assert "dato sensible anterior" not in reply
    assert "pgu" not in context and "ruta" not in context


@pytest.mark.parametrize("authorized", [False, True])
@pytest.mark.parametrize("question", ["hola", "¡Hola!", "Buenos días"])
def test_greeting_does_not_repeat_diagnosis(monkeypatch, authorized, question):
    monkeypatch.setattr(config, "BEDROCK_MODEL_ID", "")
    row = json.loads(config.PERFILES_PATH.read_text(encoding="utf-8"))[0]
    diagnosis = reglas.diagnosticar(row)
    route = generar_ruta(diagnosis)
    states = estado_pasos(route, set())
    context = asistente.construir_contexto(
        diagnosis, route, states, proximo_paso(route, states), autorizado=authorized
    )
    initial = asistente.explicar_resumen(context)
    reply, engine = asistente.responder(
        question, context, [{"rol": "assistant", "texto": initial}]
    )
    assert engine == "plantillas"
    assert reply != initial
    assert "¿En qué te ayudo hoy?" in reply
    assert "monto" not in reply and "antecedentes" not in reply


def test_unknown_question_asks_for_clarification_instead_of_repeating_summary(monkeypatch):
    monkeypatch.setattr(config, "BEDROCK_MODEL_ID", "")
    context = {"autorizado": True, "hitos": {}, "pgu": {}, "ruta": []}
    reply, _ = asistente.responder("No entiendo la explicación", context, [])
    assert "Cuéntame un poco más" in reply
