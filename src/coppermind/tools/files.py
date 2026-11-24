import os
import shutil
from pathlib import Path

from coppermind.tools.base import Tool, ToolError, safe_path

MAX_CHARACTERS = 20000
MAX_LIST_ENTRIES = 500


def show_path(root: Path, given: str | Path, actual: Path) -> str:
    """
    Describe a path the way the model gave it to us.

    If the model passed a relative path, answer with a path relative to the notes
    folder. If it passed an absolute path, answer with an absolute path.
    """
    if Path(given).is_absolute():
        return str(actual)
    return actual.relative_to(root.resolve()).as_posix()


def final_destination(root: Path, source_path: Path, destination_path: Path, destination: str) -> Path:
    """
    Work out where a copy or move will land, the way `mv` and `cp` do.

    If the destination is an existing folder, the source goes inside it, keeping its name.
    Otherwise the destination is the new path itself. Either way, nothing gets overwritten.
    """
    if destination_path.is_dir():
        final = destination_path / source_path.name
    else:
        final = destination_path

    if final.exists():
        raise ToolError(f"Destination already exists: {show_path(root, destination, final)}")
    return final


def read_file(root: Path, path: str, max_chars: int = MAX_CHARACTERS):
    """Read a text file under root and return its contents."""
    target = safe_path(root, path)

    if not target.exists():
        raise ToolError(f"File not found: {path}")
    if not target.is_file():
        raise ToolError(f"Not a file: {path}")

    try:
        content = target.read_text(encoding="utf-8")
    except UnicodeDecodeError as exc:
        raise ToolError(f"Not a text file: {path}") from exc

    if len(content) > max_chars:
        content = (content[:max_chars]
                   + f"\n[Truncated: showing the first {max_chars} characters of a long file.]")
    return content


def write_to_file(root: Path, path: str, content: str) -> str:
    """
    Replace the contents of a file with `content`, creating the file and its
    parent folders if they don't exist yet.
    """
    target = safe_path(root, path)
    target.parent.mkdir(parents=True, exist_ok=True)
    target.write_text(content, encoding="utf-8")
    return f"Wrote {len(content)} characters to {show_path(root, path, target)}"


def append_to_file(root: Path, path: str, content: str) -> str:
    """
    Add `content` to the end of a file, creating the file and its parent
    folders if they don't exist yet.
    """
    target = safe_path(root, path)
    target.parent.mkdir(parents=True, exist_ok=True)
    with open(target, "a", encoding="utf-8") as file:
        file.write(content)
    return f"Appended {len(content)} characters to {show_path(root, path, target)}"


def create_file(root: Path, path: str) -> str:
    """Create an empty file, along with any missing parent folders."""
    target = safe_path(root, path)

    if target.is_file():
        raise ToolError("File already exists.")
    if target.exists():
        raise ToolError(f"A folder already exists at that path: {path}")

    target.parent.mkdir(parents=True, exist_ok=True)
    target.touch()
    return f"Created {show_path(root, path, target)}"


def delete_file(root: Path, path: str) -> str:
    target = safe_path(root, path)
    if not target.is_file():
        raise ToolError(f"File does not exist: {path}")
    target.unlink()
    return f"Deleted {path}"


def copy_file(root: Path, source: str, destination: str) -> str:
    """Copy a file. Refuses to overwrite anything already at the destination."""
    source_path = safe_path(root, source)
    destination_path = safe_path(root, destination)

    if not source_path.exists():
        raise ToolError(f"Source path does not exist: {source}")
    if not source_path.is_file():
        raise ToolError(f"Source path is not a file: {source}")

    final = final_destination(root, source_path, destination_path, destination)
    final.parent.mkdir(parents=True, exist_ok=True)
    shutil.copy(source_path, final)
    return f"Copied {show_path(root, source, source_path)} to {show_path(root, destination, final)}"


