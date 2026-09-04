"""Detailed inspection of an Agent Engine's specification and exposed operations."""

import sys
import json
from typing import Optional
from rich.panel import Panel
from rich.table import Table
from rich import box

from ae_cli.config import AEConfig
from ae_cli.client import AgentEngineClient
from ae_cli.ui.console import console, print_error


def info_command(config: AEConfig, engine_id: Optional[str] = None):
    """Retrieves and displays full specifications for an Agent Engine."""
    target_id = engine_id or config.engine_id
    try:
        client = AgentEngineClient(config)
        if not target_id:
            target_id = client.resolve_engine().split("/")[-1]
        details = client.get_agent_engine(target_id)
    except Exception as e:
        print_error(str(e), title="Failed to inspect Agent Engine")
        sys.exit(1)

    spec = details.get("spec", {})
    package_spec = spec.get("packageSpec", {})
    class_methods = spec.get("classMethods", [])

    info_text = (
        f"[bold cyan]Display Name:[/bold cyan] {details.get('displayName', 'N/A')}\n"
        f"[bold cyan]Resource Name:[/bold cyan] {details.get('name', 'N/A')}\n"
        f"[bold cyan]Python Version:[/bold cyan] {package_spec.get('pythonVersion', 'N/A')}\n"
        f"[bold cyan]Staging Bucket:[/bold cyan] {package_spec.get('gcsStagingDirectory', 'N/A')}\n"
        f"[bold cyan]Created:[/bold cyan] {details.get('createTime', 'N/A')}\n"
        f"[bold cyan]Updated:[/bold cyan] {details.get('updateTime', 'N/A')}"
    )

    console.print()
    console.print(Panel(info_text, title="[bold yellow]Agent Engine Specifications[/bold yellow]", border_style="cyan"))

    if class_methods:
        table = Table(title="Exposed Operations & Methods", box=box.ROUNDED, header_style="bold cyan")
        table.add_column("Method Name", style="bold yellow")
        table.add_column("Parameters", style="white")
        table.add_column("Description", style="dim")

        for m in class_methods:
            if isinstance(m, dict):
                params = m.get("parameters", {}).get("properties", {})
                param_list = list(params.keys())
                table.add_row(
                    m.get("name", ""),
                    ", ".join(param_list) if param_list else "None",
                    m.get("description", "").strip() or "-",
                )
        console.print(table)
        console.print()
