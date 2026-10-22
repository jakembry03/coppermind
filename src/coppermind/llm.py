"""
Client for the model server.

This is the only module that knows how to talk to the model. It speaks the OpenAI-Compatible
chat completions API, which Ollama, llama.cpp's server, and LM Studio all support, so changing
backends is a config change, not a rewrite.
"""

from typing import Any

import httpx

from coppermind.config import Settings, load_settings

Message = dict[str, Any]


class LLMError(Exception):
    """The model server couldn't be reached or returned something unusable."""


def chat(
    messages: list[Message],
    tools: list[dict[str, Any]] | None = None,
    settings: Settings | None = None,
) -> Message:
    """
    Send a conversation to the model and return its reply message.

    The reply has the same shape as the messages sent in, e.g.
    {"role": "assistant", "content": "..."}, so callers can append it
    straight to the conversation.
    """
    settings = settings or load_settings()

    payload: dict[str, Any] = {"model": settings.model, "messages": messages}
    if tools:
        payload["tools"] = tools

    url = f"{settings.base_url}/chat/completions"

    try:
        response = httpx.post(url, json=payload, timeout=settings.timeout)
        response.raise_for_status()
    except httpx.ConnectError as exc:
        raise LLMError(
            f"Can't reach the model server at {settings.base_url}. Is Ollama running?"
        ) from exc
    except httpx.TimeoutException as exc:
        raise LLMError(
            f"The model server didn't respond within {settings.timeout:.0f} seconds."
        ) from exc
    except httpx.HTTPStatusError as exc:
        raise LLMError(
            f"The model server returned HTTP {exc.response.status_code}: {exc.response.text[:200]}"
        ) from exc

    try:
        return response.json()["choices"][0]["message"]
    except (ValueError, KeyError, IndexError) as exc:
        raise LLMError("The model server returned a response Copper couldn't read.") from exc
