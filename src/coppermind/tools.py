"""
Tools Copper can call, plus the registry the agent loop uses to find them.

Each tool has two halves: the description the model reads (name, description, JSON Schema
for its arguments) and the Python function that actually runs. The model only ever sees the
first half; it asks for a tool by name and the agent looks it up in the registry.
"""

from collections.abc import Callable
from dataclasses import dataclass
from pathlib import Path
from typing import Any
from datetime import datetime
import shutil

MAX_CHARACTERS = 20000


class ToolError(Exception):
    """A tool refused a request. The message is safe to show the model."""


def get_current_datetime() -> str:
    """
    Returns the current local date and time of the system.

    This function takes no arguments and returns a string
    formatted as 'YYYY-MM-DD HH:MM:SS' and the UTC offset..

    Returns:
        str: The current date and time.
    """
    now = datetime.now().astimezone()
    return now.strftime("%A, %Y-%m-%d %H:%M:%S (UTC%z)")

def _is_hidden(relative: Path) -> bool:
    """Dotfiles and dot-folders (.env, .git/, .obsidian/) hold config and secrets, not notes."""
    return any(part.startswith(".") for part in relative.parts)


def list_files(root: Path) -> str:
    """List every file under root as relative paths, one per line, sorted."""
    real_root = root.resolve()
    if not real_root.is_dir():
        raise ToolError("The notes folder was not found.")

    found = []
    for entry in real_root.rglob("*"):
        if not entry.is_file():
            continue
        # A symlink can live inside root but point outside it; read_file would refuse it,
        # so don't advertise it either.
        if not entry.resolve().is_relative_to(real_root):
            continue
        relative = entry.relative_to(real_root)
        if _is_hidden(relative):
            continue
        found.append(relative.as_posix())

    if not found:
        return "No files found."

    found.sort()
    return "\n".join(found)

def list_folders(root: Path) -> str:
    """List every folder under root as relative paths, one per line, sorted."""
    real_root = root.resolve()
    if not real_root.is_dir():
        raise ToolError("The notes folder was not found.")

    found = []
    for entry in real_root.rglob("*"):
        if not entry.is_dir():
            continue
        if not entry.resolve().is_relative_to(real_root):
            continue
        relative = entry.relative_to(real_root)
        if _is_hidden(relative):
            continue
        found.append(relative.as_posix())

    if not found:
        return "No files found."

    found.sort()
    return "\n".join(found)


def read_file(root: Path, path: str, max_chars: int = MAX_CHARACTERS) -> str:
    """
    Read a text file under root and return its contents.

    `path` comes from the model, so it is untrusted:
    it's resolved and checked against root before anything touches the file
    """

    real_root = root.resolve()
    target = (real_root / path).resolve()

    if not target.is_relative_to(real_root):
        raise ToolError(f"Path is outside the allowed folder: {path}")
    if _is_hidden(target.relative_to(real_root)):
        raise ToolError(f"Hidden files can't be read: {path}")

    if not target.exists():
        raise ToolError(f"File not found: {path}")
    if not target.is_file():
        raise ToolError(f"Not a file: {path}")

    try:
        content = target.read_text(encoding="utf-8")
    except UnicodeDecodeError as exc:
        raise ToolError(f"Not a text file: {path}") from exc

    if len(content) > max_chars:
        content = (
            content[:max_chars]
            + f"\n[Truncated: showing the first {max_chars} characters of a longer file.]"
        )

    return content

def write_to_file(root: Path, path: str, content: str) -> str:
    """
    Writes content passed to it to a file of a given filepath.
    If the file does not already exist it will create it.
    First checks whether the given path is relative to the real root,
    raises an error if not.
    """
    real_root = root.resolve()
    target = (real_root / path).resolve()
    if not target.is_relative_to(real_root):
        raise ToolError(f"Path is outside the allowed folder: {path}")

    if _is_hidden(target.relative_to(real_root)):
        raise ToolError("Cannot write to hidden files.")

    if not target.exists():
        target.parent.mkdir(parents=True, exist_ok=True)
        target.touch()

    with open(target, "w", encoding="utf-8") as file:
        file.write(content)

    return f"Wrote: {content} to {Path(file.name).name}"

def append_to_file(root: Path, path: str, content: str) -> str:
    """
    Appends the text passed to it to the file located
    at the given filepath. If the file does not already exist, it will create it.
    First checks whether the given path is relative to the real root, raises an error if not.
    """
    real_root = root.resolve()
    target = (real_root / path).resolve()
    if not target.is_relative_to(real_root):
        raise ToolError(f"Path is outside the allowed folder: {path}")

    if _is_hidden(target.relative_to(real_root)):
        raise ToolError("Cannot write to hidden files.")

    if not target.exists():
        raise ToolError("File to append to does not exist.")

    with open(target, "a", encoding="utf-8") as file:
        file.write(content)

    return f"Wrote {content} to the end of {Path(file.name).name}"

def copy_file(root: Path, source: str, destination: str):
    real_root = root.resolve()
    source_path = (real_root / source).resolve()
    destination_path = (real_root / destination).resolve()
    if not source_path.is_relative_to(real_root):
        raise ToolError(f"Source path is outside the allowed folder: {real_root}")
    if not destination_path.is_relative_to(real_root):
        raise ToolError(f"Destination path is outside the allowed folder: {real_root}")
    if not source_path.exists():
        raise ToolError("Source path does not exist.")
    if not source_path.is_file():
        raise ToolError("Source path is not a file.")

    shutil.copy(source_path, destination_path)
    return f"Copied: {source_path} to {destination_path}"
    

