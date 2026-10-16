"""Configurable Bedrock Converse client, without application/domain decisions."""

import os
from dataclasses import dataclass
from pathlib import Path
from typing import Any, Protocol

import boto3
from dotenv import dotenv_values

ALLOWED_MODEL_IDS = (
    "us.anthropic.claude-sonnet-5",
    "us.anthropic.claude-opus-5",
    "us.anthropic.claude-haiku-4-5",
)


@dataclass(frozen=True)
class BedrockSettings:
    model_id: str = ALLOWED_MODEL_IDS[0]
    region: str = "us-east-1"
    profile: str | None = None

    def __post_init__(self) -> None:
        if self.model_id not in ALLOWED_MODEL_IDS:
            raise ValueError("BEDROCK_MODEL_ID no está permitido por la cuenta del evento.")
        if not self.region.strip():
            raise ValueError("AWS_REGION no puede estar vacío.")

    @classmethod
    def from_env(cls, env_file: str | Path = ".env") -> "BedrockSettings":
        """Read an explicit dotenv file; process variables take precedence.

        The process environment is not mutated. An absent/empty profile uses
        boto3's default credential chain, including an IAM role on AWS.
        """
        values = {**dotenv_values(env_file, interpolate=False), **os.environ}
        return cls(
            model_id=(values.get("BEDROCK_MODEL_ID") or "").strip() or ALLOWED_MODEL_IDS[0],
            region=(values.get("AWS_REGION") or "").strip()
            or (values.get("AWS_DEFAULT_REGION") or "").strip()
            or "us-east-1",
            profile=(values.get("AWS_PROFILE") or "").strip() or None,
        )


class ConverseRuntime(Protocol):
    def converse(self, **kwargs: Any) -> dict[str, Any]: ...

    def converse_stream(self, **kwargs: Any) -> dict[str, Any]: ...


@dataclass
class BedrockClient:
    settings: BedrockSettings
    runtime: ConverseRuntime

    @classmethod
    def from_env(cls, env_file: str | Path = ".env") -> "BedrockClient":
        settings = BedrockSettings.from_env(env_file)
        session = boto3.Session(profile_name=settings.profile, region_name=settings.region)
        return cls(settings=settings, runtime=session.client("bedrock-runtime"))

    def converse(self, messages: list[dict[str, Any]], **options: Any) -> dict[str, Any]:
        """Forward Converse messages/options, preserving tool-use responses.

        AWS errors propagate to the future agent loop; no domain answer is
        fabricated on failure. The configured model cannot be overridden here.
        """
        if "modelId" in options:
            raise ValueError("Configure el modelo mediante BEDROCK_MODEL_ID.")
        return self.runtime.converse(modelId=self.settings.model_id, messages=messages, **options)

    def converse_stream(self, messages: list[dict[str, Any]], **options: Any) -> dict[str, Any]:
        """Forward incremental Converse output using the configured model."""
        if "modelId" in options:
            raise ValueError("Configure el modelo mediante BEDROCK_MODEL_ID.")
        return self.runtime.converse_stream(
            modelId=self.settings.model_id, messages=messages, **options
        )
