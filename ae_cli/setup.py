"""Automated pre-setup wizard for Google Cloud authentication and Agent Engine configuration."""

import os
import sys
import shutil
import subprocess
from pathlib import Path
from typing import Optional, List, Dict, Any
from rich.console import Console
from rich.panel import Panel
from rich.table import Table
from rich import box

from ae_cli.config import AEConfig
from ae_cli.ui.console import console, print_info_box, print_error, print_warning


def get_gcloud_binary() -> Optional[str]:
    """Finds gcloud CLI executable."""
    return shutil.which("gcloud") or shutil.which("gcloud.cmd")


def has_adc_credentials() -> bool:
    """Checks if Application Default Credentials file exists on the system."""
    env_adc = os.getenv("GOOGLE_APPLICATION_CREDENTIALS")
    if env_adc and os.path.exists(env_adc):
        return True

    if sys.platform == "win32":
        adc_path = Path(os.path.expandvars(r"%APPDATA%\gcloud\application_default_credentials.json"))
    else:
        adc_path = Path.home() / ".config" / "gcloud" / "application_default_credentials.json"

    return adc_path.exists()


def get_active_gcloud_account() -> Optional[str]:
    """Retrieves active gcloud account email if available."""
    gcloud = get_gcloud_binary()
    if not gcloud:
        return None
    try:
        res = subprocess.run(
            [gcloud, "auth", "list", "--filter=status:ACTIVE", "--format=value(account)"],
            capture_output=True,
            text=True,
            timeout=8,
        )
        acc = res.stdout.strip().split("\n")[0].strip()
        return acc if acc else None
    except Exception:
        return None


def get_active_gcloud_project() -> Optional[str]:
    """Retrieves currently configured gcloud project ID."""
    gcloud = get_gcloud_binary()
    if not gcloud:
        return None
    try:
        res = subprocess.run(
            [gcloud, "config", "get-value", "project"],
            capture_output=True,
            text=True,
            timeout=5,
        )
        proj = res.stdout.strip()
        if proj and "(unset)" not in proj:
            return proj
    except Exception:
        return None


def run_gcloud_command(args: List[str], description: str) -> bool:
    """Runs an interactive gcloud command sharing terminal stdin/stdout."""
    gcloud = get_gcloud_binary()
    if not gcloud:
        print_error("Google Cloud SDK ('gcloud') is not installed or not in PATH.", title="gcloud Missing")
        return False

    console.print(f"\n[bold cyan]▶ {description}...[/bold cyan]")
    try:
        # Run interactively so user can complete browser consent / code prompt
        code = subprocess.call([gcloud] + args)
        return code == 0
    except Exception as e:
        console.print(f"[bold red]Failed to execute gcloud {args[0]}: {e}[/bold red]")
        return False


def save_env_file(project_id: str, location: str, engine_id: Optional[str] = None, app_name: Optional[str] = None):
    """Writes or updates .env file in the current working directory."""
    env_path = Path(".env")
    existing_lines = []
    if env_path.exists():
        try:
            with open(env_path, "r", encoding="utf-8") as f:
                existing_lines = f.readlines()
        except Exception:
            pass

    key_values = {
        "GOOGLE_CLOUD_PROJECT": project_id,
        "GOOGLE_CLOUD_LOCATION": location,
    }
    if engine_id:
        key_values["AGENT_ENGINE_ID"] = engine_id
    if app_name:
        key_values["APP_NAME"] = app_name

    updated_keys = set()
    new_lines = []
    for line in existing_lines:
        stripped = line.strip()
        matched = False
        for k, v in key_values.items():
            if stripped.startswith(f"{k}=") or stripped.startswith(f"export {k}="):
                new_lines.append(f"{k}={v}\n")
                updated_keys.add(k)
                matched = True
                break
        if not matched:
            new_lines.append(line)

    for k, v in key_values.items():
        if k not in updated_keys:
            new_lines.append(f"{k}={v}\n")

    with open(env_path, "w", encoding="utf-8") as f:
        f.writelines(new_lines)


