"""Interactive prompt handler with command history and slash command completion."""

import os
from pathlib import Path
from typing import List, Optional

try:
    from prompt_toolkit import PromptSession
    from prompt_toolkit.history import FileHistory
    from prompt_toolkit.completion import WordCompleter
    from prompt_toolkit.styles import Style
    from prompt_toolkit.formatted_text import HTML
    PROMPT_TOOLKIT_AVAILABLE = True
except ImportError:
    PROMPT_TOOLKIT_AVAILABLE = False

SLASH_COMMANDS = [
    "/help",
    "/new",
    "/session",
    "/sessions",
    "/switch",
    "/history",
    "/info",
    "/tools",
    "/thoughts",
    "/raw",
    "/clear",
    "/exit",
    "/quit",
]

PROMPT_STYLE = Style.from_dict({
    "prompt-prefix": "#00d7ff bold",
    "prompt-session": "#5f87af",
    "prompt-symbol": "#00ffaf bold",
})


class InteractivePrompt:
    """Provides prompt_toolkit powered interactive prompt or standard input fallback."""

    def __init__(self, session_id: Optional[str] = None):
        self.session_id = session_id or ""
        self._session: Optional[Any] = None

        if PROMPT_TOOLKIT_AVAILABLE:
            history_path = Path.home() / ".ae" / "history"
            history_path.parent.mkdir(parents=True, exist_ok=True)

            completer = WordCompleter(SLASH_COMMANDS, ignore_case=True, sentence=True)

            self._session = PromptSession(
                history=FileHistory(str(history_path)),
                completer=completer,
                style=PROMPT_STYLE,
            )

    def update_session_id(self, session_id: str):
        self.session_id = session_id

    def get_input(self) -> str:
        """Prompts user for input, handling EOF and Interrupts cleanly."""
        short_session = self.session_id[-8:] if len(self.session_id) > 8 else self.session_id
        session_label = f"({short_session})" if short_session else ""

        if PROMPT_TOOLKIT_AVAILABLE and self._session:
            prompt_html = HTML(
                f"<prompt-prefix>ae-cli</prompt-prefix> "
                f"<prompt-session>{session_label}</prompt-session> "
                f"<prompt-symbol>❯</prompt-symbol> "
            )
            return self._session.prompt(prompt_html).strip()
        else:
            # Fallback
            prefix = f"ae-cli {session_label} ❯ " if session_label else "ae-cli ❯ "
            return input(prefix).strip()
