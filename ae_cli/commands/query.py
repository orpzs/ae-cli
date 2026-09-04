"""Single-shot query execution for pipelines, automation, or quick terminal checks."""

import sys
import json
from typing import Optional
from ae_cli.config import AEConfig
from ae_cli.client import AgentEngineClient
from ae_cli.ui.renderer import StreamRenderer
from ae_cli.ui.console import console, print_error


def query_command(
    config: AEConfig,
    prompt: Optional[str] = None,
    as_json: bool = False,
):
    """Executes a single stream query and outputs the response."""
    # If no prompt argument, check stdin for piped input
    if not prompt:
        if not sys.stdin.isatty():
            prompt = sys.stdin.read().strip()
        else:
            print_error("No prompt provided. Pass a prompt string or pipe stdin.", title="Missing Input")
            sys.exit(1)

    if not prompt:
        print_error("Prompt is empty.", title="Empty Input")
        sys.exit(1)

    try:
        client = AgentEngineClient(config)
        client.resolve_engine()
    except Exception as e:
        print_error(str(e), title="Configuration / Auth Error")
        sys.exit(1)

    renderer = StreamRenderer(
        show_thoughts=config.show_thoughts and not as_json,
        show_tool_calls=config.show_tool_calls and not as_json,
        raw_mode=config.raw_mode,
    )

    try:
        stream = client.stream_query(
            message=prompt,
            user_id=config.user_id,
            session_id=config.session_id,
        )

        if as_json:
            events = []
            for chunk in stream:
                if chunk.raw:
                    events.append(chunk.raw)
                elif chunk.text:
                    events.append({"text": chunk.text})
            print(json.dumps(events, indent=2))
        else:
            renderer.render_stream(stream)
    except KeyboardInterrupt:
        sys.exit(130)
    except Exception as e:
        print_error(str(e), title="Query Execution Failed")
        sys.exit(1)
