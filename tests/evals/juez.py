"""Juez DeepEval sobre la misma superficie Bedrock del agente."""

import asyncio
import json

from deepeval.models import DeepEvalBaseLLM

from src.agent.bedrock import BedrockClient, BedrockSettings


class BedrockJudge(DeepEvalBaseLLM):
    def load_model(self):
        client = BedrockClient.from_env()
        if client.settings.model_id != BedrockSettings().model_id:
            raise ValueError("El juez requiere us.anthropic.claude-sonnet-5")
        return client

    def get_model_name(self):
        return "us.anthropic.claude-sonnet-5"

    def generate(self, prompt, schema=None):
        if schema is not None:
            prompt += (
                "\nReturn ONLY a valid JSON object matching this schema. "
                "Do not use XML or markdown. Include every required property.\n"
                + json.dumps(schema.model_json_schema())
            )
        for attempt in range(3):
            result = self.model.converse(
                [{"role": "user", "content": [{"text": prompt}]}],
                inferenceConfig={"maxTokens": 3000},
            )
            text = "\n".join(
                c["text"] for c in result["output"]["message"]["content"] if "text" in c
            )
            if schema is None:
                return text
            try:
                begin, end = text.index("{"), text.rindex("}") + 1
                return schema.model_validate_json(text[begin:end])
            except ValueError:
                if attempt == 2:
                    raise
                prompt += "\nInvalid previous answer. Return valid JSON with every required field."

    async def a_generate(self, prompt, schema=None):
        return await asyncio.to_thread(self.generate, prompt, schema)
