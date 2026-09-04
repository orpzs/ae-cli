"""Console output, branding banner, and visual styles for ae-cli."""

import os
from typing import Optional
from rich.console import Console
from rich.panel import Panel
from rich.table import Table
from rich.text import Text
from rich import box

console = Console()

BANNER_ART = r"""
     _    _____        ____ _     ___ 
    / \  | ____|      / ___| |   |_ _|
   / _ \ |  _| _____ | |   | |    | | 
  / ___ \| |__|_____|| |___| |___ | | 
 /_/   \_\_____|      \____|_____|___|
"""


def print_banner(
    project_id: Optional[str] = None,
    location: Optional[str] = None,
    engine_name: Optional[str] = None,
    session_id: Optional[str] = None,
    user_id: Optional[str] = None,
):
    """Displays the terminal start banner and active session info."""
    title_text = Text()
    title_text.append(BANNER_ART.strip("\n"), style="bold cyan")
    title_text.append("\n  Vertex AI Agent Engine Interactive Terminal\n", style="bold white")

    meta_table = Table(box=box.SIMPLE_HEAVY, show_header=False, pad_edge=False)
    meta_table.add_column("Key", style="bold yellow")
    meta_table.add_column("Value", style="bold green")

    if project_id:
        meta_table.add_row("Project:", project_id)
    if location:
        meta_table.add_row("Location:", location)
    if engine_name:
        meta_table.add_row("Agent Engine:", engine_name)
    if session_id:
        meta_table.add_row("Session ID:", session_id)
    if user_id:
        meta_table.add_row("User ID:", user_id)

    panel = Panel(
        meta_table,
        title="[bold cyan]AE-CLI - Conversational Session[/bold cyan]",
        subtitle="[dim]Type [bold white]/help[/bold white] for commands, [bold white]/exit[/bold white] to quit[/dim]",
        border_style="cyan",
        padding=(0, 2),
    )

    console.print(title_text)
    console.print(panel)
    console.print()


def print_info_box(title: str, message: str, style: str = "cyan"):
    """Displays a stylized info box."""
    console.print(
        Panel(
            Text(message, style="white"),
            title=f"[{style}]{title}[/{style}]",
            border_style=style,
            padding=(0, 1),
        )
    )


def print_error(message: str, title: str = "Error"):
    """Displays an error alert."""
    console.print(
        Panel(
            Text(message, style="bold red"),
            title=f"[bold red]❌ {title}[/bold red]",
            border_style="red",
            padding=(0, 1),
        )
    )


def print_warning(message: str, title: str = "Warning"):
    """Displays a warning alert."""
    console.print(
        Panel(
            Text(message, style="yellow"),
            title=f"[yellow]⚠️ {title}[/yellow]",
            border_style="yellow",
            padding=(0, 1),
        )
    )
