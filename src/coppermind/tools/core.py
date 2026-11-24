from datetime import datetime

from coppermind import config
from coppermind.tools.base import Tool


def get_current_datetime() -> str:
    now = datetime.now().astimezone()
    return now.strftime("%A, %Y-%m-%d %H:%M:%S (UTC%z)")


# Both memory functions look up config.MEMORY_FILE when they run (not at import),
# so tests can point it at a temporary file with monkeypatch.
def load_memory() -> str:
    """Read the saved facts about the user, or "" if nothing has been saved yet."""
    if not config.MEMORY_FILE.exists():
        return ""
    return config.MEMORY_FILE.read_text(encoding="utf-8")


def save_memory(fact: str) -> str:
    """Append one fact about the user to long-term memory."""
    # Keep each fact on one line so memory.md stays a clean bullet list.
    fact = " ".join(fact.split())
    config.MEMORY_FILE.parent.mkdir(parents=True, exist_ok=True)
    with config.MEMORY_FILE.open("a", encoding="utf-8") as f:
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
                "Save a lasting fact about Jake for future conversations: preferences, projects, people, decisions, or anything he asks you to remember. "
                "Skip small talk, one-time requests, guesses, secrets, and facts you already know."
            ),
            parameters={
                "type": "object",
                "properties": {
                    "fact": {
                        "type": "string",
                        "description": (
                            "One short sentence about Jake that makes sense on its own, "
                            "e.g. 'Prefers dark mode in code editors.'"
                        ),
                    }
                },
                "required": ["fact"],
            },
            function=lambda fact: save_memory(fact),
            group="core",
            writes=True,
        ),
    ]