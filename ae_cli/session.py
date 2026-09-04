"""Session manager for tracking conversation history and session persistence."""

import json
import time
from pathlib import Path
from dataclasses import dataclass, field, asdict
from typing import List, Dict, Any, Optional

SESSIONS_DIR = Path.home() / ".ae" / "sessions"


@dataclass
class ConversationTurn:
    role: str  # "user" or "model"
    text: str
    thoughts: Optional[str] = None
    tool_calls: List[Dict[str, Any]] = field(default_factory=list)
    timestamp: float = field(default_factory=time.time)


@dataclass
class SessionState:
    session_id: str
    user_id: str
    engine_id: Optional[str] = None
    created_at: float = field(default_factory=time.time)
    turns: List[ConversationTurn] = field(default_factory=list)

    @property
    def turn_count(self) -> int:
        return len(self.turns)


class SessionManager:
    """Manages active session state, turn history, and disk persistence."""

    def __init__(self, session_id: str, user_id: str, engine_id: Optional[str] = None):
        self.state = SessionState(
            session_id=session_id,
            user_id=user_id,
            engine_id=engine_id or "unknown",
        )
        self.storage_dir = SESSIONS_DIR / (self.state.engine_id or "default")
        self.storage_dir.mkdir(parents=True, exist_ok=True)
        self._load_if_exists()

    def _file_path(self) -> Path:
        return self.storage_dir / f"{self.state.session_id}.json"

    def _load_if_exists(self):
        fp = self._file_path()
        if fp.exists():
            try:
                with open(fp, "r", encoding="utf-8") as f:
                    data = json.load(f)
                    turns = [ConversationTurn(**t) for t in data.get("turns", [])]
                    self.state.turns = turns
                    self.state.created_at = data.get("created_at", self.state.created_at)
            except Exception:
                pass

    def add_user_message(self, text: str):
        self.state.turns.append(ConversationTurn(role="user", text=text))
        self.save()

    def add_model_response(
        self,
        text: str,
        thoughts: Optional[str] = None,
        tool_calls: Optional[List[Dict[str, Any]]] = None,
    ):
        self.state.turns.append(
            ConversationTurn(
                role="model",
                text=text,
                thoughts=thoughts,
                tool_calls=tool_calls or [],
            )
        )
        self.save()

    def save(self):
        try:
            with open(self._file_path(), "w", encoding="utf-8") as f:
                data = asdict(self.state)
                json.dump(data, f, indent=2)
        except Exception:
            pass

    def reset(self, new_session_id: str):
        """Starts a new clean session."""
        self.state = SessionState(
            session_id=new_session_id,
            user_id=self.state.user_id,
            engine_id=self.state.engine_id,
        )
        self.save()

    @classmethod
    def list_saved_sessions(cls, engine_id: Optional[str] = None) -> List[Dict[str, Any]]:
        """Lists previously saved sessions."""
        results = []
        base_dir = SESSIONS_DIR / (engine_id or "default") if engine_id else SESSIONS_DIR
        if not base_dir.exists():
            return []

        for p in base_dir.glob("**/*.json"):
            try:
                with open(p, "r", encoding="utf-8") as f:
                    data = json.load(f)
                    results.append({
                        "session_id": data.get("session_id"),
                        "user_id": data.get("user_id"),
                        "engine_id": data.get("engine_id"),
                        "turns": len(data.get("turns", [])),
                        "created_at": data.get("created_at"),
                        "path": str(p),
                    })
            except Exception:
                continue
        return results
