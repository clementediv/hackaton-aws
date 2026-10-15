"""Rutas HTTP v2 con validación y consentimiento explícito."""

import json
from datetime import UTC, datetime

from pydantic import BaseModel, ConfigDict, Field, ValidationError

from src.api.chat import responder
from src.cases.repositorio import CaseRepository
from src.contracts import Authorization, Channel, Invitation, InvitationResponse, LifeEvent
from src.tools.profiles import normalize_run


class Input(BaseModel):
    model_config = ConfigDict(extra="forbid")


class Create(Input):
    run: str
    event: LifeEvent = LifeEvent.RETIREMENT


class Invite(Input):
    response: InvitationResponse
    channel: Channel = Channel.WEB


class Consent(Input):
    granted: bool
    sources: list[str] = Field(min_length=1)
    purpose: str = Field(min_length=1, max_length=1000)
    channel: Channel = Channel.WEB


class Chat(Input):
    case_id: str
    text: str = Field(min_length=1, max_length=8000)
    channel: Channel = Channel.WEB


def dispatch(event, *, repo=None, client=None):
    repo = repo if repo is not None else CaseRepository()
    method = event["requestContext"]["http"]["method"]
    path = event.get("rawPath", "")
    headers = {k.lower(): v for k, v in event.get("headers", {}).items()}
    run = normalize_run(headers.get("x-run", ""))
    if event.get("isBase64Encoded"):
        import base64

        raw = base64.b64decode(event.get("body") or "", validate=True).decode()
    else:
        raw = event.get("body") or "{}"
    data = json.loads(raw)
    now = datetime.now(UTC)
    if method == "POST" and path == "/casos":
        body = Create.model_validate(data)
        if normalize_run(body.run) != run:
            raise PermissionError()
        case = repo.crear(run, body.event)
        case.invitation = Invitation(
            reason="Orientación preliminar sobre beneficios", channel=Channel.WEB, sent_at=now
        )
        repo.guardar_estado(case)
        return case.model_dump(mode="json")
    parts = path.strip("/").split("/")
    if method == "POST" and path == "/chat":
        body = Chat.model_validate(data)
        case_id = body.case_id
    elif len(parts) in (2, 3) and parts[0] == "casos":
        case_id = parts[1]
    else:
        raise KeyError(path)
    case = repo.cargar(case_id)
    if case.run != run:
        raise PermissionError()
    if method == "POST" and path == "/chat":
        return responder(case_id, body.text, body.channel, client=client, repo=repo)
    if method == "GET" and len(parts) == 2:
        return case.model_dump(mode="json")
    if method == "POST" and len(parts) == 3 and parts[2] == "invitacion":
        body = Invite.model_validate(data)
        if case.invitation is None:
            case.invitation = Invitation(reason="Orientación", channel=body.channel, sent_at=now)
        case.invitation.response = body.response
        case.invitation.responded_at = now
        if body.response != InvitationResponse.ACCEPTED and case.authorization:
            case.authorization.granted = False
    elif method == "POST" and len(parts) == 3 and parts[2] == "autorizacion":
        body = Consent.model_validate(data)
        if not case.invitation or case.invitation.response != InvitationResponse.ACCEPTED:
            raise PermissionError()
        case.authorization = Authorization(**body.model_dump(), decided_at=now)
    else:
        raise KeyError(path)
    repo.guardar_estado(case)
    return case.model_dump(mode="json")


def route(event):
    from src.api.handler import response

    try:
        return response(200, {"ok": True, "data": dispatch(event)})
    except PermissionError:
        return response(403, {"ok": False, "error": {"type": "forbidden"}})
    except KeyError:
        return response(404, {"ok": False, "error": {"type": "not_found"}})
    except (ValueError, ValidationError, TypeError):
        return response(400, {"ok": False, "error": {"type": "invalid_input"}})
