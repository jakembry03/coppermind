import pytest

from coppermind import cli
from coppermind.agent import AgentError
from coppermind.llm import LLMError


class FakeAgent:
    """Stands in for Agent so CLI tests never touch the model."""

    def __init__(self, replies=None, error=None):
        self.replies = list(replies or [])
        self.error = error
        self.sent = []
        self.cleared = False

    def send(self, text):
        self.sent.append(text)
        if self.error:
            raise self.error
        return self.replies.pop(0)

    def clear(self):
        self.cleared = True


def feed_input(monkeypatch, lines):
    """Make input() return each line in turn, then act like Ctrl-D / Ctrl-Z (EOF)."""
    remaining = iter(lines)

    def fake_input(prompt=""):
        try:
            return next(remaining)
        except StopIteration:
            raise EOFError from None

    monkeypatch.setattr("builtins.input", fake_input)


def use_fake_agent(monkeypatch, fake):
    """Make main() use our fake instead of building a real Agent."""
    monkeypatch.setattr(cli, "Agent", lambda *args, **kwargs: fake)


def test_main_greets_then_quits(monkeypatch, capsys):
    use_fake_agent(monkeypatch, FakeAgent())
    feed_input(monkeypatch, ["/quit"])

    exit_code = cli.main([])

    assert cli.GREETING in capsys.readouterr().out
    assert exit_code == 0


def test_main_gives_the_agent_every_tool(monkeypatch):
    captured = {}

    def fake_agent_factory(registry, **kwargs):
        captured["registry"] = registry
        return FakeAgent()

    monkeypatch.setattr(cli, "Agent", fake_agent_factory)
    feed_input(monkeypatch, ["/quit"])

    cli.main([])

    assert set(captured["registry"]) == {
        "list_files",
        "list_folders", 
        "read_file", 
        "get_current_datetime", 
        "write_to_file", 
        "append_to_file", 
        "create_file",
        "delete_file",
    }


def test_repl_sends_message_and_prints_reply(monkeypatch, capsys):
    agent = FakeAgent(replies=["The capital of Spain is Madrid."])
    feed_input(monkeypatch, ["What is the capital of Spain?"])

    cli.repl(agent)

    assert agent.sent == ["What is the capital of Spain?"]
    assert "The capital of Spain is Madrid." in capsys.readouterr().out


def test_repl_ignores_blank_lines(monkeypatch):
    agent = FakeAgent()
    feed_input(monkeypatch, ["", "   "])

    cli.repl(agent)

    assert agent.sent == []


def test_clear_command_clears_history(monkeypatch):
    agent = FakeAgent()
    feed_input(monkeypatch, ["/clear"])

    cli.repl(agent)

    assert agent.cleared


def test_unknown_command_is_not_sent_to_model(monkeypatch, capsys):
    agent = FakeAgent()
    feed_input(monkeypatch, ["/qiut"])

    cli.repl(agent)

    assert agent.sent == []
    assert "Unknown command" in capsys.readouterr().out


@pytest.mark.parametrize(
    "error",
    [LLMError("Is Ollama running?"), AgentError("Copper gave up after 10 tool steps.")],
)
def test_repl_prints_errors_and_keeps_going(monkeypatch, capsys, error):
    agent = FakeAgent(error=error)
    feed_input(monkeypatch, ["hello"])

    exit_code = cli.repl(agent)

    assert f"Error: {error}" in capsys.readouterr().err
    assert exit_code == 0


def test_one_shot_prints_only_the_reply(monkeypatch, capsys):
    fake = FakeAgent(replies=["The capital of Spain is Madrid."])
    use_fake_agent(monkeypatch, fake)

    exit_code = cli.main(["-p", "What is the capital of Spain?"])

    output = capsys.readouterr().out
    assert output.strip() == "The capital of Spain is Madrid."
    assert cli.GREETING not in output
    assert fake.sent == ["What is the capital of Spain?"]
    assert exit_code == 0


def test_long_prompt_flag_works(monkeypatch):
    fake = FakeAgent(replies=["Madrid."])
    use_fake_agent(monkeypatch, fake)

    cli.main(["--prompt", "Capital of Spain?"])

    assert fake.sent == ["Capital of Spain?"]


@pytest.mark.parametrize(
    "error",
    [LLMError("Is Ollama running?"), AgentError("Copper gave up after 10 tool steps.")],
)
def test_one_shot_error_goes_to_stderr_with_exit_code_1(monkeypatch, capsys, error):
    use_fake_agent(monkeypatch, FakeAgent(error=error))

    exit_code = cli.main(["-p", "hello"])

    captured = capsys.readouterr()
    assert captured.out == ""
    assert str(error) in captured.err
    assert exit_code == 1


def test_empty_prompt_is_rejected(monkeypatch):
    use_fake_agent(monkeypatch, FakeAgent())

    with pytest.raises(SystemExit) as exit_info:
        cli.main(["-p", "   "])

    assert exit_info.value.code == 2


def test_version_flag(capsys):
    with pytest.raises(SystemExit) as exit_info:
        cli.main(["--version"])

    assert exit_info.value.code == 0
    assert capsys.readouterr().out.startswith("copper ")