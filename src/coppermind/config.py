"""
Settings for Copper, read from environment variables with sensible defaults.
"""

import os
from dataclasses import dataclass
from pathlib import Path

DEFAULT_BASE_URL = "http://localhost:11434/v1"
DEFAULT_MODEL = "qwen3:4b-instruct"
DEFAULT_TIMEOUT_SECONDS = 120.0
# How many tokens the model can see at once. Ollama's OpenAI-compatible endpoint can't
# change this per request, so set it to match what `ollama ps` reports for the model.
DEFAULT_CONTEXT_WINDOW = 4096

# The repo root, found from this file's location: src/coppermind/config.py -> parents[2].
# This only points at the repo when Copper is installed in editable mode (pip install -e .).
REPO_ROOT = Path(__file__).resolve().parents[2]

# The only folder the file tools can change. It's always the repo's sandbox/notes,
# no matter which directory `copper` is run from.
NOTES_DIR = REPO_ROOT / "sandbox" / "notes"

# Long-term memory lives in the user's home folder, outside the repo, so personal
# facts never get committed and it works however Copper is installed.
MEMORY_FILE = Path.home() / ".copper" / "memory.md"

# Token usage log: one JSON line per model call, kept across sessions.
USAGE_FILE = Path.home() / ".copper" / "usage.jsonl"


# frozen=True with a dataclass makes its instances immutable.
# You cannot modify or delete the attributes once it is initialized.
@dataclass(frozen=True)
class Settings:
    base_url: str
    model: str
    timeout: float
    notes_dir: Path
    context_window: int


# Create configuration settings for the model to use
# This makes it so that changing the backend is just changing a variable
def load_settings() -> Settings:
    """Build settings from COPPER_* environment variables, falling back to defaults."""
    return Settings(
        base_url=os.environ.get("COPPER_BASE_URL", DEFAULT_BASE_URL).rstrip("/"),
        model=os.environ.get("COPPER_MODEL", DEFAULT_MODEL),
        timeout=float(os.environ.get("COPPER_TIMEOUT", DEFAULT_TIMEOUT_SECONDS)),
        notes_dir=NOTES_DIR,
        context_window=int(os.environ.get("COPPER_CONTEXT_WINDOW", DEFAULT_CONTEXT_WINDOW)),
    )
