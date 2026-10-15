import json

from src.api import handler


def test_missing_key_never_creates_client(monkeypatch):
    monkeypatch.setattr(
        handler.BedrockClient, "from_env", lambda: (_ for _ in ()).throw(AssertionError())
    )
    assert handler.on_http({"headers": {}}, None)["statusCode"] == 401


def test_health_and_authorizer(monkeypatch):
    monkeypatch.setattr(handler, "api_key", lambda: "test-key")

    class Client:
        def converse(self, *args, **kwargs):
            return {"output": {"message": {"content": [{"text": "OK"}]}}}

    monkeypatch.setattr(handler.BedrockClient, "from_env", lambda: Client())
    event = {
        "headers": {"x-api-key": "test-key"},
        "rawPath": "/health",
        "requestContext": {"http": {"method": "GET"}},
    }
    assert handler.authorize(event, None) == {"isAuthorized": True}
    result = handler.on_http(event, None)
    assert result["statusCode"] == 200
    assert json.loads(result["body"])["data"]["bedrock"] == "OK"
    event["headers"]["x-api-key"] = "wrong"
    assert handler.authorize(event, None) == {"isAuthorized": False}
