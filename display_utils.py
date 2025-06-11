# Rich display helpers for DracoVed
from rich.console import Console
from rich.table import Table
from rich.panel import Panel
from rich.text import Text

console = Console()

def print_rich_table(headers, rows, title=None):
    table = Table(title=title, show_lines=True, header_style="bold magenta")
    for h in headers:
        table.add_column(h, style="bold cyan")
    for row in rows:
        table.add_row(*[str(x) for x in row])
    console.print(table)
