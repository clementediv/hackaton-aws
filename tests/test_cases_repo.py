from datetime import UTC, date, datetime

import boto3
import pytest
from moto import mock_aws

from src.cases.repositorio import CaseRepository
from src.contracts import (
    Authorization,
    Channel,
    Invitation,
    InvitationResponse,
    Message,
    MessageRole,
)


@pytest.fixture
def repo(monkeypatch):
    monkeypatch.setenv("AWS_DEFAULT_REGION", "us-east-1")
    monkeypatch.delenv("AWS_PROFILE", raising=False)
    with mock_aws():
        table = boto3.resource("dynamodb").create_table(
            TableName="ca-casos",
            BillingMode="PAY_PER_REQUEST",
            KeySchema=[
                {"AttributeName": "pk", "KeyType": "HASH"},
                {"AttributeName": "sk", "KeyType": "RANGE"},
            ],
            AttributeDefinitions=[
                {"AttributeName": x, "AttributeType": "S"}
                for x in ("pk", "sk", "run", "created_at")
            ],
            GlobalSecondaryIndexes=[
                {
                    "IndexName": "por-run",
                    "KeySchema": [
                        {"AttributeName": "run", "KeyType": "HASH"},
                        {"AttributeName": "created_at", "KeyType": "RANGE"},
                    ],
                    "Projection": {"ProjectionType": "ALL"},
                }
            ],
        )
        yield CaseRepository(table)


def test_round_trip_and_append_order(repo):
    case = repo.crear("100000001-5")
    now = datetime.now(UTC)
    case.invitation = Invitation(
        reason="Orientación", channel=Channel.WEB, sent_at=now, response=InvitationResponse.ACCEPTED
    )
    case.authorization = Authorization(
        granted=True, sources=["Dataset A"], purpose="Orientar", channel=Channel.WEB, decided_at=now
    )
    from src.contracts import (
        ChecklistItem,
        Milestone,
        MilestoneKind,
        PguResult,
        PguStatus,
        RouteStep,
    )

    case.pgu_result = PguResult(
        run=case.run, status=PguStatus.ELIGIBLE, reference_date=date.today()
    )
    case.milestones = [
        Milestone(kind=MilestoneKind.PGU_ACCESS, date=date.today(), description="Hito")
    ]
    case.route = [RouteStep(order=1, title="Consultar", description="Orientación preliminar")]
    case.checklist = [ChecklistItem(item_id="id", label="Identidad")]
    repo.guardar_estado(case)
    messages = [
        Message(role=MessageRole.PERSON, channel=Channel.WEB, text=str(n), created_at=now)
        for n in range(3)
    ]
    repo.agregar_mensajes(case.case_id, messages[:2])
    repo.agregar_mensajes(case.case_id, messages[2:])
    case.messages = messages
    assert repo.cargar(case.case_id) == case
    assert repo.buscar_por_run(case.run) == [case]
    assert repo.cargar(case.case_id).can_read_profile
    case.authorization.granted = False
    repo.guardar_estado(case)
    assert not repo.cargar(case.case_id).can_read_profile
    assert len(repo.cargar(case.case_id).messages) == 3


def test_invalid_and_missing(repo):
    with pytest.raises(ValueError):
        repo.crear("100000001-0")
    with pytest.raises(KeyError):
        repo.cargar("missing")
