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
PERSON = {"run": "90000002-2", "nombre": "Jorge Demo", "fecha_nacimiento": "1963-01-10"}
APP_DIR = Path(__file__).resolve().parents[1] / "src/app"


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


def test_contacts_for_carries_the_notice_texts(db):
    dynamodb, jorge, _ = db
    (contact,) = aws.contacts_for(jorge, dynamodb)
    assert contact["beneficio_id"] == "pgu" and contact["nombre"] == "Jorge Demo"
    assert "PGU" in contact["titulo"] or "Pensión" in contact["titulo"]
    assert "65 años" in contact["por_que"]
    assert "token" not in contact


def test_event_changes_the_person_only_if_it_exists(db):
    dynamodb, jorge, _ = db
    values = aws.event_values(age=(65, 2), children=1, accident=True, reference=TODAY)
    assert values == {
        "fecha_nacimiento": "1961-08-15",
        "num_hijos": 1,
        "accidente_laboral": True,
    }
    aws.apply_event(jorge, values, dynamodb)
    person = dynamodb.Table("ca-personas").get_item(Key={"run": jorge})["Item"]
    assert person["fecha_nacimiento"] == "1961-08-15" and person["num_hijos"] == 1
    with pytest.raises(ClientError):
        aws.apply_event("11111111-1", values, dynamodb)
    with pytest.raises(ValueError):
        aws.apply_event(jorge, {}, dynamodb)


def test_accepting_in_the_app_stops_every_open_contact(db, monkeypatch):
    dynamodb, jorge, paula = db
    monkeypatch.setenv("CA_AWS", "1")
    assert aws.sync_invitation(paula, True, "Mi Gobierno", dynamodb) == ["suf"]
    (contact,) = aws.contacts_for(paula, dynamodb)
    assert (contact["estado"], contact["respuesta_canal"]) == ("aceptado", "Mi Gobierno")
    assert "cola" not in contact and contact["paso_siguiente"]
    assert aws.sync_invitation(paula, False, "Mi Gobierno", dynamodb) == []  # first answer wins
    assert [e["evento"] for e in aws.load_history(paula, dynamodb)][-1] == "respuesta_acepto"
    assert aws.sync_invitation(jorge, False, "Web", dynamodb) == ["pgu"]
    assert aws.contacts_for(jorge, dynamodb)[0]["estado"] == "rechazado"


def test_sync_is_off_with_ca_aws_0(db):
    dynamodb, _, paula = db  # conftest sets CA_AWS=0
    assert aws.sync_invitation(paula, True, "Mi Gobierno", dynamodb) == []
    assert aws.contacts_for(paula, dynamodb)[0]["estado"] == "email_enviado"
    assert not aws.check()[0]


def test_answer_one_benefit_and_reset_a_person(db):
    dynamodb, jorge, _ = db
    contact = aws.record_answer(jorge, "pgu", "acepto", "Mi Gobierno", dynamodb)
    assert contact["estado"] == "aceptado" and "token" in contact
    assert aws.reset_person(jorge, dynamodb) == (1, 3)
    assert aws.contacts_for(jorge, dynamodb) == []


def test_case_answers_notify_listeners(tmp_path, monkeypatch):
    from src.app.ruta import casos, config

    monkeypatch.setattr(config, "DB_PATH", tmp_path / "cases.db")
    calls = []
    monkeypatch.setattr(casos, "_oyentes_respuesta", {})
    casos.al_responder_invitacion("test", lambda *args: calls.append(args))
    casos.al_responder_invitacion("test", lambda *args: calls.append(args))  # rerun: no duplicate
    casos.responder_invitacion("100000010-4", True, "Web")
    assert calls == [("100000010-4", True, "Web")]
    assert casos.obtener_caso("100000010-4")["invitacion"] == "aceptado"


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
    monkeypatch.setattr(module, "load_people", lambda dynamodb=None: [PERSON])
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


def test_officer_simulates_a_life_event(monkeypatch, tmp_path):
    pytest.importorskip("streamlit")
    monkeypatch.syspath_prepend(str(APP_DIR))
    module = importlib.import_module("ruta.aws_contactos")
    applied, detected = [], {"n": 0}

    def contacts_for(run, dynamodb=None):
        detected["n"] += 1  # before the event: none; then the Lambda wrote one
        return [] if detected["n"] == 1 else [{"beneficio_id": "pgu", "estado": "email_enviado"}]

    monkeypatch.setattr(module, "contacts_for", contacts_for)
    monkeypatch.setattr(module, "apply_event", lambda run, values: applied.append((run, values)))
    app = _app(monkeypatch, tmp_path, available=True)
    assert app.selectbox(key="aws_event_person").value.startswith("90000002-2 · Jorge Demo")
    form = app.number_input
    next(n for n in form if n.label == "Edad (años)").set_value(65)
    next(b for b in app.button if b.label == "Aplicar evento").click().run()
    assert not app.exception
    ((run, values),) = applied
    assert run == "90000002-2" and set(values) == {"fecha_nacimiento"}
    assert "Detección lista" in app.success[0].value


def test_mi_gobierno_shows_the_aws_notice_and_answers(monkeypatch, tmp_path):
    pytest.importorskip("streamlit")
    from streamlit.testing.v1 import AppTest

    app_dir = Path(__file__).resolve().parents[1] / "src/app"
    monkeypatch.syspath_prepend(str(app_dir))
    config = importlib.import_module("ruta.config")
    monkeypatch.setattr(config, "DB_PATH", tmp_path / "gov-aws.db")
    monkeypatch.setattr(config, "BEDROCK_MODEL_ID", "")
    module = importlib.import_module("ruta.aws_contactos")
    importlib.import_module("streamlit").cache_data.clear()
    answers, synced = [], []
    notice = {
        "beneficio_id": "pgu",
        "titulo": "Felicitaciones: aparentemente usted es elegible a la PGU",
        "por_que": "Usted cumplió 65 años.",
        "estado": "email_enviado",
        "email_enviado": True,
        "email_enviado_en": "2026-10-16T15:00:00+00:00",
    }
    monkeypatch.setattr(module, "check", lambda dynamodb=None: (True, ""))
    monkeypatch.setattr(module, "contacts_for", lambda run, dynamodb=None: [notice])
    monkeypatch.setattr(module, "record_answer", lambda *args: answers.append(args))
    monkeypatch.setattr(module, "sync_invitation", lambda *args: synced.append(args) or [])

    app = AppTest.from_file(str(app_dir / "app.py"), default_timeout=30).run()
    app.radio(key="portal_section").set_value("Mi Gobierno").run()
    run = app.selectbox(key="gov_demo_example").value
    app.text_input(key="gov_login_rut").set_value(run)
    app.text_input(key="gov_login_password").set_value("demo2026")
    next(button for button in app.button if button.label == "Ingresar a Mi Gobierno").click().run()
    assert not app.exception
    run = app.session_state["government_person"]
    assert any(notice["titulo"] in m.value for m in app.markdown)
    assert any("te envió un email el 16-10-2026" in c.value for c in app.caption)
    next(b for b in app.button if b.label == "Quiero orientación").click().run()
    assert answers == [(run, "pgu", "acepto", "Mi Gobierno")]

    next(i for i in app.checkbox if i.label.startswith("Acepto el acompañamiento")).check().run()
    next(b for b in app.button if b.label == "Activar Mi Gobierno").click().run()
    assert not app.exception
    assert synced == [(run, True, "Web ChileAtiende")]
