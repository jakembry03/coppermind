import time

from rich.table import Table
from rich.console import Console
from rich.text import Text
from rich.panel import Panel
from rich import box


art = Text("▄█▀▀█▄\n▀ ▀ ▀", style="#b87333")      # the whole thing in copper

console = Console()
info = Text()
info.append("Copper\n", style="bold #b87333")
info.append("v0.1.0", style="dim")
grid = Table.grid(padding=(0, 2))
grid.add_column()
grid.add_column()
grid.add_row(art, info)


console.rule()
console.rule("[dim]conversation[/]")

with console.status("Copper is thinking...", spinner="dots"):
    time.sleep(2)
console.print("[#b87333]●[/] Here's your answer.")

console.print(Panel(grid, box=box.ROUNDED, border_style="#b87333", expand=True))


