from datetime import datetime

from coppermind.tools.base import Tool

from pathlib import Path

MEMORY_FILE = Path(__file__).parent.parent / "memory" / "memory.md"

def get_current_datetime() -> str:
    now = datetime.now().astimezone()
    return now.strftime("%A, %Y-%m-%d %H:%M:%S (UTC%z)")


def save_memory(fact: str) -> str:
    """Append one fact about the user to long-term memory."""
    with MEMORY_FILE.open("a", encoding="utf-8") as f:
        f.write(f"- {fact}\n")
    return f"saved: {fact}"


def core_tools() -> list[Tool]:
    return [
        Tool(
            name="get_current_datetime",
            description="Get the current local date, time, weekday, and UTC offset.",
            parameters={"type": "object", "properties": {}, "required": []},
            function=get_current_datetime,
            group="core",
            writes=False,
        ),
        Tool(
            name="save_memory",
            description=(
                "Save a lasting fact about Jake for future conversations:"
                "preferences, projects, people, decisions, or anything he asks you to remember."
                "Skip small talk, one-time requests, guesses, secrets, and facts you already know."
            ),
            parameters={
                "type": "object",
                "properties": {
                    "fact": {
                        "type": "string",
                        "description": (
                            "One short sentence about Jake that makes sense on its own."
                            "e.g. 'Prefers dark mode in code editors.'"
                        ),
                    }
                },
                "required": ["fact"],
            },
            function=save_memory,
            group="core",
            writes=True,
        ),
    ]