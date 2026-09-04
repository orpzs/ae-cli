"""Stream renderer for real-time visualization of agent events, thoughts, and tool executions."""

import time
import json
from typing import Generator, Optional, Tuple, List, Dict, Any
from rich.console import Console
from rich.live import Live
from rich.spinner import Spinner
from rich.text import Text
from rich.panel import Panel

from ae_cli.client import AgentStreamChunk, FunctionCall, FunctionResponse
from ae_cli.ui.console import console


class StreamRenderer:
    """Handles rendering of streaming chunks from the Agent Engine."""

    def __init__(
        self,
        show_thoughts: bool = True,
        show_tool_calls: bool = True,
        raw_mode: bool = False,
    ):
        self.show_thoughts = show_thoughts
        self.show_tool_calls = show_tool_calls
        self.raw_mode = raw_mode

    def render_stream(
        self,
        stream: Generator[AgentStreamChunk, None, None],
    ) -> Tuple[str, str, List[Dict[str, Any]]]:
        """Consumes the stream, renders tokens live to console, and returns captured data.

        Returns:
            Tuple[full_text, full_thoughts, tool_calls_list]
        """
        full_text = ""
        full_thoughts = ""
        tool_calls: List[Dict[str, Any]] = []

        in_thought_block = False
        text_started = False
        chunk_count = 0
        start_time = time.time()

        # Initial spinner while connecting
        with Live(
            Spinner("dots", text="[cyan]Connecting to Agent Engine...[/cyan]"),
            console=console,
            refresh_per_second=10,
            transient=True,
        ) as live:
            first_chunk = True
            for chunk in stream:
                chunk_count += 1
                if first_chunk:
                    live.stop()
                    first_chunk = False

                if self.raw_mode and chunk.raw:
                    console.print(
                        f"[dim cyan][RAW EVENT][/dim cyan] {json.dumps(chunk.raw)}"
                    )
                    continue

                if chunk.error:
                    console.print(f"\n[bold red]❌ Error:[/bold red] {chunk.error}")
                    continue

                # 1. Thought block
                if chunk.thought:
                    if self.show_thoughts:
                        if not in_thought_block:
                            console.print("\n[dim cyan]🧠 Thinking...[/dim cyan]")
                            in_thought_block = True
                        console.print(f"[dim italic]{chunk.thought}[/dim italic]", end="", highlight=False)
                    full_thoughts += chunk.thought

                # 2. Tool / Function Call
                elif chunk.function_call:
                    if in_thought_block:
                        console.print()
                        in_thought_block = False

                    fc = chunk.function_call
                    tool_calls.append({"type": "call", "name": fc.name, "args": fc.args})
                    if self.show_tool_calls:
                        args_str = json.dumps(fc.args, indent=2) if fc.args else "{}"
                        console.print(
                            f"\n[bold yellow]⚙️  Action:[/bold yellow] [bold white]{fc.name}[/bold white]"
                        )
                        if fc.args:
                            console.print(f"[dim]{args_str}[/dim]")

                # 3. Tool / Function Result
                elif chunk.function_response:
                    if in_thought_block:
                        console.print()
                        in_thought_block = False

                    fr = chunk.function_response
                    tool_calls.append({"type": "response", "name": fr.name, "response": fr.response})
                    if self.show_tool_calls:
                        resp_str = json.dumps(fr.response)
                        if len(resp_str) > 200:
                            resp_str = resp_str[:200] + "... [truncated]"
                        console.print(
                            f"[bold green]✓ Result from {fr.name}:[/bold green] [dim]{resp_str}[/dim]"
                        )

                # 4. Agent Response Text
                elif chunk.text:
                    if in_thought_block:
                        console.print("\n")
                        in_thought_block = False

                    if not text_started:
                        text_started = True

                    console.print(chunk.text, end="", highlight=False)
                    full_text += chunk.text

        # Ensure newline after streaming finishes
        if text_started or in_thought_block:
            console.print()

        # Display timing stats
        elapsed = time.time() - start_time
        if chunk_count > 0:
            console.print(
                f"[dim]⏱  {elapsed:.2f}s | {chunk_count} events[/dim]\n"
            )

        return full_text, full_thoughts, tool_calls
