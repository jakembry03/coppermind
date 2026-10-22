"""Command-line entry point for Copper.

Everything the user types and sees goes through this module. It should
stay thin: read input, call into the core, display results. No agent
logic lives here.
"""

from coppermind.conversation import Conversation
from coppermind.llm import LLMError

GREETING = "Hi, my name is Copper. How can I help you?"
INPUT_PROMPT = "> "
QUIT_COMMANDS = {"/quit", "/exit"}


def main() -> int:
    """Entry point for the `copper` command. Returns the process exit code."""
    print(GREETING)
    return repl(Conversation())


def repl(conversation: Conversation) -> int:
    """Read-eval-print loop: read a line, send it to Copper, print the reply."""
    while True:
        try:
            text = input(INPUT_PROMPT).strip()
        except (EOFError, KeyboardInterrupt):
            print()
            return 0

        if not text:
            continue
        if text in QUIT_COMMANDS:
            return 0
        if text == "/clear":
            conversation.clear()
            print("(conversation cleared)")
            continue
        if text.startswith("/"):
            print(f"Unknown command: {text}. Try /clear or /quit.")
            continue

        try:
            reply = conversation.send(text)
        except LLMError as error:
            print(f"Error: {error}")
            continue
        except KeyboardInterrupt:
            print("\n(interrupted)")
            continue

        print(reply)