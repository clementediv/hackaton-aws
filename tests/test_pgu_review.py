import pytest

from src.app.ruta import reglas
from src.app.ruta.datos import cargar_perfiles
from src.app.ruta.pgu_review import is_personal_pgu_question, review_pgu


@pytest.mark.parametrize("question", [
    "Quiero revisar si soy apto para la PGU", "¿En qué paso de la PGU estoy?",
    "¿Qué me falta para mi PGU?", "¿Puedo recibir la PGU?",
])
def test_personal_pgu_intent(question):
    assert is_personal_pgu_question(question)
    assert not is_personal_pgu_question("¿Qué es la PGU?")


@pytest.mark.parametrize("run,case", [(None, None), ("demo", {"autorizacion": False})])
def test_no_profile_is_read_without_identity_and_consent(run, case):
    def forbidden():
        pytest.fail("No leer perfiles sin autorización")

    text = review_pgu(run, case, forbidden)
    assert "Mi Gobierno" in text
    assert "autoriza" in text


def test_missing_pgu_information_is_requested_and_progress_uses_saved_steps():
    profiles = cargar_perfiles()
    run = next(run for run, profile in profiles.items()
               if reglas.diagnosticar(profile).pgu.resultado == reglas.ANTECEDENTE_FALTANTE)
    case = {"autorizacion": True, "completados": set()}
    text = review_pgu(run, case, lambda: profiles)
    assert "Antecedentes que faltan" in text
    assert "Adjúntalo aquí mismo" in text
    assert "0 de" in text
    assert "Próximo paso" in text
    assert "el IPS valida y resuelve" in text


def test_eligible_is_preliminary_and_never_promises_award():
    profiles = cargar_perfiles()
    run = next(run for run, profile in profiles.items()
               if reglas.diagnosticar(profile).pgu.resultado == reglas.ELEGIBLE)
    text = review_pgu(run, {"autorizacion": True, "completados": set()}, lambda: profiles)
    assert "Podrías solicitar" in text
    assert "Evaluación preliminar" in text


def test_pgu_followup_keeps_personal_review_context():
    assert is_personal_pgu_question("¿En qué paso estoy?", pgu_context=True)
    assert not is_personal_pgu_question("¿Qué es la PGU?", pgu_context=True)
