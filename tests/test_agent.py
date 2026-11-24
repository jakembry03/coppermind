import json
import logging

import pytest

from coppermind import agent as agent_module
from coppermind import config
from coppermind.agent import Agent
from coppermind.llm import ChatReply
from coppermind.tools.base import Tool
from coppermind.tools.core import load_memory, save_memory


def make_tool(function, name="boom"):
    """A one-off tool in the core group, with a single `text` parameter."""
    return Tool(
        name=name,
        description="A test tool.",
        parameters={"type": "object", "properties": {"text": {"type": "string"}}},
        function=function,
        group="core",
    )


def tool_call(name="boom", **arguments):
    """A tool call shaped the way the model server sends it."""
    return {"id": "call_1", "function": {"name": name, "arguments": json.dumps(arguments)}}


def model_reply(message):
    """Wrap a message the way llm.chat returns it, with no usage numbers."""
    return ChatReply(message=message, usage=None)


def use_temp_memory(monkeypatch, tmp_path):
    """Point long-term memory at a temp file so tests never touch the real one."""
    memory = tmp_path / "copper" / "memory.md"
    monkeypatch.setattr(config, "MEMORY_FILE", memory)
    return memory


def test_load_memory_is_empty_before_anything_is_saved(monkeypatch, tmp_path):
    use_temp_memory(monkeypatch, tmp_path)
    assert load_memory() == ""


def test_save_memory_creates_the_file_and_keeps_one_fact_per_line(monkeypatch, tmp_path):
    memory = use_temp_memory(monkeypatch, tmp_path)

    save_memory("Likes\ncoffee")
    save_memory("Has a dog")

    assert memory.read_text(encoding="utf-8") == "- Likes coffee\n- Has a dog\n"


def test_new_memories_reach_the_model_on_the_next_message(monkeypatch, tmp_path):
    use_temp_memory(monkeypatch, tmp_path)
    seen_prompts = []

    def fake_chat(messages, tools=None, settings=None):
        seen_prompts.append(messages[0]["content"])
        return model_reply({"role": "assistant", "content": "ok"})

    monkeypatch.setattr(agent_module.llm, "chat", fake_chat)
    agent = Agent(registry={})

    agent.send("hello")
    save_memory("Favorite color is green.")
    agent.send("what's my favorite color?")

    assert "Favorite color is green." not in seen_prompts[0]
    assert "Favorite color is green." in seen_prompts[1]


def test_a_fixed_system_prompt_is_never_replaced(monkeypatch, tmp_path):
    use_temp_memory(monkeypatch, tmp_path)
    monkeypatch.setattr(
        agent_module.llm,
        "chat",
        lambda *a, **k: model_reply({"role": "assistant", "content": "ok"}),
    )
    agent = Agent(registry={}, system_prompt="test prompt")

    agent.send("hello")

    assert agent.messages[0] == {"role": "system", "content": "test prompt"}


# --- Unexpected tool errors -------------------------------------------------

def crash(text):
    raise ValueError("the server sent garbage")


def test_a_crashing_tool_becomes_an_error_message(caplog):
    agent = Agent(registry={"boom": make_tool(crash)}, system_prompt="s")

    with caplog.at_level(logging.ERROR):
        result = agent.run_tool_call(tool_call(text="hi"))

    assert result == "Error: boom failed unexpectedly (ValueError: the server sent garbage)"
    # The full traceback is logged for the developer, not just the short message.
    assert "Tool boom crashed" in caplog.text
    assert "Traceback" in caplog.text


def test_a_type_error_inside_a_tool_is_not_called_wrong_arguments():
    def buggy(text):
        return text + 1  # TypeError: can only concatenate str to str

    agent = Agent(registry={"boom": make_tool(buggy)}, system_prompt="s")

    result = agent.run_tool_call(tool_call(text="hi"))

    assert result.startswith("Error: boom failed unexpectedly (TypeError")


@pytest.mark.parametrize("arguments", [{}, {"text": "hi", "extra": 1}, {"wrong": "hi"}])
def test_bad_arguments_from_the_model_are_called_wrong_arguments(arguments):
    agent = Agent(registry={"boom": make_tool(lambda text: text)}, system_prompt="s")

    assert agent.run_tool_call(tool_call(**arguments)) == "Error: wrong arguments for boom"


def test_ctrl_c_still_interrupts_a_tool_and_rolls_back_the_turn(monkeypatch):
    def slow(text):
        raise KeyboardInterrupt

    replies = iter([
        model_reply({"role": "assistant", "content": None, "tool_calls": [tool_call(text="hi")]}),
    ])
    monkeypatch.setattr(agent_module.llm, "chat", lambda *a, **k: next(replies))
    agent = Agent(registry={"boom": make_tool(slow)}, system_prompt="s")

    with pytest.raises(KeyboardInterrupt):
        agent.send("hello")

    assert agent.messages == [{"role": "system", "content": "s"}]


def test_the_model_hears_about_the_crash_and_the_turn_carries_on(monkeypatch):
    sent = []
    replies = iter([
        model_reply({"role": "assistant", "content": None, "tool_calls": [tool_call(text="hi")]}),
        model_reply({"role": "assistant", "content": "Sorry, that tool is broken."}),
    ])

    def fake_chat(messages, tools=None, settings=None):
        sent.append(list(messages))
        return next(replies)

    monkeypatch.setattr(agent_module.llm, "chat", fake_chat)
    agent = Agent(registry={"boom": make_tool(crash)}, system_prompt="s")

    assert agent.send("hello") == "Sorry, that tool is broken."
    tool_message = sent[1][-1]
    assert tool_message["role"] == "tool"
    assert tool_message["tool_call_id"] == "call_1"
    assert "failed unexpectedly" in tool_message["content"]
