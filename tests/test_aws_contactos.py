import importlib
from datetime import UTC, date, datetime
from pathlib import Path

import boto3
import pytest
from botocore.exceptions import ClientError
from moto import mock_aws

from src.app.ruta import aws_contactos as aws
from src.proactivo import carga
from src.proactivo.catalogo import BENEFICIOS
from src.proactivo.esquema import create_tables
from src.proactivo.reglas import add_years
from src.proactivo.servicio import Service, Settings

TODAY = date(2026, 10, 15)
INBOX = "demo@utem.cl"


@pytest.fixture
def db(monkeypatch):
    for key in ("AWS_PROFILE", "AWS_DEFAULT_PROFILE"):
        monkeypatch.delenv(key, raising=False)
    monkeypatch.setenv("AWS_ACCESS_KEY_ID", "testing")
    monkeypatch.setenv("AWS_SECRET_ACCESS_KEY", "testing")
    with mock_aws():
        dynamodb = boto3.resource("dynamodb", region_name="us-east-1")
        ses = boto3.client("ses", region_name="us-east-1")
        ses.verify_email_identity(EmailAddress=INBOX)
        settings = Settings(sender=INBOX, real_emails=frozenset({INBOX}), reference_date=TODAY)
        create_tables(dynamodb.meta.client, settings.table_names())
        with dynamodb.Table(settings.beneficios).batch_writer() as batch:
            for benefit in BENEFICIOS:
                batch.put_item(Item=benefit)
        svc = Service(
            settings,
            dynamodb=dynamodb,
            ses=ses,
            clock=lambda: datetime(2026, 10, 15, 15, tzinfo=UTC),
        )
        people = {p["nombre"].split()[0]: p for p in carga.demo_people(INBOX, TODAY)}
        jorge, paula = people["Jorge"], people["Paula"] | {"email": "paula@example.com"}
        for person in (jorge, paula):
            svc.people.put_item(Item=person)
        old = svc.person(jorge["run"])
        svc.people.put_item(Item=old | {"fecha_nacimiento": add_years(TODAY, -65).isoformat()})
        svc.on_person_change(old, svc.person(jorge["run"]), "cambio")
        old = svc.person(paula["run"])
        svc.people.put_item(Item=old | {"num_hijos": 1})
        svc.on_person_change(old, svc.person(paula["run"]), "cambio")
        yield dynamodb, jorge["run"], paula["run"]


def test_contacts_carry_names_labels_and_no_token(db):
    dynamodb, jorge, paula = db
    contacts = {c["run"]: c for c in aws.load_contacts(dynamodb)}
    assert set(contacts) == {jorge, paula}
    assert contacts[jorge]["nombre"] == "Jorge Demo"
    assert contacts[jorge]["estado_texto"] == "Email enviado, sin respuesta"
    assert contacts[jorge]["tipo_texto"] == "Podría recibirlo hoy"
    assert all("token" not in c for c in contacts.values())


def test_summary_separates_real_and_simulated_email(db):
    dynamodb, _, _ = db
    s = aws.summary(aws.load_contacts(dynamodb))
    assert (s["personas"], s["emails_reales"], s["emails_simulados"]) == (2, 1, 1)
    assert s["por_beneficio"]["Subsidio Único Familiar (SUF)"] == 1


def test_history_is_readable(db):
    dynamodb, jorge, _ = db
    events = aws.load_history(jorge, dynamodb)
    assert [e["evento_texto"] for e in events] == ["Detectado", "Email enviado"]
    assert events[0]["fecha"].startswith("2026-10-15 15:00")


def test_check_explains_expired_credentials():
    class Expired:
        def Table(self, name):  # noqa: N802 - boto3 resource API
            return self

        def scan(self, **_):
            error = {"Error": {"Code": "ExpiredTokenException", "Message": "expired"}}
            raise ClientError(error, "Scan")

    ok, message = aws.check(Expired())
    assert not ok and "vencieron" in message


def _app(monkeypatch, tmp_path, *, available):
    st = pytest.importorskip("streamlit", reason="Instalar el grupo app para verificar la UI")
    from streamlit.testing.v1 import AppTest

    st.cache_data.clear()  # the AWS status is cached across reruns

    app_dir = Path(__file__).resolve().parents[1] / "src/app"
    monkeypatch.syspath_prepend(str(app_dir))
    config = importlib.import_module("ruta.config")
    monkeypatch.setattr(config, "DB_PATH", tmp_path / "ui-cases.db")
    monkeypatch.setattr(config, "BEDROCK_MODEL_ID", "")
    module = importlib.import_module("ruta.aws_contactos")
    sample = [
        {
            "run": "90000002-2",
            "nombre": "Jorge Demo",
            "beneficio_id": "pgu",
            "beneficio": "Pensión Garantizada Universal (PGU)",
            "tipo": "disponible",
            "tipo_texto": "Podría recibirlo hoy",
            "estado": "email_enviado",
            "estado_texto": "Email enviado, sin respuesta",
            "email_enviado": True,
            "email_simulado": False,
            "respuesta": "pendiente",
            "detectado_en": "2026-10-15T20:17:22+00:00",
        }
    ]
    reason = "" if available else "Las credenciales del perfil `hackaton` vencieron."
    monkeypatch.setattr(module, "check", lambda dynamodb=None: (available, reason))
    monkeypatch.setattr(module, "load_contacts", lambda dynamodb=None: sample)
    monkeypatch.setattr(module, "load_history", lambda run, dynamodb=None: [])
    app = AppTest.from_file(str(app_dir / "app.py"), default_timeout=30).run()
    app.button(key="open_executive").click().run()
    app.text_input(key="staff_login_email").set_value("ejecutivo.rm@example.com")
    app.text_input(key="staff_login_password").set_value("Ejecutivo2026!")
    next(button for button in app.button if button.label == "Ingresar como ejecutivo").click().run()
    app.radio(key="executive_section").set_value("Contactos AWS").run()
    assert not app.exception
    return app


def test_view_shows_aws_contacts(monkeypatch, tmp_path):
    app = _app(monkeypatch, tmp_path, available=True)
    metrics = {m.label: m.value for m in app.metric}
    assert metrics["Personas detectadas"] == "1"
    assert metrics["Emails reales enviados"] == "1"
    assert app.dataframe[0].value.iloc[0]["Nombre"] == "Jorge Demo"


def test_view_explains_when_aws_is_unavailable(monkeypatch, tmp_path):
    app = _app(monkeypatch, tmp_path, available=False)
    assert "vencieron" in app.warning[0].value
    assert not app.metric
