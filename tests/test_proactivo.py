import json
from datetime import UTC, date, datetime, timedelta
from pathlib import Path

import boto3
import pytest
from boto3.dynamodb.types import TypeSerializer
from moto import mock_aws
from moto.core import DEFAULT_ACCOUNT_ID
from moto.ses.models import ses_backends

from src.proactivo import carga, handlers
from src.proactivo.catalogo import BENEFICIOS
from src.proactivo.esquema import create_tables
from src.proactivo.reglas import add_years, eligible_from, evaluate
from src.proactivo.servicio import Service, Settings

TODAY = date(2026, 10, 15)
INBOX = "demo@utem.cl"
BENEFIT = {b["beneficio_id"]: b for b in BENEFICIOS}


class Clock:
    def __init__(self):
        self.now = datetime(2026, 10, 15, 15, 0, tzinfo=UTC)

    def __call__(self):
        return self.now

    def advance(self, minutes):
        self.now += timedelta(minutes=minutes)


@pytest.fixture
def env(monkeypatch):
    for key in ("AWS_PROFILE", "AWS_DEFAULT_PROFILE"):
        monkeypatch.delenv(key, raising=False)
    monkeypatch.setenv("AWS_ACCESS_KEY_ID", "testing")
    monkeypatch.setenv("AWS_SECRET_ACCESS_KEY", "testing")
    monkeypatch.setenv("AWS_DEFAULT_REGION", "us-east-1")
    with mock_aws():
        db = boto3.resource("dynamodb", region_name="us-east-1")
        ses = boto3.client("ses", region_name="us-east-1")
        ses.verify_email_identity(EmailAddress=INBOX)
        settings = Settings(
            sender=INBOX,
            real_emails=frozenset({INBOX}),
            response_url="https://respuesta.example",
            reference_date=TODAY,
        )
        create_tables(db.meta.client, settings.table_names())
        with db.Table(settings.beneficios).batch_writer() as batch:
            for benefit in BENEFICIOS:
                batch.put_item(Item=benefit)
        clock = Clock()
        svc = Service(settings, dynamodb=db, ses=ses, clock=clock)
        yield svc, clock, db


def demo(name):
    return next(p for p in carga.demo_people(INBOX, TODAY) if p["nombre"].startswith(name))


def insert(svc, person):
    svc.people.put_item(Item=person)
    return svc.on_person_change(None, svc.person(person["run"]), "carga")


def change(svc, run, **values):
    old = svc.person(run)
    new = old | values
    svc.people.put_item(Item=new)
    return svc.on_person_change(old, svc.person(run), "cambio")


def sent_emails():
    return ses_backends[DEFAULT_ACCOUNT_ID]["us-east-1"].sent_messages


def test_demo_people_are_quiet_on_insert(env):
    svc, _, _ = env
    for person in carga.demo_people(INBOX, TODAY):
        assert insert(svc, person) == []
    assert sent_emails() == []


def test_turning_65_sends_a_real_email_about_pgu(env):
    svc, _, _ = env
    jorge = demo("Jorge")
    insert(svc, jorge)
    opened = change(svc, jorge["run"], fecha_nacimiento=add_years(TODAY, -65).isoformat())
    assert [c["beneficio_id"] for c in opened] == ["pgu"]
    contact = opened[0]
    assert contact["estado"] == "email_enviado"
    assert contact["email_enviado"] and not contact["email_simulado"]
    assert "edad: 64 → 65" in contact["motivo"]
    assert len(sent_emails()) == 1
    assert sent_emails()[0].destinations["ToAddresses"] == [INBOX]
    assert contact["cola"] == "pendiente"


@pytest.mark.parametrize(
    ("name", "values", "expected"),
    [
        (
            "Camila",
            {"fecha_nacimiento": add_years(TODAY, -18).isoformat()},
            "subsidio_empleo_joven",
        ),
        ("Paula", {"num_hijos": 1}, "suf"),
        ("Marcelo", {"estado_civil": "casado"}, "asignacion_conyuge"),
        ("Pedro", {"accidente_laboral": True}, "seguro_laboral"),
        ("Ana", {"tramo_rsh": 70}, "subsidio_electrico"),
    ],
)
def test_each_life_event_detects_its_benefit(env, name, values, expected):
    svc, _, _ = env
    person = demo(name)
    insert(svc, person)
    opened = change(svc, person["run"], **values)
    assert [c["beneficio_id"] for c in opened] == [expected]


