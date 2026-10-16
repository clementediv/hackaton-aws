import boto3
import pytest
from moto import mock_aws

from src.app.ruta import casos, config, correo, ficha, government
from src.app.ruta import reglas as rules
from src.app.ruta.datos import cargar_perfiles

INBOX = "persona@utem.cl"


@pytest.fixture
def person(tmp_path, monkeypatch):
    monkeypatch.setattr(config, "DB_PATH", tmp_path / "correo.db")
    monkeypatch.setattr(config, "SES_SENDER", "")
    run, profile = next(iter(cargar_perfiles().items()))
    casos.responder_invitacion(run, True, "Web")
    casos.autorizar(run, True, "Web")
    return run, profile


@pytest.fixture
def ses(monkeypatch):
    for key in ("AWS_PROFILE", "AWS_DEFAULT_PROFILE"):
        monkeypatch.delenv(key, raising=False)
    monkeypatch.setenv("AWS_ACCESS_KEY_ID", "testing")
    monkeypatch.setenv("AWS_SECRET_ACCESS_KEY", "testing")
    with mock_aws():
        yield boto3.client("ses", region_name="us-east-1")


def test_email_requires_consent_and_a_valid_address(tmp_path, monkeypatch, person):
    run, _ = person
    with pytest.raises(ValueError):
        correo.save_email(run, "no-es-un-correo")
    other = next(r for r in cargar_perfiles() if r != run)
    with pytest.raises(PermissionError):
        correo.save_email(other, INBOX)


def test_declared_email_becomes_the_contact_and_is_deleted_on_revoke(person):
    run, profile = person
    assert correo.save_email(run, "  Persona@UTEM.cl ") == INBOX
    contact, source = ficha.contact_for(run, profile)
    assert contact.email == INBOX and source == ficha.SOURCE_PERSON
    assert any(e["tipo"] == "correo_actualizado" for e in casos.obtener_caso(run)["eventos"])
    government.delete_personal_data(run)
    assert ficha.contact_for(run, profile)[0].email != INBOX


def test_summary_is_sent_only_to_a_verified_inbox(person, ses, monkeypatch):
    run, profile = person
    diagnosis = rules.diagnosticar(profile)
    correo.save_email(run, INBOX)
    # moto verifies identities immediately; simulate the sandbox's pending link.
    real_verified = correo._verified
    monkeypatch.setattr(correo, "_verified", lambda client, address: False)
    assert correo.send_summary(run, diagnosis, ses) == correo.VERIFICATION_SENT
    assert correo.send_summary(run, diagnosis, ses) == correo.PENDING_VERIFICATION
    monkeypatch.setattr(correo, "_verified", real_verified)
    assert correo.send_summary(run, diagnosis, ses) == correo.SENT
    assert ses.get_send_statistics()["SendDataPoints"][0]["DeliveryAttempts"] == 1
    events = [e["tipo"] for e in casos.obtener_caso(run)["eventos"]]
    assert "correo_verificacion_solicitada" in events and "resumen_enviado" in events


def test_summary_states_it_is_not_a_resolution(person):
    _, profile = person
    subject, text, html = correo.summary(rules.diagnosticar(profile))
    assert "Mi Gobierno" in subject
    assert "No es una resolución" in text and config.FUENTE_PGU in html
