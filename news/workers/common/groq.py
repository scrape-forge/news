"""Small reusable client for Groq JSON chat completions."""

from dataclasses import dataclass, field
import json
from typing import Any

import requests


GROQ_API_URL = "https://api.groq.com/openai/v1/chat/completions"
DEFAULT_MODEL = "llama-3.1-8b-instant"


@dataclass(frozen=True)
class GroqResult:
    content: Any = None
    status_code: int | None = None
    usage: dict[str, int] = field(default_factory=dict)
    remaining_tokens: int | None = None
    remaining_requests: int | None = None
    retry_after: int | None = None
    error: str | None = None


def _optional_int(value: object) -> int | None:
    try:
        return int(value) if value is not None else None
    except (TypeError, ValueError):
        return None


def _parse_json_content(content: str):
    try:
        return json.loads(content)
    except ValueError as original_error:
        candidates = (
            (content.find("{"), content.rfind("}")),
            (content.find("["), content.rfind("]")),
        )
        for start, end in candidates:
            if start == -1 or end <= start:
                continue
            try:
                return json.loads(content[start:end + 1])
            except ValueError:
                continue
        raise original_error


def request_json_completion(
    *,
    api_key: str,
    messages: list[dict[str, str]],
    model: str = DEFAULT_MODEL,
    temperature: float = 0.1,
    timeout: int = 8,
    max_tokens: int | None = None,
    response_format: dict[str, str] | None = None,
) -> GroqResult:
    payload: dict[str, Any] = {
        "model": model,
        "messages": messages,
        "temperature": temperature,
    }
    if max_tokens is not None:
        payload["max_tokens"] = max_tokens
    if response_format is not None:
        payload["response_format"] = response_format

    try:
        response = requests.post(
            GROQ_API_URL,
            headers={
                "Authorization": f"Bearer {api_key}",
                "Content-Type": "application/json",
            },
            json=payload,
            timeout=timeout,
        )
    except requests.RequestException as exc:
        return GroqResult(error=str(exc))

    remaining_tokens = _optional_int(
        response.headers.get("x-ratelimit-remaining-tokens")
    )
    remaining_requests = _optional_int(
        response.headers.get("x-ratelimit-remaining-requests")
    )

    if response.status_code == 429:
        return GroqResult(
            status_code=429,
            remaining_tokens=remaining_tokens,
            remaining_requests=remaining_requests,
            retry_after=_optional_int(response.headers.get("Retry-After")),
            error="rate limited",
        )

    if response.status_code != 200:
        return GroqResult(
            status_code=response.status_code,
            remaining_tokens=remaining_tokens,
            remaining_requests=remaining_requests,
            error=response.text[:200],
        )

    try:
        response_data = response.json()
        content = response_data["choices"][0]["message"]["content"].strip()
        parsed_content = _parse_json_content(content)
    except (KeyError, IndexError, TypeError, ValueError) as exc:
        return GroqResult(
            status_code=200,
            remaining_tokens=remaining_tokens,
            remaining_requests=remaining_requests,
            error=f"invalid JSON response: {exc}",
        )

    return GroqResult(
        content=parsed_content,
        status_code=200,
        usage=response_data.get("usage", {}),
        remaining_tokens=remaining_tokens,
        remaining_requests=remaining_requests,
    )