def run_setup(config: AEConfig) -> AEConfig:
    """Runs the complete interactive pre-setup wizard:

    1. gcloud auth login
    2. gcloud auth application-default login
    3. Google Cloud Project ID
    4. Vertex AI Location / Region
    5. Agent Engine discovery & selection
    6. Saves to .env and ~/.ae/config.json
    """
    console.print()
    console.print(
        Panel(
            "[bold white]Welcome to ae-cli Pre-Setup Wizard[/bold white]\n\n"
            "[dim]We will configure Google Cloud authentication, select your project & region,\n"
            "and connect to your deployed Vertex AI Agent Engine.[/dim]",
            title="[bold cyan]⚡ ae-cli Initialization[/bold cyan]",
            border_style="cyan",
            padding=(1, 2),
        )
    )

    # -------------------------------------------------------------
    # Step 1: Google Cloud Login
    # -------------------------------------------------------------
    active_account = get_active_gcloud_account()
    if active_account:
        console.print(f"\n[green]✓ Detected active gcloud account:[/green] [bold white]{active_account}[/bold white]")
        reauth = input("Do you want to re-authenticate or switch account? [y/N]: ").strip().lower()
        should_login = reauth in ("y", "yes")
    else:
        console.print("\n[yellow]No active Google Cloud account detected.[/yellow]")
        should_login = True

    if should_login:
        console.print("[cyan]Opening browser for Google Cloud SDK login...[/cyan]")
        ok = run_gcloud_command(["auth", "login"], "Running 'gcloud auth login'")
        if not ok:
            print_warning("gcloud auth login did not exit cleanly. Continuing with existing credentials...")

    # -------------------------------------------------------------
    # Step 2: Application Default Credentials (ADC)
    # -------------------------------------------------------------
    has_adc = has_adc_credentials()
    if has_adc and not should_login:
        console.print("[green]✓ Application Default Credentials (ADC) found.[/green]")
        reauth_adc = input("Refresh Application Default Credentials? [y/N]: ").strip().lower()
        should_adc = reauth_adc in ("y", "yes")
    else:
        console.print("\n[yellow]Configuring Application Default Credentials for Vertex AI APIs...[/yellow]")
        should_adc = True

    if should_adc:
        console.print("[cyan]Opening browser for Application Default Credentials (ADC) consent...[/cyan]")
        ok = run_gcloud_command(
            ["auth", "application-default", "login"],
            "Running 'gcloud auth application-default login'"
        )
        if not ok:
            print_warning("Application Default Credentials setup had warnings. Continuing...")

    # -------------------------------------------------------------
    # Step 3: Google Cloud Project ID
    # -------------------------------------------------------------
    current_proj = config.project_id or get_active_gcloud_project()
    proj_prompt = f"Enter Google Cloud Project ID [{current_proj}]: " if current_proj else "Enter Google Cloud Project ID: "
    user_proj = input(f"\n{proj_prompt}").strip()
    project_id = user_proj if user_proj else current_proj

    while not project_id:
        print_error("A Google Cloud Project ID is required.")
        project_id = input("Enter Google Cloud Project ID: ").strip()

    config.project_id = project_id

    # Update gcloud config project
    gcloud = get_gcloud_binary()
    if gcloud:
        try:
            subprocess.run([gcloud, "config", "set", "project", project_id], capture_output=True, timeout=5)
        except Exception:
            pass

    # -------------------------------------------------------------
    # Step 4: Vertex AI Location / Region
    # -------------------------------------------------------------
    current_loc = config.location or "us-central1"
    loc_prompt = f"Enter Vertex AI Location / Region [{current_loc}]: "
    user_loc = input(loc_prompt).strip()
    location = user_loc if user_loc else current_loc
    config.location = location

    # -------------------------------------------------------------
    # Step 5: Agent Engine Discovery & Selection
    # -------------------------------------------------------------
    console.print(f"\n[cyan]Checking deployed Agent Engines in [bold white]{project_id}[/bold white] ({location})...[/cyan]")
    chosen_engine_id = None
    chosen_app_name = None

    try:
        # Attempt to list engines using client
        from ae_cli.client import AgentEngineClient
        client = AgentEngineClient(config)
        engines = client.list_agent_engines()

        if engines:
            console.print(f"\n[green]✓ Found {len(engines)} deployed Agent Engine(s):[/green]")
            table = Table(box=box.ROUNDED, header_style="bold cyan")
            table.add_column("#", style="bold yellow", width=4)
            table.add_column("Display Name", style="bold white")
            table.add_column("Engine ID", style="cyan")
            table.add_column("Created", style="dim")

            for idx, eng in enumerate(engines, 1):
                eid = eng["name"].split("/")[-1]
                table.add_row(str(idx), eng.get("displayName", "Unnamed"), eid, eng.get("createTime", "N/A"))

            console.print(table)
            console.print(f"  [bold yellow]{len(engines) + 1}[/bold yellow]. Enter ID or name manually\n")

            choice = input(f"Select Agent Engine [1-{len(engines) + 1}] (default 1): ").strip()
            if not choice:
                choice = "1"

            try:
                choice_idx = int(choice)
                if 1 <= choice_idx <= len(engines):
                    selected = engines[choice_idx - 1]
                    chosen_engine_id = selected["name"].split("/")[-1]
                    chosen_app_name = selected.get("displayName", chosen_engine_id)
            except ValueError:
                pass

        else:
            console.print("[yellow]No deployed Agent Engines found in this project/location.[/yellow]")

    except Exception as e:
        console.print(f"[dim]Could not auto-fetch deployed engines: {e}[/dim]")

    if not chosen_engine_id:
        def_engine = config.engine_id or config.app_name or ""
        prompt_txt = f"Enter Agent Engine ID or App Display Name [{def_engine}]: " if def_engine else "Enter Agent Engine ID or App Display Name: "
        user_engine = input(prompt_txt).strip()
        final_engine = user_engine if user_engine else def_engine
        if final_engine:
            if final_engine.isdigit() or final_engine.startswith("projects/"):
                chosen_engine_id = final_engine
            else:
                chosen_app_name = final_engine

    if chosen_engine_id:
        config.engine_id = chosen_engine_id
    if chosen_app_name:
        config.app_name = chosen_app_name

    # -------------------------------------------------------------
    # Step 6: Save Configuration
    # -------------------------------------------------------------
    save_env_file(
        project_id=config.project_id,
        location=config.location,
        engine_id=config.engine_id,
        app_name=config.app_name,
    )
    config.save()

    # Success Summary
    summary_table = Table(box=box.SIMPLE_HEAVY, show_header=False)
    summary_table.add_column("Setting", style="bold yellow")
    summary_table.add_column("Value", style="bold green")

    summary_table.add_row("Google Cloud Project:", config.project_id)
    summary_table.add_row("Vertex AI Location:", config.location)
    summary_table.add_row("Target Agent Engine:", config.app_name or config.engine_id or "Auto-discover")
    summary_table.add_row("Configuration Saved:", ".env and ~/.ae/config.json")

    console.print()
    console.print(
        Panel(
            summary_table,
            title="[bold green]✓ Pre-Setup Completed Successfully![/bold green]",
            border_style="green",
            padding=(0, 2),
        )
    )
    console.print()

    return config
