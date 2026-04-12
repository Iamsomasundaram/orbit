from __future__ import annotations

import asyncio
import json
import time
from dataclasses import dataclass
from pathlib import Path
from typing import Protocol, TypeVar

from openai import AsyncOpenAI
from pydantic import BaseModel

T = TypeVar("T", bound=BaseModel)


class LLMProviderError(RuntimeError):
    pass


class UnsupportedLLMProviderError(LLMProviderError):
    pass


@dataclass(frozen=True)
class InferenceTelemetry:
    duration_ms: int
    input_tokens: int = 0
    output_tokens: int = 0
    total_tokens: int = 0
    estimated_cost_usd: float = 0.0


class StructuredLLMProvider(Protocol):
    provider_name: str
    model_name: str

    async def infer_structured(
        self,
        *,
        system_prompt: str,
        user_prompt: str,
        response_model: type[T],
        timeout_seconds: int,
        max_output_tokens: int,
    ) -> tuple[T, InferenceTelemetry]: ...


def resolve_api_key(explicit_api_key: str, api_key_file: str) -> str:
    if explicit_api_key.strip():
        return explicit_api_key.strip()
    file_path = Path(api_key_file)
    if file_path.exists() and file_path.is_file():
        return file_path.read_text(encoding="utf-8").strip()
    return ""


def _response_output_text(response: object) -> str:
    output_text = getattr(response, "output_text", "")
    if isinstance(output_text, str) and output_text.strip():
        return output_text

    output_blocks = getattr(response, "output", None)
    if not isinstance(output_blocks, list):
        return ""

    collected: list[str] = []
    for block in output_blocks:
        content_blocks = getattr(block, "content", None)
        if not isinstance(content_blocks, list):
            continue
        for content in content_blocks:
            text_value = getattr(content, "text", None)
            if isinstance(text_value, str) and text_value:
                collected.append(text_value)
    return "".join(collected)


def _openai_usage_tokens(response: object) -> tuple[int, int, int]:
    usage = getattr(response, "usage", None)
    input_tokens = int(getattr(usage, "input_tokens", 0) or 0)
    output_tokens = int(getattr(usage, "output_tokens", 0) or 0)
    total_tokens = int(getattr(usage, "total_tokens", input_tokens + output_tokens) or (input_tokens + output_tokens))
    return input_tokens, output_tokens, total_tokens


def _openai_estimated_cost_usd(model_name: str, input_tokens: int, output_tokens: int) -> float:
    # Default rates follow the official gpt-4o-mini model page.
    if model_name.startswith("gpt-4o-mini"):
        input_rate_per_million = 0.15
        output_rate_per_million = 0.60
    else:
        return 0.0
    estimated_cost = ((input_tokens / 1_000_000) * input_rate_per_million) + ((output_tokens / 1_000_000) * output_rate_per_million)
    return round(estimated_cost, 8)


class OpenAIResponsesProvider:
    provider_name = "openai"

    def __init__(self, *, api_key: str, model_name: str) -> None:
        if not api_key:
            raise LLMProviderError("OPENAI_API_KEY is empty and OPENAI_API_KEY_FILE did not resolve to a usable key.")
        if not model_name:
            raise LLMProviderError("OPENAI_MODEL must be configured for llm runtime mode.")
        self.model_name = model_name
        self._client = AsyncOpenAI(api_key=api_key)

    async def infer_structured(
        self,
        *,
        system_prompt: str,
        user_prompt: str,
        response_model: type[T],
        timeout_seconds: int,
        max_output_tokens: int,
    ) -> tuple[T, InferenceTelemetry]:
        started = time.perf_counter()
        request_kwargs = {
            "model": self.model_name,
            "input": [
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": user_prompt},
            ],
            "text_format": response_model,
            "max_output_tokens": max_output_tokens,
            "temperature": 0,
        }
        try:
            response = await asyncio.wait_for(self._client.responses.parse(**request_kwargs), timeout=timeout_seconds)
        except TypeError:
            request_kwargs.pop("temperature", None)
            response = await asyncio.wait_for(self._client.responses.parse(**request_kwargs), timeout=timeout_seconds)
        except Exception as exc:
            raise LLMProviderError(f"OpenAI inference failed: {exc}") from exc

        parsed = getattr(response, "output_parsed", None)
        duration_ms = int((time.perf_counter() - started) * 1000)
        input_tokens, output_tokens, total_tokens = _openai_usage_tokens(response)
        telemetry = InferenceTelemetry(
            duration_ms=duration_ms,
            input_tokens=input_tokens,
            output_tokens=output_tokens,
            total_tokens=total_tokens,
            estimated_cost_usd=_openai_estimated_cost_usd(self.model_name, input_tokens, output_tokens),
        )
        if isinstance(parsed, response_model):
            return parsed, telemetry
        if parsed is not None:
            return response_model.model_validate(parsed), telemetry

        output_text = _response_output_text(response)
        if output_text.strip():
            try:
                return response_model.model_validate_json(output_text), telemetry
            except Exception:
                return response_model.model_validate(json.loads(output_text)), telemetry

        raise LLMProviderError("OpenAI response did not contain a structured payload.")


class AnthropicPlaceholderProvider:
    provider_name = "anthropic"

    def __init__(self, *, model_name: str) -> None:
        self.model_name = model_name

    async def infer_structured(
        self,
        *,
        system_prompt: str,
        user_prompt: str,
        response_model: type[T],
        timeout_seconds: int,
        max_output_tokens: int,
    ) -> tuple[T, InferenceTelemetry]:
        raise UnsupportedLLMProviderError("Anthropic provider support is reserved for a later milestone.")


class LocalPlaceholderProvider:
    provider_name = "local"

    def __init__(self, *, model_name: str) -> None:
        self.model_name = model_name

    async def infer_structured(
        self,
        *,
        system_prompt: str,
        user_prompt: str,
        response_model: type[T],
        timeout_seconds: int,
        max_output_tokens: int,
    ) -> tuple[T, InferenceTelemetry]:
        raise UnsupportedLLMProviderError("Local provider support is reserved for a later milestone.")
