"""
A conversation with Copper: the message history and how to add to it.

The model has no memory of its own. Every call sends the full history, so "remembering" a conversation just means keeping
this list and resending it.
"""

from importlib.resources import files

from coppermind import llm
from coppermind.config import Settings
from coppermind.llm import Message


def load_system_prompt() -> str:
    """Read the system prompt that ships inside the coppermind package."""
    return (files("coppermind") / "prompts" / "system.md").read_text(encoding="utf-8")


class Conversation:
    """The running message history for one chat session."""

    def __init__(self, settings: Settings | None = None, system_prompt: str | None = None) -> None:
        self.settings = settings
        self.system_prompt = system_prompt if system_prompt is not None else load_system_prompt()
        self.messages: list[Message] = []
        self.clear()

    def clear(self) -> None:
        """Forget the conversation, keeping only the system prompt."""
        self.messages = [{"role": "system", "content": self.system_prompt}]

    def send(self, text: str) -> str:
        """
        Add the user's message, get Copper's reply, record it, and return its text.

        If the call fails for any reason (server down, Ctrl + C), the user's message
        is removed again so the history never hsa a question without an answer.
        """
        self.messages.append({"role": "user", "content": text})
        try:
            reply = llm.chat(self.messages, settings=self.settings)
        except BaseException:
            self.messages.pop()
            raise
        self.messages.append(reply)
        return reply.get("content") or ""
