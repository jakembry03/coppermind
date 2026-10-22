from coppermind import llm
from coppermind.conversation import Conversation, load_system_prompt


def fake_chat_replying(text, calls):
    """Stand-in for llm.chat that records what it was sent and replies with `text`."""

    def fake_chat(messages, tools=None, settings=None):
        calls.append(list(messages))
        return {"role": "assistant", "content": text}

    return fake_chat


def test_system_prompt_ships_with_the_package():
    assert "Copper" in load_system_prompt()


def test_new_conversation_contains_only_the_system_prompt():
    conversation = Conversation(system_prompt="test prompt")

    assert conversation.messages == [{"role": "system", "content": "test prompt"}]


def test_send_records_both_sides_and_returns_reply(monkeypatch):
    calls = []
    monkeypatch.setattr(llm, "chat", fake_chat_replying("Hi Jake!", calls))
    conversation = Conversation(system_prompt="test prompt")

    reply = conversation.send("I'm Jake")

    assert reply == "Hi Jake!"
    assert conversation.messages[1:] == [
        {"role": "user", "content": "I'm Jake"},
        {"role": "assistant", "content": "Hi Jake!"},
    ]


def test_each_call_resends_the_full_history(monkeypatch):
    calls = []
    monkeypatch.setattr(llm, "chat", fake_chat_replying("ok", calls))
    conversation = Conversation(system_prompt="test prompt")

    conversation.send("first")
    conversation.send("second")

    second_call = calls[1]
    assert [m["content"] for m in second_call] == ["test prompt", "first", "ok", "second"]


def test_clear_keeps_only_the_system_prompt(monkeypatch):
    monkeypatch.setattr(llm, "chat", fake_chat_replying("ok", []))
    conversation = Conversation(system_prompt="test prompt")
    conversation.send("hello")

    conversation.clear()

    assert conversation.messages == [{"role": "system", "content": "test prompt"}]


def test_failed_send_leaves_history_unchanged(monkeypatch):
    def failing_chat(messages, tools=None, settings=None):
        raise llm.LLMError("server down")

    monkeypatch.setattr(llm, "chat", failing_chat)
    conversation = Conversation(system_prompt="test prompt")

    try:
        conversation.send("hello")
    except llm.LLMError:
        pass

    assert conversation.messages == [{"role": "system", "content": "test prompt"}]