def create_file(root: Path, path: str) -> str:
    """
    Creates an empty file of a given file type.
    """
    real_root = root.resolve()
    target = (real_root / path).resolve()
    if not target.is_relative_to(real_root):
        raise ToolError(f"Path is outside the allowed folder: {path}")

    if _is_hidden(target.relative_to(real_root)):
        raise ToolError("Cannot create dot files/hidden files.")

    if target.exists():
        raise ToolError("File already exists.")
    elif not target.exists():
        target.parent.mkdir(parents=True, exist_ok=True)
        target.touch()

    return f"Created {path}"

def delete_file(root: Path, path: str) -> str:
    """
    Deletes a file located at the given file path.
    """
    real_root = root.resolve()
    target = (real_root / path).resolve()
    if not target.is_relative_to(real_root):
        raise ToolError(f"Path is outside the allowed folder: {path}")

    if _is_hidden(target.relative_to(real_root)):
        raise ToolError("Cannot delete dot files/hidden files.")

    if not target.exists():
        raise ToolError("File does not exist.")

    Path(target).unlink(missing_ok=True)
    return f"Deleted {target}"

    




@dataclass(frozen=True)
class Tool:
    """One tool: what the model is told about it, the function that runs, and whether it writes.

    `writes` is checked by the approval gate (M6): any tool that changes something
    outside Copper must be marked True so Jake is asked first.
    """

    name: str
    description: str
    parameters: dict[str, Any]
    function: Callable[..., str]
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


def build_registry(notes_root: Path) -> dict[str, Tool]:
    """
    Create the tools with the notes folder already bound in, keyed by name.

    The root is fixed here, by Copper, so it never appears in a schema: the model can
    choose which file to read but never which folder it's allowed to read from. The
    lambdas accept exactly the arguments in each schema, so any extra argument the model
    invents (like `root` or `max_chars`) fails instead of being passed through.
    """
    tools = [
        Tool(
            name="list_files",
            description=(
                "List every file in the user's notes folder. Returns one relative path per line."
            ),
            parameters={
                "type": "object", 
                "properties": {}, 
                "required": []
            },
            function=lambda: list_files(notes_root),
        ),
        Tool(
            name="list_folders",
            description=(
                "List every folder in the user's notes folder. Returns one relative path per line."
            ),
            parameters={
                "type": "object",
                "properties": {},
                "required": []
            },
            function=lambda: list_folders(notes_root),
        ),
        Tool(
            name="read_file",
            description=(
                "Read one text file from the user's notes folder and return its contents. "
                "Use a path exactly as list_files returns it."
            ),
            parameters={
                "type": "object",
                "properties": {
                    "path": {
                        "type": "string",
                        "description": "Path relative to the notes folder, e.g. 'ideas/movie.md'.",
                    }
                },
                "required": ["path"],
            },
            function=lambda path: read_file(notes_root, path),
        ),
        Tool(
            name="get_current_datetime",
            description=(
                "Returns the current local date and time of the system formatted as 'YYYY-MM-DD HH:MM:SS'."
            ),
            parameters={
                "type": "object",
                "properties": {},
                "required": [],
            },
            function=get_current_datetime,
        ),
        Tool(
            name="write_to_file",
            description=(
                "Write text to a given file path in the users notes folder. Create the file and parent folders if do not already exist."
                "Use file path exactly how it is given by the user."
            ),
            parameters={
                "type": "object",
                "properties": {
                    "path": {
                        "type": "string",
                        "description": "Path of the file to be written to. Will be relative to the notes folder. e.g. reviews/superman.md",
                    },
                    "content": {
                        "type": "string",
                        "description": "Text to be written to the file."
                    },
                },
                "required": ["path", "content"],
            },
            function=lambda path, content: write_to_file(notes_root, path, content),
        ),
        Tool(
            name="append_to_file",
            description=(
                "Appends text to the end of a given file in the users notes folder."
                "Use file path exactly how it is given by the user."
            ),
            parameters={
                "type": "object",
                "properties": {
                    "path": {
                        "type": "string",
                        "description": "Path of the file to append to. Will be relative to the notes folder. e.g. reviews/spider-man.md."
                    },
                    "content": {
                        "type": "string",
                        "description": "Text to be appended to the file."
                    },
                },
                "required": ["path", "content"]
            },
            function=lambda path, content: append_to_file(notes_root, path, content),
        ),
        Tool(
            name="create_file",
            description=(
                "Create an empty file at given location."
                "Use location exactly as provided by the user."
            ),
            parameters={
                "type": "object",
                "properties": {
                    "path": {
                        "type": "string",
                        "description": "Path of the file to be created. Will be relative to the notes folder."
                    },
                },
                "required": ["path"]
            },
            function=lambda path: create_file(notes_root, path),
        ),
        Tool(
            name="delete_file",
            description=(
                "Deletes a file at a given location."
                "Use location exactly as given by user."
            ),
            parameters={
                "type": "object",
                "properties": {
                    "path": {
                        "type": "string",
                        "description": "Path of the file to be deleted. Will be relative to the notes folder."
                    },
                },
                "required": ["path"]
            },
            function=lambda path: delete_file(notes_root, path),
        )
    ]
    return {tool.name: tool for tool in tools}

def tool_schemas(registry: dict[str, Tool]) -> list[dict[str, Any]]:
    """Every tool's description, in the form sent to the model."""
    return [tool.schema() for tool in registry.values()]
