from collections.abc import Callable
from dataclasses import dataclass
from pathlib import Path
from typing import Any

class ToolError(Exception):
    """A tool refused a request. the message is safe to show the model."""

@dataclass(frozen=True)
class Tool:
    name: str
    description: str
    parameters: dict[str, Any]
    function: Callable[..., str]
    group: str
    writes: bool = False

    def schema(self) -> dict[str, Any]:
        """The tool description in the OpenAI-compatible format the model server expects."""
        return {
            "type": "function",
            "function": {
                "name": self.name,
                "description": self.description,
                "parameters": self.parameters,
            },
        }


def is_hidden(relative: Path) -> bool:
    return any(part.startswith(".") for part in relative.parts)

def safe_path(root: Path, path: str) -> Path:
    """Turn an untrusted model path into a real path inside root, or raise ToolError."""
    real_root = root.resolve()
    target = (real_root / path).resolve()
    if not target.is_relative_to(real_root):
        raise ToolError(f"Path is outside the notes folder: {path}")
    if is_hidden(target.relative_to(real_root)):
        raise ToolError(f"Hidden files are off-limits: {path}")
    return target

