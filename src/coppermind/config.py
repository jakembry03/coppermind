"""
Settings for Copper, read from environment variables with sensible defaults.
"""

import os
from dataclasses import dataclass
from pathlib import Path

DEFAULT_BASE_URL = "http://localhost:11434/v1"
DEFAULT_MODEL = "qwen3:8b"
DEFAULT_TIMEOUT_SECONDS = 120.0
COPPER_NOTES_DIR = "sandbox/notes"

# frozen=True with a dataclass makes its instances immutable.
# You cannot modify or delete the attributes once it is initialized.
@dataclass(frozen=True)
class Settings:
    base_url: str
    model: str
    timeout: float
    notes_dir: Path


# Create configuration settings for the model to use
# This makes it so that changing the backend is just changing a variable
def load_settings() -> Settings:
    """Build settings from COPPER_* environment variables, falling back to defaults."""
    return Settings(
        base_url=os.environ.get("COPPER_BASE_URL", DEFAULT_BASE_URL).rstrip("/"),
        model=os.environ.get("COPPER_MODEL", DEFAULT_MODEL),
        timeout=float(os.environ.get("COPPER_TIMEOUT", DEFAULT_TIMEOUT_SECONDS)),
        notes_dir=Path(os.environ.get("COPPER_NOTES_DIR", COPPER_NOTES_DIR)),
    )