def move_file(root: Path, source: str, destination: str) -> str:
    """Move a file. Refuses to overwrite anything already at the destination."""
    source_path = safe_path(root, source)
    destination_path = safe_path(root, destination)

    if not source_path.exists():
        raise ToolError(f"Source path does not exist: {source}")
    if not source_path.is_file():
        raise ToolError(f"Source path is not a file: {source}")

    final = final_destination(root, source_path, destination_path, destination)
    final.parent.mkdir(parents=True, exist_ok=True)
    shutil.move(source_path, final)
    return f"Moved {show_path(root, source, source_path)} to {show_path(root, destination, final)}"


def list_target(root: Path, path: str | None) -> Path:
    """
    The folder a listing tool should walk: the notes folder by default, or any
    absolute path the model passes. Unlike the other file tools, listing is not
    limited to the notes folder.
    """
    if not path:
        target = root
    else:
        requested = Path(path)
        if not requested.is_absolute():
            raise ToolError(f"The path must be absolute, e.g. C:\\Users\\name\\Documents: {path}")
        if any(part.startswith(".") for part in requested.parts):
            raise ToolError(f"Hidden folders are off-limits: {path}")
        target = requested

    target = target.resolve()
    if not target.exists():
        raise ToolError("Files not found.")
    if not target.is_dir():
        raise ToolError(f"Not a folder: {path or root}")
    return target


def walk_entries(target: Path, want_folders: bool) -> str:
    """
    Every file (or every folder) under target, as sorted relative paths, one per line.

    Hidden entries are skipped, and hidden folders aren't searched at all. The list
    stops at MAX_LIST_ENTRIES so a big folder can't flood the model's context.
    """
    found = []
    truncated = False
    for folder, subfolders, files in os.walk(target):
        # Editing `subfolders` in place tells os.walk not to go into hidden folders.
        subfolders[:] = [name for name in subfolders if not name.startswith(".")]
        names = subfolders if want_folders else files
        for name in names:
            if name.startswith("."):
                continue
            entry = Path(folder) / name
            # A symlink can live inside the folder but point outside it; don't advertise it.
            if not entry.resolve().is_relative_to(target):
                continue
            found.append(entry.relative_to(target).as_posix())
            if len(found) > MAX_LIST_ENTRIES:
                truncated = True
                break
        if truncated:
            break

    if not found:
        return "No folders found." if want_folders else "No files found."

    found = sorted(found[:MAX_LIST_ENTRIES])
    if truncated:
        found.append(f"[Truncated: showing the first {MAX_LIST_ENTRIES} entries.]")
    return "\n".join(found)


def list_files(root: Path, path: str | None = None) -> str:
    """List every file under the notes folder, or under an absolute `path`."""
    return walk_entries(list_target(root, path), want_folders=False)


def list_folders(root: Path, path: str | None = None) -> str:
    """List every folder under the notes folder, or under an absolute `path`."""
    return walk_entries(list_target(root, path), want_folders=True)


def create_folder(root: Path, path: str) -> str:
    """Create a folder, along with any missing parent folders."""
    target = safe_path(root, path)

    if target.is_dir():
        raise ToolError("Folder already exists.")
    if target.exists():
        raise ToolError(f"A file already exists at that path: {path}")

    target.mkdir(parents=True)
    return f"Created the folder: {show_path(root, path, target)}"


def copy_folder(root: Path, source: str, destination: str) -> str:
    """Copy a folder and everything in it. Refuses to overwrite or to copy into itself."""
    source_path = safe_path(root, source)
    destination_path = safe_path(root, destination)

    if not source_path.exists():
        raise ToolError(f"Source path does not exist: {source}")
    if not source_path.is_dir():
        raise ToolError(f"Source path is not a folder: {source}")

    final = final_destination(root, source_path, destination_path, destination)
    if final.is_relative_to(source_path):
        raise ToolError(f"Can't copy a folder into itself: {source} -> {destination}")

    # copytree creates `final` and any missing parent folders.
    shutil.copytree(source_path, final)
    return f"Copied {show_path(root, source, source_path)} to {show_path(root, destination, final)}"


