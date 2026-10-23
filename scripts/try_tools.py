"""Manual check: run the tools against the sandbox notes and print the output."""

from pathlib import Path
from coppermind.tools import ToolError, list_files

try:
    print(list_files(Path("sandbox/notes")))
except ToolError as error:
    print(f"Tool refused: {error}")