import json

from src.api import handler, http

pytest_plugins = ["test_cases_repo"]


def event(path, body=None, method="POST", run="100000001-5"):
    return {
        "version": "2.0",
        "rawPath": path,
        "body": json.dumps(body or {}),
        "headers": {"x-api-key": "key", "x-run": run},
        "requestContext": {"http": {"method": method}},
    }


def test_flow_and_errors(repo, monkeypatch):
    monkeypatch.setattr(handler, "api_key", lambda: "key")
    monkeypatch.setattr(http, "CaseRepository", lambda: repo)

    def call(e):
        return handler.on_http(e, None)

    result = call(event("/casos", {"run": "100000001-5"}))
    assert result["statusCode"] == 200
    case_id = json.loads(result["body"])["data"]["case_id"]
    path = f"/casos/{case_id}"
    assert call(event(path, method="GET", run="100000002-3"))["statusCode"] == 403
    assert call(event("/casos/missing", method="GET"))["statusCode"] == 404
    assert call(event("/casos", {"run": "100000001-0"}))["statusCode"] == 400
    consent = {"granted": True, "sources": ["Dataset A"], "purpose": "Orientar"}
    assert call(event(path + "/autorizacion", consent))["statusCode"] == 403
    assert call(event(path + "/invitacion", {"response": "aceptada"}))["statusCode"] == 200
    assert call(event(path + "/autorizacion", {**consent, "sources": []}))["statusCode"] == 400
    assert call(event(path + "/autorizacion", consent))["statusCode"] == 200
    assert repo.cargar(case_id).can_read_profile
    assert call(event(path + "/invitacion", {"response": "declinada"}))["statusCode"] == 200
    assert not repo.cargar(case_id).can_read_profile


def test_internal_error_not_exposed(monkeypatch):
    monkeypatch.setattr(handler, "api_key", lambda: "key")

    def fail():
        raise RuntimeError("sensitive-internal")

    monkeypatch.setattr(http, "CaseRepository", fail)
    result = handler.on_http(event("/casos", {"run": "100000001-5"}), None)
    assert result["statusCode"] == 503
    assert "sensitive" not in result["body"]