def move_folder(root: Path, source: str, destination: str) -> str:
    """Move a folder and everything in it. Refuses to overwrite or to move into itself."""
    source_path = safe_path(root, source)
    destination_path = safe_path(root, destination)

    if not source_path.exists():
        raise ToolError(f"Source path does not exist: {source}")
    if not source_path.is_dir():
        raise ToolError(f"Source path is not a folder: {source}")

    final = final_destination(root, source_path, destination_path, destination)
    if final.is_relative_to(source_path):
        raise ToolError(f"Can't move a folder into itself: {source} -> {destination}")

    final.parent.mkdir(parents=True, exist_ok=True)
    shutil.move(source_path, final)
    return f"Moved {show_path(root, source, source_path)} to {show_path(root, destination, final)}"


# Shared wording for the copy and move tools, so all four describe destinations the same way.
DESTINATION_RULES = (
    "If the destination is an existing folder, the source goes inside it. "
    "Otherwise the destination becomes the new path, and missing parent folders are created. "
    "Fails if something already exists at the final path."
)


def file_tools(notes_root: Path) -> list[Tool]:
    """The file group, with the notes folder bound in so the model never chooses it."""
    return [
        Tool(
            name="read_file",
            description=(
                "Read one text file from the user's notes folder and return its contents. "
                "Use a path exactly as list_files returns it for the notes folder."
            ),
            parameters={
                "type": "object",
                "properties": {
                    "path": {"type": "string",
                             "description": "Path relative to the notes folder, e.g. 'ideas/movie.md'."}
                },
                "required": ["path"],
            },
            function=lambda path: read_file(notes_root, path),
            group="files",
            writes=False,
        ),
        Tool(
            name="write_to_file",
            description=(
                "Write text to a file in the user's notes folder, replacing anything already in it. "
                "Creates the file and its parent folders if they don't exist yet. "
                "Use the file path exactly as the user gives it."
            ),
            parameters={
                "type": "object",
                "properties": {
                    "path": {
                        "type": "string",
                        "description": "Path of the file to write, relative to the notes folder, e.g. reviews/superman.md.",
                    },
                    "content": {
                        "type": "string",
                        "description": "Text to write to the file."
                    },
                },
                "required": ["path", "content"],
            },
            function=lambda path, content: write_to_file(notes_root, path, content),
            group="files",
            writes=True,
        ),
        Tool(
            name="append_to_file",
            description=(
                "Add text to the end of a file in the user's notes folder. "
                "Creates the file and its parent folders if they don't exist yet. "
                "Use the file path exactly as the user gives it."
            ),
            parameters={
                "type": "object",
                "properties": {
                    "path": {
                        "type": "string",
                        "description": "Path of the file to append to, relative to the notes folder, e.g. reviews/spider-man.md."
                    },
                    "content": {
                        "type": "string",
                        "description": "Text to add to the end of the file."
                    },
                },
                "required": ["path", "content"]
            },
            function=lambda path, content: append_to_file(notes_root, path, content),
            group="files",
            writes=True,
        ),
        Tool(
            name="create_file",
            description=(
                "Create an empty file in the user's notes folder. "
                "Use the location exactly as the user gives it."
            ),
            parameters={
                "type": "object",
                "properties": {
                    "path": {
                        "type": "string",
                        "description": "Path of the file to create, relative to the notes folder."
                    },
                },
                "required": ["path"]
            },
            function=lambda path: create_file(notes_root, path),
            group="files",
            writes=True,
        ),
        Tool(
            name="delete_file",
            description="Delete one file from the user's notes folder.",
            parameters={
                "type": "object",
                "properties": {
                    "path": {"type": "string", "description": "Path relative to the notes folder."}
                },
                "required": ["path"],
            },
            function=lambda path: delete_file(notes_root, path),
            group="files",
            writes=True,      # it changes something, so the approval gate must see it
        ),
        Tool(
            name="create_folder",
            description=(
                "Create an empty folder in the user's notes folder. "
                "Use the location exactly as the user gives it."
            ),
            parameters={
                "type": "object",
                "properties": {
                    "path": {
                        "type": "string",
                        "description": "Path of the folder to create, relative to the notes folder."
                    }
                },
                "required": ["path"],
            },
            function=lambda path: create_folder(notes_root, path),
            group="files",
            writes=True,
        ),
        Tool(
            name="list_files",
            description=(
                "List every file in a folder and its subfolders. Returns one path per line, "
                "relative to the listed folder. Lists the user's notes folder unless given a path."
            ),
            parameters={
                "type": "object",
                "properties": {
                    "path": {
                        "type": "string",
                        "description": (
                            "Absolute path of the folder to list, e.g. C:\\Users\\jake\\Documents. "
                            "Leave it out to list the notes folder."
                        ),
                    }
                },
                "required": []
            },
            function=lambda path=None: list_files(notes_root, path),
            group="files",
            writes=False,
        ),
        Tool(
            name="list_folders",
            description=(
                "List every folder in a folder and its subfolders. Returns one path per line, "
                "relative to the listed folder. Lists the user's notes folder unless given a path."
            ),
            parameters={
                "type": "object",
                "properties": {
                    "path": {
                        "type": "string",
                        "description": (
                            "Absolute path of the folder to list, e.g. C:\\Users\\jake\\Documents. "
                            "Leave it out to list the notes folder."
                        ),
                    }
                },
                "required": []
            },
            function=lambda path=None: list_folders(notes_root, path),
            group="files",
            writes=False,
        ),
        Tool(
            name="copy_folders",
            description=(
                "Copy a folder and everything in it to a new location in the user's notes folder. "
                + DESTINATION_RULES + " "
                "Use paths exactly as the user gives them."
            ),
            parameters={
                "type": "object",
                "properties": {
                    "source_path": {
                        "type": "string",
                        "description": "Path of the folder to copy, relative to the notes folder."
                    },
                    "destination_path": {
                        "type": "string",
                        "description": "Where to copy the folder to, relative to the notes folder."
                    }
                },
                "required": ["source_path", "destination_path"]
            },
            function=lambda source_path, destination_path: copy_folder(notes_root, source_path, destination_path),
            group="files",
            writes=True,
        ),
        Tool(
            name="move_folder",
            description=(
                "Move a folder and everything in it to a new location in the user's notes folder. "
                + DESTINATION_RULES + " "
                "Use paths exactly as the user gives them."
            ),
            parameters={
                "type": "object",
                "properties": {
                    "source_path": {
                        "type": "string",
                        "description": "Path of the folder to move, relative to the notes folder."
                    },
                    "destination_path": {
                        "type": "string",
                        "description": "Where to move the folder to, relative to the notes folder."
                    }
                },
                "required": ["source_path", "destination_path"]
            },
            function=lambda source_path, destination_path: move_folder(notes_root, source_path, destination_path),
            group="files",
            writes=True,
        ),
        Tool(
            name="copy_file",
            description=(
                "Copy a file to a new location in the user's notes folder. "
                + DESTINATION_RULES + " "
                "Use paths exactly as the user gives them."
            ),
            parameters={
                "type": "object",
                "properties": {
                    "source_path": {
                        "type": "string",
                        "description": "Path of the file to copy, relative to the notes folder."
                    },
                    "destination_path": {
                        "type": "string",
                        "description": "Where to copy the file to, relative to the notes folder."
                    }
                },
                "required": ["source_path", "destination_path"]
            },
            function=lambda source_path, destination_path: copy_file(notes_root, source_path, destination_path),
            group="files",
            writes=True,
        ),
        Tool(
            name="move_file",
            description=(
                "Move a file to a new location in the user's notes folder. "
                + DESTINATION_RULES + " "
                "Use paths exactly as the user gives them."
            ),
            parameters={
                "type": "object",
                "properties": {
                    "source_path": {
                        "type": "string",
                        "description": "Path of the file to move, relative to the notes folder."
                    },
                    "destination_path": {
                        "type": "string",
                        "description": "Where to move the file to, relative to the notes folder."
                    }
                },
                "required": ["source_path", "destination_path"]
            },
            function=lambda source_path, destination_path: move_file(notes_root, source_path, destination_path),
            group="files",
            writes=True,
        )
    ]