def test_same_change_twice_opens_one_contact(env):
    svc, _, _ = env
    paula = demo("Paula")
    insert(svc, paula)
    assert change(svc, paula["run"], num_hijos=1)
    assert change(svc, paula["run"], num_hijos=2) == []
    assert len(svc.contacts_of(paula["run"])) == 1


def test_exclusions_and_missing_records(env):
    svc, _, _ = env
    ana = demo("Ana")
    insert(svc, ana)
    assert change(svc, ana["run"], tramo_rsh=70, beneficios_vigentes=["subsidio_electrico"]) == []
    pedro = demo("Pedro")
    insert(svc, pedro)
    assert change(svc, pedro["run"], accidente_laboral=True, fallecido=True) == []
    without_rsh = {k: v for k, v in demo("Jorge").items() if k != "percentil_pfp"}
    without_rsh["fecha_nacimiento"] = add_years(TODAY, -70).isoformat()
    assert evaluate(without_rsh, BENEFIT["pgu"], TODAY).cumple is None
    assert [c["beneficio_id"] for c in insert(svc, without_rsh)] == []


def test_no_answer_escalates_email_sms_field(env):
    svc, clock, _ = env
    paula = demo("Paula")
    insert(svc, paula)
    change(svc, paula["run"], num_hijos=1)
    key = (paula["run"], "suf")
    svc.interact(*key, svc.contact(*key)["token"], "abrir", "email")
    svc.interact(*key, svc.contact(*key)["token"], "ver", "email")
    assert svc.escalate() == 0  # not due yet
    clock.advance(6)
    assert svc.escalate() == 1
    contact = svc.contact(*key)
    assert contact["estado"] == "sms_enviado" and contact["sms_simulado"]
    assert contact["email_abierto"] and contact["email_click"]  # recorded, did not stop it
    clock.advance(6)
    assert svc.escalate() == 1
    contact = svc.contact(*key)
    assert contact["estado"] == "terreno" and contact["respuesta"] == "sin_respuesta"
    assert "cola" not in contact
    assert [c["run"] for c in svc.by_state("terreno")] == [paula["run"]]
    events = [e["evento"] for e in svc.history_of(paula["run"])]
    assert events == [
        "detectado",
        "email_enviado",
        "email_abierto",
        "entro_al_mensaje",
        "sin_respuesta",
        "sms_enviado",
        "sin_respuesta",
        "asignado_terreno",
    ]


def test_accepting_stops_channels_and_sets_next_step(env):
    svc, clock, _ = env
    pedro = demo("Pedro")
    insert(svc, pedro)
    change(svc, pedro["run"], accidente_laboral=True)
    key = (pedro["run"], "seguro_laboral")
    token = svc.contact(*key)["token"]
    with pytest.raises(PermissionError):
        svc.interact(*key, "otro-token", "acepto", "email")
    contact = svc.interact(*key, token, "acepto", "email")
    assert contact["estado"] == "aceptado" and contact["respuesta_canal"] == "email"
    assert contact["paso_siguiente"] == BENEFIT["seguro_laboral"]["paso_siguiente"]
    svc.interact(*key, token, "rechazo", "email")  # first answer wins
    assert svc.contact(*key)["estado"] == "aceptado"
    clock.advance(60)
    assert svc.escalate() == 0


def test_field_team_records_answers(env):
    svc, _, _ = env
    ana = demo("Ana")
    insert(svc, ana)
    change(svc, ana["run"], tramo_rsh=70)
    contact = svc.record_answer(ana["run"], "subsidio_electrico", "rechazo", "terreno")
    assert contact["estado"] == "rechazado" and contact["respuesta_canal"] == "terreno"


