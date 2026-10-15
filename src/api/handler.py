"""API Gateway v2 health probe; authentication precedes Bedrock creation."""

import hmac
import json
import os
from functools import lru_cache

import boto3

from src.agent.bedrock import BedrockClient


@lru_cache(maxsize=1)
def api_key():
    return boto3.client("secretsmanager").get_secret_value(
        SecretId=os.environ["API_KEY_SECRET_ARN"]
    )["SecretString"]


def response(status, payload):
    return {
        "statusCode": status,
        "headers": {"content-type": "application/json"},
        "body": json.dumps(payload, ensure_ascii=False),
    }


def on_http(event, context):
    try:
        headers = {k.lower(): v for k, v in (event.get("headers") or {}).items()}
        supplied = headers.get("x-api-key", "")
        if not supplied or not hmac.compare_digest(supplied, api_key()):
            return response(401, {"ok": False, "error": {"type": "unauthorized"}})
        http = event.get("requestContext", {}).get("http", {})
        if http.get("method") != "GET" or event.get("rawPath") != "/health":
            return response(404, {"ok": False, "error": {"type": "not_found"}})
        result = BedrockClient.from_env().converse(
            [{"role": "user", "content": [{"text": "Responde solamente OK."}]}],
            inferenceConfig={"maxTokens": 16},
        )
        text = "".join(c.get("text", "") for c in result["output"]["message"]["content"])
        return response(200, {"ok": True, "data": {"bedrock": text}})
    except Exception:
        return response(503, {"ok": False, "error": {"type": "service_unavailable"}})


def authorize(event, context):
    try:
        supplied = (event.get("headers") or {}).get("x-api-key", "")
        return {"isAuthorized": bool(supplied) and hmac.compare_digest(supplied, api_key())}
    except Exception:
        return {"isAuthorized": False}
