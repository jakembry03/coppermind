from pathlib import Path
from coppermind.tools.base import Tool, ToolError, safe_path, is_hidden
import shutil

MAX_CHARACTERS = 20000

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
    Writes content passed to it to a file of a given filepath.
    If the file does not already exist it will create it.
    First checks whether the given path is relative to the real root,
    raises an error if not.
    """
    target = safe_path(root, path)

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
    target = safe_path(root, path)

    with open(target, "a", encoding="utf-8") as file:
        file.write(content)

    return f"Wrote {content} to the end of {Path(file.name).name}"


def create_file(root: Path, path: str) -> str:
    """
    Creates an empty file of a given file type.
    """
    target = safe_path(root, path)

    if target.exists():
        raise ToolError("File already exists.")
    elif not target.exists():
        target.parent.mkdir(parents=True, exist_ok=True)
        target.touch()

    return f"Created {path}"


def delete_file(root: Path, path: str) -> str:
    target = safe_path(root, path)
    if not target.is_file():
        raise ToolError(f"File does not exist: {path}")
    target.unlink()
    return f"Deleted {path}"


def create_folder(root: Path, path: str) -> str:
    target = safe_path(root, path)
    if target.exists():
        raise ToolError("Folder already exists.")
    elif not target.exists():
        target.mkdir(parents=True, exist_ok=True)

    return f"Created the folder: {target}"


def list_files(root: Path, path: str = ".") -> str:
    """List every file under root as relative paths, one per line, sorted."""
    target = safe_path(root, path)

    found = []
    for entry in target.rglob("*"):
        if not entry.is_file():
            continue
        # A symlink can live inside root but point outside it; read_file would refuse it,
        # so don't advertise it either.
        if not entry.resolve().is_relative_to(target):
            continue
        relative = entry.relative_to(target)
        if is_hidden(relative):
            continue
        found.append(relative.as_posix())

    if not found:
        return "No files found."

    found.sort()
    return "\n".join(found)


def list_folders(root: Path, path: str = ".") -> str:
    """List every folder under root as relative paths, one per line, sorted."""
    target = safe_path(root, path)

    found = []
    for entry in target.rglob("*"):
        if not entry.is_dir():
            continue
        if not entry.resolve().is_relative_to(target):
            continue
        relative = entry.relative_to(target)
        if is_hidden(relative):
            continue
        found.append(relative.as_posix())

    if not found:
        return "No files found."

    found.sort()
    return "\n".join(found)


def copy_file(root: Path, source: str, destination: str) -> str:
    source_path = safe_path(root, source)
    destination_path = safe_path(root, destination)

    shutil.copy(source_path, destination_path)
    return f"Copied: {source_path} to {destination_path}"


def move_file(root: Path, source: str, destination: str) -> str:
    source_path = safe_path(root, source)
    destination_path = safe_path(root, destination)

    shutil.move(source_path, destination_path)
    return f"Moved: {source_path} to {destination_path}"


def file_tools(notes_root: Path) -> list[Tool]:
    """The file group, with the notes folder bound in so the model never chooses it."""
    return [
        Tool(
            name="read_file",
            description=(
                "Read one text file from the user's notes folder and return its contents. "
                "Use a path exactly as list_files returns it."
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
            group="files",
            writes=True,
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
            group="files",
            writes=True,
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
                "Create an empty folder at a given location."
                "Use location exactly as given by user."
            ),
            parameters={
                "type": "object",
                "properties": {
                    "path": {
                        "type": "string",
                        "description": "Path of the folder to be created. Will be relative to the notes folder."
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
                "List every file in the user's notes folder. Returns one relative path per line."
            ),
            parameters={
                "type": "object", 
                "properties": {}, 
                "required": []
            },
            function=lambda: list_files(notes_root),
            group="files",
            writes=False,
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
            group="files",
            writes=False,
        ),
        Tool(
            name="copy_file",
            description=(
                "Copies a file from a source path to a destination path."
                "Use paths exactly as given to you by the user."
            ),
            parameters={
                "type": "object",
                "properties": {
                    "source_path": {
                        "type": "string",
                        "description": "The path of the source file to be copied. Will be relative to the notes folder."
                    },
                    "destination_path": {
                        "type": "string",
                        "description": "The path of the destination file to be copied to. Will be relative to the notes folder."
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
                "Moves a file from a source path to a destination path."
                "Use paths exactly as given to you by the user."
            ),
            parameters={
                "type": "object",
                "properties": {
                    "source_path": {
                        "type": "string",
                        "description": "The path of the source file to be moved. Will be relative to the notes folder."
                    },
                    "destination_path": {
                        "type": "string",
                        "description": "The destination path to move the file to. Will be relative to the notes folder."
                    }
                },
                "required": ["source_path", "destination_path"]
            },
            function=lambda source_path, destination_path: move_file(notes_root, source_path, destination_path),
            group="files",
            writes=True,
        )
    ]