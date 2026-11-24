"""Manual check: run the tools against the sandbox notes and print the output."""

from coppermind.config import NOTES_DIR
from coppermind.tools import ToolError
from coppermind.tools.files import list_files

try:
    print(list_files(NOTES_DIR))
except ToolError as error:
    print(f"Tool refused: {error}")
