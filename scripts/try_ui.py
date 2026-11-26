"""
Playground for Copper's terminal UI (rich + prompt_toolkit). Not part of the package.

The conversation is printed into the terminal's normal scrollback, so you scroll it like
any other output. The input is a small bordered box that prompt_toolkit draws at the
bottom of the terminal. It disappears when you press Enter, and the message is then
printed into the scrollback with rich.
"""

from importlib.metadata import version
from pathlib import Path

from prompt_toolkit.application import Application
from prompt_toolkit.history import InMemoryHistory
from prompt_toolkit.key_binding import KeyBindings
from prompt_toolkit.layout import HSplit, Layout, Window
from prompt_toolkit.layout.controls import FormattedTextControl
from prompt_toolkit.styles import Style
from prompt_toolkit.widgets import Frame, TextArea
from rich import box
from rich.console import Console
from rich.panel import Panel
from rich.table import Table
from rich.text import Text

from coppermind.agent import Agent, AgentError
from coppermind.config import load_settings
from coppermind.llm import LLMError
from coppermind.tools import build_registry

COPPER = "#b87333"
QUIT_COMMANDS = {"/quit", "/exit"}

# Placeholder rock creature: a carapace on top, legs underneath. Replace it with your own Rocky.
ART = (
    "  ▄▓▓▓▓▓▄\n"
    " ▐▓▒░▒░▒▓▌\n"
    "  ▀▓▓▓▓▓▀\n"
    " ▄▀ ▐ ▌ ▀▄\n"
    "▀   ▀ ▀   ▀"
)

# Long-lived objects are created ONCE, not inside the loop.
console = Console()                  # conversation output -> stdout
err_console = Console(stderr=True)   # errors -> stderr
history = InMemoryHistory()          # lets the up arrow bring back earlier prompts


# ---------------------------------------------------------------- output (rich)

def short_path(path: Path) -> str:
    """Show a path under the home folder as ~/..., like most shells do."""
    home = Path.home()
    if path == home:
        return "~"
    if path.is_relative_to(home):
        return "~/" + path.relative_to(home).as_posix()
    return str(path)


def show_banner(model: str) -> None:
    """The welcome box: art on the left, name/version/model/folder on the right."""
    art = Text(ART, style=COPPER)

    info = Text()
    info.append("Copper", style=f"bold {COPPER}")
    info.append(f"  v{version('coppermind')}\n", style="dim")
    info.append(f"{model}\n")
    info.append(short_path(Path.cwd()), style="dim")

    grid = Table.grid(padding=(0, 2))
    grid.add_column(vertical="middle")
    grid.add_column(vertical="middle")
    grid.add_row(art, info)

    console.print(Panel(grid, box=box.ROUNDED, border_style=COPPER, expand=False))
    console.print()


def show_user(text: str) -> None:
    # Text.assemble joins (text, style) pieces. Plain strings are never read as markup,
    # so a message containing "[something]" prints exactly as typed.
    console.print(Text.assemble(("> ", f"bold {COPPER}"), (text, "bold")))
    console.print()


def show_reply(reply: str) -> None:
    console.print(Text.assemble(("● ", COPPER), reply))
    console.print()


def show_note(note: str) -> None:
    console.print(Text(note, style="dim"))


def show_error(message: str) -> None:
    err_console.print(Text(f"Error: {message}", style="bold red"))


# ---------------------------------------------------------------- input (prompt_toolkit)

def read_in_box() -> str:
    """
    Draw a bordered input box at the bottom of the terminal and wait for Enter.

    Returns the typed text. Raises KeyboardInterrupt on Ctrl+C and EOFError on
    Ctrl+D, the same as input() does, so the loop can treat them the same way.
    """

    def submit(buffer) -> bool:
        # Called by the TextArea when Enter is pressed. `app` is looked up when this
        # runs (after it's been created below), not when the function is defined.
        app.exit(result=buffer.text)
        return False  # False = don't keep the text in the box afterwards

    text_box = TextArea(
        prompt="> ",
        multiline=False,
        history=history,
        accept_handler=submit,
    )
    hints = Window(
        FormattedTextControl(" /clear • /quit"),
        height=1,
        style="class:hints",
    )

    keys = KeyBindings()

    @keys.add("c-c")
    def _ctrl_c(event):
        event.app.exit(exception=KeyboardInterrupt)

    @keys.add("c-d")
    def _ctrl_d(event):
        event.app.exit(exception=EOFError)

    app = Application(
        # HSplit stacks its children top to bottom: the framed box, then the hint line.
        layout=Layout(HSplit([Frame(text_box), hints]), focused_element=text_box),
        key_bindings=keys,
        style=Style.from_dict({
            "frame.border": COPPER,  # Frame's border uses the "frame.border" style class
            "hints": "#888888",
        }),
        full_screen=False,       # draw inline at the bottom, don't take over the screen
        erase_when_done=True,    # remove the box once Enter is pressed
    )
    return app.run()


# ---------------------------------------------------------------- the chat loop

def main() -> None:
    settings = load_settings()
    agent = Agent(build_registry(settings.notes_dir), settings=settings)

    show_banner(settings.model)

    while True:
        try:
            text = read_in_box().strip()
        except (KeyboardInterrupt, EOFError):
            break

        if not text:
            continue
        if text in QUIT_COMMANDS:
            break
        if text == "/clear":
            agent.clear()
            console.clear()
            show_banner(settings.model)
            continue
        if text.startswith("/"):
            show_note(f"Unknown command: {text}. Try /clear or /quit.")
            continue

        show_user(text)
        try:
            with console.status("Copper is thinking...", spinner="dots"):
                reply = agent.send(text)
        except (LLMError, AgentError) as error:
            show_error(str(error))
            continue
        except KeyboardInterrupt:
            show_note("(interrupted)")
            continue

        show_reply(reply)


if __name__ == "__main__":
    main()