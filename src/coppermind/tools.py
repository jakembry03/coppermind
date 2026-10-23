from pathlib import Path

MAX_CHARACTERS = 20000

class ToolError(Exception):
    """A tool refused a request. The message is safe to show the model."""


def list_files(root: Path) -> str:
    """List evrey file under root as relative paths, oen per line, sorted."""
    real_root = root.resolve()
    if not real_root.is_dir():
        raise ToolError("The notes folder was not found.")

    found = []
    for entry in real_root.rglob("*"):
        if not entry.is_file():
            continue
        relative = entry.relative_to(real_root)
        if any(part.startswith(".") for part in relative.parts):
            continue
        found.append(relative.as_posix())

    if not found:
        return "No files found."

    found.sort()
    return "\n".join(found)


def read_file(root, path, max_chars = MAX_CHARACTERS) -> str:
    """
    Read a text file under root and return its contents.

    `path` comes from the model, so it is untrusted:
    it's resolved and checked against root before anything touches the file
    """

    real_root = root.resolve()
    target = (real_root / path).resolve()

    if not target.is_relative_to(real_root):
        raise ToolError(f"Path is outside the allowed folder: {path}")

    if not target.exists():
        raise ToolError(f"File not found: {path}")
    if not target.is_file():
        raise ToolError(f"Not a file: {path}")

    try :
        content = target.read_text(encoding="utf-8")
    except UnicodeDecodeError as exc:
        raise ToolError(f"Not a text file: {path}") from exc

    if len(content) > max_chars:
        content = (
            content[:max_chars]
            + f"\n[Truncated: showing the first {max_chars} characters of a longer file.]"
        )

    return content
                

    

            
    
        


