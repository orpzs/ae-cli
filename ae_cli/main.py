"""CLI entrypoint for ae-cli (Agent Engine Streaming CLI)."""

import sys
import click
from rich.table import Table
from rich import box

from ae_cli.config import AEConfig
from ae_cli.ui.console import console
from ae_cli.commands.chat import chat_command
from ae_cli.commands.query import query_command
from ae_cli.commands.list_agents import list_agents_command
from ae_cli.commands.info import info_command
from ae_cli.session import SessionManager


from ae_cli import __version__


@click.group(invoke_without_command=True)
@click.version_option(__version__, "-v", "--version", message="ae-cli %(version)s")
@click.option("--project", "-p", help="Google Cloud Project ID")
@click.option("--location", "-l", help="Vertex AI region (default: us-central1)")
@click.option("--engine", "-e", help="Agent Engine ID or full resource name")
@click.option("--app", "-a", help="Agent Engine display name (APP_NAME)")
@click.option("--user", "-u", help="User ID for session management")
@click.option("--session", "-s", help="Session ID to resume")
@click.option("--token", "-t", help="OAuth2 Access Token override")
@click.option("--no-thoughts", is_flag=True, help="Hide model thinking/reasoning blocks")
@click.option("--raw", is_flag=True, help="Stream raw event JSON payloads")
@click.option("--setup", "force_setup", is_flag=True, help="Run Google Cloud authentication & agent setup wizard")
@click.pass_context
def cli(ctx, project, location, engine, app, user, session, token, no_thoughts, raw, force_setup):
    """ae-cli - Real-time conversational CLI for Vertex AI Agent Engine.

    Run interactively in conversational mode or pipe queries directly.
    """
    ctx.ensure_object(dict)
    ctx.obj["force_setup"] = force_setup
    ctx.obj["config"] = AEConfig.load(
        project_id=project,
        location=location,
        engine_id=engine,
        app_name=app,
        user_id=user,
        session_id=session,
        token=token,
        show_thoughts=not no_thoughts,
        raw_mode=raw,
    )
    if ctx.invoked_subcommand is None:
        ctx.invoke(chat)


@cli.command("setup")
@click.pass_context
def setup_cmd(ctx):
    """Run interactive Google Cloud authentication and Agent Engine setup wizard."""
    from ae_cli.setup import run_setup
    config: AEConfig = ctx.obj["config"]
    updated_config = run_setup(config)
    start_chat = input("Start interactive chat session now? [Y/n]: ").strip().lower()
    if start_chat not in ("n", "no"):
        chat_command(updated_config)


@cli.command("chat")
@click.pass_context
def chat(ctx):
    """Start interactive conversational chat session (default mode)."""
    config: AEConfig = ctx.obj["config"]
    force_setup: bool = ctx.obj.get("force_setup", False)
    chat_command(config, force_setup=force_setup)


@cli.command("query")
@click.argument("prompt", required=False)
@click.option("--json", "as_json", is_flag=True, help="Output raw JSON array of events")
@click.pass_context
def query(ctx, prompt, as_json):
    """Send a single query and stream the response (supports piping)."""
    config: AEConfig = ctx.obj["config"]
    query_command(config, prompt=prompt, as_json=as_json)


@cli.command("list")
@click.pass_context
def list_agents(ctx):
    """List all deployed Agent Engines in the current project and region."""
    config: AEConfig = ctx.obj["config"]
    list_agents_command(config)


@cli.command("info")
@click.argument("engine_id", required=False)
@click.pass_context
def info(ctx, engine_id):
    """Display detailed specifications and operations of an Agent Engine."""
    config: AEConfig = ctx.obj["config"]
    info_command(config, engine_id=engine_id)


@cli.command("sessions")
@click.argument("engine_id", required=False)
@click.pass_context
def sessions(ctx, engine_id):
    """List locally saved conversation sessions."""
    config: AEConfig = ctx.obj["config"]
    target_engine = engine_id or config.engine_id
    saved = SessionManager.list_saved_sessions(target_engine)

    if not saved:
        console.print("[dim]No saved sessions found.[/dim]\n")
        return

    table = Table(title="Conversation Sessions", box=box.ROUNDED, header_style="bold cyan")
    table.add_column("Session ID", style="bold yellow")
    table.add_column("Agent Engine", style="white")
    table.add_column("User ID", style="cyan")
    table.add_column("Turns", style="green")

    for s in saved:
        table.add_row(
            s["session_id"],
            s.get("engine_id", "default"),
            s.get("user_id", "default"),
            str(s.get("turns", 0)),
        )

    console.print()
    console.print(table)
    console.print("\n[dim]To resume a session: [bold white]ae chat --session <Session ID>[/bold white][/dim]\n")


@cli.command("config")
@click.pass_context
def show_config(ctx):
    """Show current resolved configuration."""
    config: AEConfig = ctx.obj["config"]
    table = Table(title="Active Configuration", box=box.ROUNDED, header_style="bold cyan")
    table.add_column("Field", style="bold yellow")
    table.add_column("Value", style="bold white")

    table.add_row("Project ID", config.project_id or "[dim]Not set (detecting via ADC/gcloud)[/dim]")
    table.add_row("Location", config.location)
    table.add_row("Agent Engine ID", config.engine_id or "[dim]None (auto-discover or specify)[/dim]")
    table.add_row("App Name Filter", config.app_name or "[dim]None[/dim]")
    table.add_row("User ID", config.user_id)
    table.add_row("Active Session ID", config.session_id or "[dim]Auto-generate per session[/dim]")
    table.add_row("Show Thoughts", str(config.show_thoughts))
    table.add_row("Raw Mode", str(config.raw_mode))
    table.add_row("API Host", config.get_api_host())

    console.print()
    console.print(table)
    console.print()


def main():
    cli(obj={})


if __name__ == "__main__":
    main()
