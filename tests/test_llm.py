import httpx
import pytest

from pathlib import Path

from coppermind import llm
from coppermind.config import Settings

TEST_SETTINGS = Settings(
    base_url="http://localhost:11434/v1", 
    model="qwen3:4b-instruct", 
    timeout=5.0,
    notes_dir=Path("sandbox/notes")
)
USER_MESSAGE = [{"role": "user", "content": "What is the capital of Spain?"}]


def fake_post_returning(status_code, body, captured=None):
    """Build a stand-in for httpx.post that returns a canned response."""

    def fake_post(url, json, timeout):
        if captured is not None:
            captured.update(url=url, json=json)
        request = httpx.Request("POST", url)
        return httpx.Response(status_code, json=body, request=request)

    return fake_post


def test_chat_returns_assistant_message(monkeypatch):
    body = {"choices": [{"message": {"role": "assistant", "content": "Madrid."}}]}
    monkeypatch.setattr(llm.httpx, "post", fake_post_returning(200, body))

    reply = llm.chat(USER_MESSAGE, settings=TEST_SETTINGS)

    assert reply == {"role": "assistant", "content": "Madrid."}


def test_chat_sends_model_and_messages_to_the_right_url(monkeypatch):
    captured = {}
    body = {"choices": [{"message": {"role": "assistant", "content": "Madrid."}}]}
    monkeypatch.setattr(llm.httpx, "post", fake_post_returning(200, body, captured))

    llm.chat(USER_MESSAGE, settings=TEST_SETTINGS)

    assert captured["url"] == "http://localhost:11434/v1/chat/completions"
    assert captured["json"] == {"model": "qwen3:4b-instruct", "messages": USER_MESSAGE}


def test_chat_explains_when_server_is_down(monkeypatch):
    def fake_post(url, json, timeout):
        raise httpx.ConnectError("connection refused")

    monkeypatch.setattr(llm.httpx, "post", fake_post)

    with pytest.raises(llm.LLMError, match="Is Ollama running"):
        llm.chat(USER_MESSAGE, settings=TEST_SETTINGS)


def test_chat_reports_http_errors(monkeypatch):
    monkeypatch.setattr(llm.httpx, "post", fake_post_returning(404, {"error": "model not found"}))

    with pytest.raises(llm.LLMError, match="HTTP 404"):
        llm.chat(USER_MESSAGE, settings=TEST_SETTINGS)


def test_chat_rejects_unexpected_response_shape(monkeypatch):
    monkeypatch.setattr(llm.httpx, "post", fake_post_returning(200, {"unexpected": True}))

    with pytest.raises(llm.LLMError, match="couldn't read"):
        llm.chat(USER_MESSAGE, settings=TEST_SETTINGS)
