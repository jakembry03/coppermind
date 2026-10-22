from coppermind import cli
from coppermind.llm import LLMError


class FakeConversation:
    """Stands in for Conversation so CLI tests never touch the model."""

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
    """Make input() return each line in turn, then act like Ctrl-Z/Ctrl-D (EOF)."""
    remaining = iter(lines)

    def fake_input(prompt=""):
        try:
            return next(remaining)
        except StopIteration:
            raise EOFError from None

    monkeypatch.setattr("builtins.input", fake_input)


def test_main_greets_then_quits(monkeypatch, capsys):
    monkeypatch.setattr(cli, "Conversation", FakeConversation)
    feed_input(monkeypatch, ["/quit"])

    exit_code = cli.main()

    assert cli.GREETING in capsys.readouterr().out
    assert exit_code == 0


def test_repl_sends_message_and_prints_reply(monkeypatch, capsys):
    conversation = FakeConversation(replies=["The capital of Spain is Madrid."])
    feed_input(monkeypatch, ["What is the capital of Spain?"])

    cli.repl(conversation)

    assert conversation.sent == ["What is the capital of Spain?"]
    assert "The capital of Spain is Madrid." in capsys.readouterr().out


def test_repl_ignores_blank_lines(monkeypatch):
    conversation = FakeConversation()
    feed_input(monkeypatch, ["", "   "])

    cli.repl(conversation)

    assert conversation.sent == []


def test_clear_command_clears_conversation(monkeypatch):
    conversation = FakeConversation()
    feed_input(monkeypatch, ["/clear"])

    cli.repl(conversation)

    assert conversation.cleared


def test_unknown_command_is_not_sent_to_model(monkeypatch, capsys):
    conversation = FakeConversation()
    feed_input(monkeypatch, ["/qiut"])

    cli.repl(conversation)

    assert conversation.sent == []
    assert "Unknown command" in capsys.readouterr().out


def test_model_errors_are_printed_and_repl_keeps_going(monkeypatch, capsys):
    conversation = FakeConversation(error=LLMError("Is Ollama running?"))
    feed_input(monkeypatch, ["hello"])

    exit_code = cli.repl(conversation)

    assert "Error: Is Ollama running?" in capsys.readouterr().out
    assert exit_code == 0