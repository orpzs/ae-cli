"""Interactive conversational REPL loop for conversing with deployed Agent Engines."""

import sys
import json
from rich.table import Table
from rich.panel import Panel
from rich.text import Text
from rich import box

from ae_cli.config import AEConfig
from ae_cli.client import AgentEngineClient
from ae_cli.session import SessionManager
from ae_cli.ui.console import console, print_banner, print_info_box, print_error
from ae_cli.ui.renderer import StreamRenderer
from ae_cli.ui.prompt import InteractivePrompt


def print_help_menu():
    """Prints available slash commands and tips."""
    table = Table(box=box.ROUNDED, show_header=True, header_style="bold cyan")
    table.add_column("Command", style="bold yellow", width=16)
    table.add_column("Description", style="white")

    commands = [
        ("/help", "Show this help menu"),
        ("/new", "Start a new conversation session on the Agent Engine"),
        ("/session", "View current session details and turn count"),
        ("/sessions", "List all locally saved sessions for this agent"),
        ("/switch <id>", "Switch to an existing conversation session"),
        ("/history", "View message history of the current session"),
        ("/info", "Inspect deployed Agent Engine metadata and specs"),
        ("/tools", "List tools/operations exposed by the agent"),
        ("/thoughts", "Toggle visibility of model thinking/reasoning blocks"),
        ("/raw", "Toggle raw JSON event streaming (useful for debugging)"),
        ("/clear", "Clear the terminal screen"),
        ("/exit or /quit", "Exit the interactive session"),
    ]

    for cmd, desc in commands:
        table.add_row(cmd, desc)

    console.print(Panel(table, title="[bold cyan]Available Slash Commands[/bold cyan]", border_style="cyan"))
    console.print("[dim]Tip: Use Up/Down arrows to navigate previous prompt history.[/dim]\n")


