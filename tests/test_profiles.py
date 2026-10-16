import json
from datetime import UTC, datetime

import pytest

from src.contracts import Authorization, Case, Channel, Invitation, InvitationResponse, Profile
from src.tools.profiles import (
    DEFAULT_DATASET_PATH,
    ProfileRepository,
    consultar_perfil,
    normalize_run,
)


def authorized_case(run="100000001-5"):
    return Case(
        case_id="test-case",
        run=run,
        created_at=datetime.now(UTC),
        authorization=Authorization(
            granted=True,
            sources=["dataset_A"],
            purpose="Orientación jubilación y PGU",
            channel=Channel.WEB,
            decided_at=datetime.now(UTC),
        ),
    )


@pytest.fixture
def repository():
    return ProfileRepository()


@pytest.mark.parametrize("run", ["100000001-5", "100.000.001-5", " 100.000.001-5 "])
def test_existing_run_returns_shared_profile(run, repository):
    profile = consultar_perfil(run, case=authorized_case(), repository=repository)
    assert isinstance(profile, Profile)
    assert profile.run == "100000001-5"
    assert profile.civil_registry.first_names == "Luis Cristián"


def test_nonexistent_run_returns_none(repository):
    run = "12345678-5"
    assert consultar_perfil(run, case=authorized_case(run), repository=repository) is None


def test_missing_rsh_is_preserved(repository):
    rows = json.loads(DEFAULT_DATASET_PATH.read_text(encoding="utf-8"))
    row = next(row for row in rows if row["rsh"] is None)
    profile = consultar_perfil(row["run"], case=authorized_case(row["run"]), repository=repository)
    assert profile.rsh is None
    assert profile.model_dump(mode="json", by_alias=True) == row


@pytest.mark.parametrize("case_state", ["missing", "no_consent", "declined", "pending"])
def test_denied_access_does_not_read_dataset(tmp_path, case_state):
    case = authorized_case()
    if case_state == "missing":
        case = None
    elif case_state == "no_consent":
        case.authorization.granted = False
    else:
        case.invitation = Invitation(
            reason="Preparar próximo hito",
            channel=Channel.WEB,
            sent_at=datetime.now(UTC),
            response=(
                InvitationResponse.DECLINED
                if case_state == "declined"
                else InvitationResponse.PENDING
            ),
        )
    repository = ProfileRepository(tmp_path / "file-that-must-not-be-read.json")
    with pytest.raises(PermissionError):
        consultar_perfil("100000001-5", case=case, repository=repository)


def test_authorization_cannot_be_reused_for_another_person(tmp_path):
    repository = ProfileRepository(tmp_path / "not-read.json")
    with pytest.raises(PermissionError, match="no corresponde"):
        consultar_perfil("100000002-3", case=authorized_case(), repository=repository)


def test_mutating_returned_lists_does_not_modify_cached_profile(repository):
    case = authorized_case()
    first = consultar_perfil(case.run, case=case, repository=repository)
    first.pension_fund.contributions.clear()
    second = consultar_perfil(case.run, case=case, repository=repository)
    assert len(second.pension_fund.contributions) == 12


@pytest.mark.parametrize("run", ["", "100000001-6", "1000000016", "100..000.001-5", "abc", None])
def test_invalid_run_is_rejected(run):
    with pytest.raises(ValueError):
        normalize_run(run)


def test_lowercase_k_is_normalized():
    assert normalize_run("12.345.670-k") == "12345670-K"


@pytest.mark.parametrize("run", ["123456785", "12345678-5", "12.345.678-5", " 12 345 678 5 "])
def test_run_without_hyphen_matches_demo_login(run):
    from src.app.ruta.demo_auth import normalize_run as demo_normalize

    assert normalize_run(run) == demo_normalize(run) == "12345678-5"


def test_dataset_with_duplicates_fails_explicitly(tmp_path):
    row = json.loads(DEFAULT_DATASET_PATH.read_text(encoding="utf-8"))[0]
    path = tmp_path / "duplicates.json"
    path.write_text(json.dumps([row, row]), encoding="utf-8")
    with pytest.raises(ValueError, match="duplicados"):
        consultar_perfil(row["run"], case=authorized_case(), repository=ProfileRepository(path))