def test_missing_channels_are_skipped(env):
    svc, _, _ = env
    paula = demo("Paula") | {"email": "", "telefono": ""}
    insert(svc, paula)
    contact = change(svc, paula["run"], num_hijos=1)[0]
    assert contact["estado"] == "terreno"
    events = [(e["evento"], e["canal"]) for e in svc.history_of(paula["run"])]
    assert ("canal_omitido", "email") in events and ("canal_omitido", "sms") in events


def test_simulated_inbox_is_never_sent(env):
    svc, _, _ = env
    paula = demo("Paula") | {"email": "paula@example.com"}
    insert(svc, paula)
    contact = change(svc, paula["run"], num_hijos=1)[0]
    assert contact["email_enviado"] and contact["email_simulado"]
    assert sent_emails() == []


def test_anticipation_then_available(env):
    svc, clock, _ = env
    birthday = TODAY + timedelta(days=30)
    jorge = demo("Jorge") | {"fecha_nacimiento": add_years(birthday, -65).isoformat()}
    assert eligible_from(jorge, BENEFIT["pgu"], TODAY) == birthday
    contact = insert(svc, jorge)[0]
    assert contact["tipo"] == "anticipado"
    assert contact["disponible_desde"] == birthday.strftime("%d-%m-%Y")
    svc.record_answer(jorge["run"], "pgu", "acepto", "telefono")
    later = Service(
        Settings(**{**svc.settings.__dict__, "reference_date": birthday}),
        dynamodb=boto3.resource("dynamodb", region_name="us-east-1"),
        ses=svc.ses,
        clock=clock,
    )
    assert later.reconcile_all() == 1
    contact = later.contact(jorge["run"], "pgu")
    assert contact["tipo"] == "disponible" and contact["estado"] == "aceptado"
    assert len(sent_emails()) == 2


def test_stream_and_http_handlers(env, monkeypatch):
    svc, _, _ = env
    monkeypatch.setattr(handlers, "_service", svc)
    pedro = demo("Pedro")
    svc.people.put_item(Item=pedro)
    serializer = TypeSerializer()

    def image(item):
        return {k: serializer.serialize(v) for k, v in item.items()}

    event = {
        "Records": [
            {
                "eventName": "MODIFY",
                "dynamodb": {
                    "SequenceNumber": "1",
                    "OldImage": image(pedro),
                    "NewImage": image(pedro | {"accidente_laboral": True}),
                },
            }
        ]
    }
    assert handlers.on_person_change(event, None) == {"batchItemFailures": []}
    contact = svc.contact(pedro["run"], "seguro_laboral")
    query = {"c": pedro["run"], "b": "seguro_laboral", "t": contact["token"], "v": "email"}
    pixel = handlers.on_http({"queryStringParameters": query | {"a": "abrir"}}, None)
    assert pixel["headers"]["Content-Type"] == "image/gif"
    page = handlers.on_http({"queryStringParameters": query | {"a": "ver"}}, None)
    assert page["statusCode"] == 200 and "Sí, quiero ayuda" in page["body"]
    page = handlers.on_http({"queryStringParameters": query | {"a": "acepto"}}, None)
    assert "Tu próximo paso" in page["body"]
    bad = handlers.on_http({"queryStringParameters": query | {"t": "x", "a": "acepto"}}, None)
    assert bad["statusCode"] == 400


def test_dataset_detection_respects_current_benefits(env):
    svc, _, _ = env
    contacts = carga.load_contacts()
    profiles = json.loads(carga.PROFILES.read_text(encoding="utf-8"))
    people = [carga.from_dataset(p, contacts.get(p["run"])) for p in profiles]
    assert all(p["email"].endswith("@example.com") for p in people if p.get("email"))
    opened = [c for person in people for c in insert(svc, person)]
    assert opened and sent_emails() == []
    receiving = {p["run"] for p in people if "pgu" in p["beneficios_vigentes"]}
    dead = {p["run"] for p in people if p["fallecido"]}
    assert not {c["run"] for c in opened if c["beneficio_id"] == "pgu"} & receiving
    assert not {c["run"] for c in opened} & dead


def test_lambda_package_is_self_contained():
    for path in Path("src/proactivo").glob("*.py"):
        text = path.read_text(encoding="utf-8")
        if path.name in ("carga.py",):
            continue
        assert "from src" not in text and "import src" not in text, path