def chat_command(config: AEConfig):
    """Starts the interactive chat loop with the deployed Agent Engine."""
    try:
        client = AgentEngineClient(config)
    except Exception as e:
        print_error(str(e), title="Authentication / Config Error")
        sys.exit(1)

    # Resolve target agent engine
    try:
        engine_resource = client.resolve_engine()
        engine_id = engine_resource.split("/")[-1]
    except ValueError:
        # Try to list available engines and auto-select or guide user
        try:
            engines = client.list_agent_engines()
            if not engines:
                print_error(
                    f"No deployed Agent Engines found in project '{config.project_id}' ({config.location}).\n"
                    f"Deploy an agent first using vertexai.agent_engines.create()",
                    title="No Agent Engines Found",
                )
                sys.exit(1)
            elif len(engines) == 1:
                eng = engines[0]
                config.engine_id = eng["name"].split("/")[-1]
                config.app_name = eng.get("displayName", config.engine_id)
                engine_resource = eng["name"]
                engine_id = config.engine_id
                console.print(f"[cyan]Auto-selected sole deployed Agent Engine:[/cyan] [bold white]{config.app_name}[/bold white]")
            else:
                console.print(f"\n[bold cyan]Found multiple Agent Engines in {config.project_id}:[/bold cyan]")
                for idx, eng in enumerate(engines, 1):
                    console.print(f"  [bold yellow]{idx}[/bold yellow]. {eng.get('displayName')} [dim]({eng['name'].split('/')[-1]})[/dim]")
                console.print("\n[white]Specify one using:[/white] [cyan]ae chat --engine <ID>[/cyan] or [cyan]--app <NAME>[/cyan]\n")
                sys.exit(0)
        except Exception as e:
            print_error(str(e), title="Failed to resolve Agent Engine")
            sys.exit(1)

    # Obtain or create session
    if not config.session_id:
        try:
            session_data = client.create_session(user_id=config.user_id)
            config.session_id = session_data.get("id", f"s_{config.user_id}")
        except Exception as e:
            config.session_id = f"sess_local_{config.user_id}"

    # Initialize session manager, prompt, and renderer
    session_mgr = SessionManager(
        session_id=config.session_id,
        user_id=config.user_id,
        engine_id=engine_id,
    )

    prompt = InteractivePrompt(session_id=config.session_id)
    renderer = StreamRenderer(
        show_thoughts=config.show_thoughts,
        show_tool_calls=config.show_tool_calls,
        raw_mode=config.raw_mode,
    )

    # Display start banner
    print_banner(
        project_id=config.project_id,
        location=config.location,
        engine_name=config.app_name or engine_id,
        session_id=config.session_id,
        user_id=config.user_id,
    )

    # Conversational Loop
    while True:
        try:
            user_input = prompt.get_input()
        except KeyboardInterrupt:
            console.print("\n[dim]Use /exit to quit.[/dim]")
            continue
        except EOFError:
            console.print("\n[cyan]Goodbye![/cyan]")
            break

        if not user_input:
            continue

        # Handle slash commands
        lower_input = user_input.lower()
        if lower_input in ("/exit", "/quit", "exit", "quit"):
            console.print("[bold cyan]Ending session. Goodbye![/bold cyan]")
            break

        elif lower_input == "/help":
            print_help_menu()
            continue

        elif lower_input == "/clear":
            console.clear()
            continue

        elif lower_input == "/thoughts":
            renderer.show_thoughts = not renderer.show_thoughts
            state_str = "visible" if renderer.show_thoughts else "hidden"
            console.print(f"[cyan]🧠 Thought visibility:[/cyan] [bold]{state_str}[/bold]\n")
            continue

        elif lower_input == "/raw":
            renderer.raw_mode = not renderer.raw_mode
            state_str = "enabled" if renderer.raw_mode else "disabled"
            console.print(f"[cyan]Raw event stream mode:[/cyan] [bold]{state_str}[/bold]\n")
            continue

        elif lower_input == "/session":
            console.print(
                Panel(
                    f"[bold]Session ID:[/bold] {session_mgr.state.session_id}\n"
                    f"[bold]User ID:[/bold] {session_mgr.state.user_id}\n"
                    f"[bold]Engine ID:[/bold] {session_mgr.state.engine_id}\n"
                    f"[bold]Turn Count:[/bold] {session_mgr.state.turn_count}",
                    title="[bold cyan]Session Details[/bold cyan]",
                    border_style="cyan",
                )
            )
            continue

        elif lower_input == "/sessions":
            sessions = SessionManager.list_saved_sessions(engine_id)
            if not sessions:
                console.print("[dim]No saved sessions found for this engine.[/dim]\n")
            else:
                table = Table(box=box.ROUNDED, header_style="bold cyan")
                table.add_column("Session ID", style="bold yellow")
                table.add_column("User ID", style="white")
                table.add_column("Turns", style="green")
                table.add_column("Created", style="dim")
                for s in sessions:
                    table.add_row(
                        s["session_id"],
                        s["user_id"],
                        str(s["turns"]),
                        str(s["created_at"]),
                    )
                console.print(table)
            continue

        elif lower_input.startswith("/switch"):
            parts = user_input.split(maxsplit=1)
            if len(parts) < 2:
                console.print("[yellow]Usage: /switch <session_id>[/yellow]\n")
                continue
            new_id = parts[1].strip()
            config.session_id = new_id
            session_mgr = SessionManager(
                session_id=new_id,
                user_id=config.user_id,
                engine_id=engine_id,
            )
            prompt.update_session_id(new_id)
            console.print(f"[green]✓ Switched to session:[/green] [bold white]{new_id}[/bold white]\n")
            continue

        elif lower_input == "/new":
            try:
                new_session_data = client.create_session(user_id=config.user_id)
                new_id = new_session_data.get("id", f"s_{config.user_id}")
            except Exception:
                new_id = f"s_{config.user_id}"
            config.session_id = new_id
            session_mgr.reset(new_id)
            prompt.update_session_id(new_id)
            console.print(f"[green]✓ Started new conversation session:[/green] [bold white]{new_id}[/bold white]\n")
            continue

        elif lower_input == "/history":
            if not session_mgr.state.turns:
                console.print("[dim]No messages in current session yet.[/dim]\n")
            else:
                for idx, turn in enumerate(session_mgr.state.turns, 1):
                    role_color = "yellow" if turn.role == "user" else "green"
                    role_icon = "👤 User" if turn.role == "user" else "🤖 Agent"
                    console.print(f"[bold {role_color}]{role_icon} (#{idx}):[/bold {role_color}]")
                    if turn.thoughts:
                        console.print(f"[dim italic]🧠 Thoughts: {turn.thoughts}[/dim italic]")
                    console.print(f"{turn.text}\n")
            continue

        elif lower_input == "/info":
            try:
                details = client.get_agent_engine(engine_id)
                spec = details.get("spec", {})
                methods = spec.get("classMethods", [])
                method_names = [m.get("name", "") for m in methods if isinstance(m, dict)]
                console.print(
                    Panel(
                        f"[bold]Display Name:[/bold] {details.get('displayName', 'N/A')}\n"
                        f"[bold]Resource Name:[/bold] {details.get('name', 'N/A')}\n"
                        f"[bold]Created:[/bold] {details.get('createTime', 'N/A')}\n"
                        f"[bold]Updated:[/bold] {details.get('updateTime', 'N/A')}\n"
                        f"[bold]Available Operations:[/bold] {', '.join(method_names) if method_names else 'query, stream_query'}",
                        title="[bold cyan]Agent Engine Specifications[/bold cyan]",
                        border_style="cyan",
                    )
                )
            except Exception as e:
                console.print(f"[red]Failed to fetch info: {e}[/red]\n")
            continue

        elif lower_input == "/tools":
            try:
                details = client.get_agent_engine(engine_id)
                spec = details.get("spec", {})
                methods = spec.get("classMethods", [])
                table = Table(box=box.ROUNDED, header_style="bold cyan")
                table.add_column("Operation / Method", style="bold yellow")
                table.add_column("Parameters", style="dim")
                for m in methods:
                    if isinstance(m, dict):
                        params = m.get("parameters", {}).get("properties", {})
                        param_names = ", ".join(params.keys()) if params else "None"
                        table.add_row(m.get("name", ""), param_names)
                console.print(table)
            except Exception as e:
                console.print(f"[red]Failed to fetch tools: {e}[/red]\n")
            continue

        # Standard conversation turn
        session_mgr.add_user_message(user_input)

        try:
            stream = client.stream_query(
                message=user_input,
                user_id=config.user_id,
                session_id=config.session_id,
            )
            full_text, full_thoughts, tool_calls = renderer.render_stream(stream)
            session_mgr.add_model_response(
                text=full_text,
                thoughts=full_thoughts if full_thoughts else None,
                tool_calls=tool_calls if tool_calls else None,
            )
        except KeyboardInterrupt:
            console.print("\n[yellow]Query interrupted by user.[/yellow]\n")
        except Exception as e:
            print_error(str(e), title="Stream Query Error")
