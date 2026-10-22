"""Command-line entry point for Copper.

Everything the user types and sees goes through this module. It should
stay thin: read input, call into the core, display results. No agent
logic lives here.
"""
import argparse
import sys
from importlib.metadata import version

from coppermind.conversation import Conversation
from coppermind.llm import LLMError

GREETING = "Hi, my name is Copper. How can I help you?"
INPUT_PROMPT = "> "
QUIT_COMMANDS = {"/quit", "/exit"}

EXIT_OK = 0
EXIT_ERROR = 1
EXIT_INTERRUPTED = 130

def build_parser() -> argparse.ArgumentParser:
    """Define the command-line options for `copper`."""
    parser = argparse.ArgumentParser(
        prog="copper",
        description="Copper: a personal AI assistant running on local models.",
        epilog="Run with no options to start an interactive conversation.",
    )
    parser.add_argument(
        "-p",
        "--prompt",
        metavar="TEXT",
        help="send one message, print the reply, and exit",
    )
    parser.add_argument(
        "--version",
        action="version",
        version=f"%(prog)s {version('coppermind')}",
    )
    return parser


def main(argv: list[str] | None = None) -> int:
    """Entry point for the `copper` command. Returns the process exit code."""
    parser = build_parser()
    args = parser.parse_args(argv)
    conversation = Conversation()

    if args.prompt is not None:
        text = args.prompt.strip()
        if not text:
            parser.error("the prompt can't be empty")
        return one_shot(conversation, text)

    print(GREETING)
    return repl(conversation)

def one_shot(conversation: Conversation, text: str) -> int:
    """Send a single message, print the reply, and return the exit code."""
    try:
        reply = conversation.send(text)
    except LLMError as error:
        print(f"Error: {error}", file=sys.stderr)
        return EXIT_ERROR
    except KeyboardInterrupt:
        print("(interrupted)", file=sys.stderr)
        return EXIT_INTERRUPTED

    print(reply)
    return EXIT_OK


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