from rich import box
from rich.console import Console
from rich.panel import Panel
from rich.table import Table
from rich.text import Text


from coppermind.agent import Agent
from coppermind.config import load_settings
from coppermind.tools import build_registry


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
    text = console.input(f"[bold {COPPER}]>[/] ").strip()
    if text in {"/quit", "/exit"}:
        break
    if not text:
        continue

    with console.status("Copper is thinking...", spinner="dots"):
        reply = agent.send(text)

    console.print(f"[{COPPER}]●[/]", reply, markup=False)



