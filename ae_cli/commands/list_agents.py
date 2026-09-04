"""Lists deployed Vertex AI Agent Engines."""

import sys
from rich.table import Table
from rich import box

from ae_cli.config import AEConfig
from ae_cli.client import AgentEngineClient
from ae_cli.ui.console import console, print_error


def list_agents_command(config: AEConfig):
    """Fetches and displays deployed Agent Engines in the configured project/location."""
    try:
        client = AgentEngineClient(config)
        engines = client.list_agent_engines()
    except Exception as e:
        print_error(str(e), title="Failed to list Agent Engines")
        sys.exit(1)

    if not engines:
        console.print(
            f"\n[yellow]No deployed Agent Engines found in project '{config.project_id}' ({config.location}).[/yellow]"
        )
        return

    table = Table(
        title=f"Deployed Agent Engines ({config.project_id} / {config.location})",
        box=box.ROUNDED,
        header_style="bold cyan",
    )
    table.add_column("Display Name", style="bold white")
    table.add_column("Engine ID", style="bold yellow")
    table.add_column("Created", style="dim")
    table.add_column("Updated", style="dim")

    for eng in engines:
        name = eng.get("name", "")
        engine_id = name.split("/")[-1] if "/" in name else name
        table.add_row(
            eng.get("displayName", "Unnamed"),
            engine_id,
            eng.get("createTime", "N/A"),
            eng.get("updateTime", "N/A"),
        )

    console.print()
    console.print(table)
    console.print("\n[dim]To converse with an agent: [bold white]ae chat --engine <Engine ID>[/bold white][/dim]\n")
