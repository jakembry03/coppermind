from pathlib import Path
from typing import Any

from coppermind.tools.base import Tool, ToolError
from coppermind.tools.core import core_tools
from coppermind.tools.files import file_tools

__all__ = ["Tool", "ToolError", "build_registry", "tool_schemas"]

def build_registry(notes_root: Path) -> dict[str, Tool]:
    """Every tool from every group, keyed by name."""
    tools = [
        *core_tools(),
        *file_tools(notes_root),
    ]
    registry: dict[str, Tool] = {}
    for tool in tools:
        if tool.name in registry:
            raise ValueError(f"Two tools are named {tool.name!r}")
        registry[tool.name] = tool
    return registry

def tool_schemas(registry: dict[str, Tool], groups: set[str] | None = None) -> list[dict[str, Any]]:
    """The descriptions sent to the model: every tool, or only those in `groups`."""
    return [t.schema() for t in registry.values() if groups is None or t.group in groups]

