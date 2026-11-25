from rich import box
from rich.console import Console
from rich.panel import Panel
from rich.table import Table
from rich.text import Text


from prompt_toolkit import PromptSession
from prompt_toolkit.formatted_text import HTML


from coppermind.agent import Agent, AgentError
from coppermind.config import load_settings
from coppermind.tools import build_registry
from coppermind.llm import LLMError


COPPER = "#b87333"

console = Console()
settings = load_settings()
agent = Agent(build_registry(settings.notes_dir), settings=settings)

# Header: printed once, then everything scrolls below it
art = Text("▄█▀▀█▄\n▀ ▀ ▀", style=COPPER)
info = Text()
info.append("Copper\n", style=f"bold {COPPER}")
info.append("v0.1.0", style="dim")
grid = Table.grid(padding=(0, 2))
grid.add_row(art, info)
console.print(Panel(grid, box=box.ROUNDED, border_style=COPPER))


while True:
    try:
        session = PromptSession()
        text = session.prompt(
            HTML('<style fg="#b87333"><b>&gt;</b></style> '),
            bottom_toolbar=" /clear • /quit",
        )
    except KeyboardInterrupt:
        break
    if text in {"/quit", "/exit"}:
        break
    if not text:
        continue

    try:
        with console.status("Copper is thinking...", spinner="dots"):
            reply = agent.send(text)

        console.print(f"[{COPPER}]●[/]", reply, markup=True)
    except (LLMError, AgentError) as error:
        console.print(f"[{COPPER}]●[/]", f"Error: {error}", markup=True)

    

