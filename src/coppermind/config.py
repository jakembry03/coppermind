"""
Settings for Copper, read from environment variables with sensible defaults.
"""

import os
from dataclasses import dataclass

DEFAULT_BASE_URL = "http://localhost:11434/v1"
DEFAULT_MODEL = "qwen3:4b-instruct"
DEFAULT_TIMEOUT_SECONDS = 120.0


@dataclass(frozen=True)
class Settings:
    base_url: str
    model: str
    timeout: float


def load_settings() -> Settings:
    """Build settings from COPPER_* environment variables, falling back to defaults."""
    return Settings(
        base_url=os.environ.get("COPPER_BASE_URL", DEFAULT_BASE_URL).rstrip("/"),
        model=os.environ.get("COPPER_MODE", DEFAULT_MODEL),
        timeout=float(os.environ.get("COPPER_TIMEOUT", DEFAULT_TIMEOUT_SECONDS)),
    )
