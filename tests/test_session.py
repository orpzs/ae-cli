"""Unit tests for session tracking and persistence."""

import unittest
import tempfile
from pathlib import Path
from ae_cli.session import SessionManager, ConversationTurn


class TestSession(unittest.TestCase):
    def test_session_turns(self):
        mgr = SessionManager(session_id="test_sess_01", user_id="test_user", engine_id="engine_mock")
        self.assertEqual(mgr.state.turn_count, 0)

        mgr.add_user_message("Hello Agent")
        self.assertEqual(mgr.state.turn_count, 1)
        self.assertEqual(mgr.state.turns[0].role, "user")
        self.assertEqual(mgr.state.turns[0].text, "Hello Agent")

        mgr.add_model_response(
            text="Hello user!",
            thoughts="Thinking about greeting...",
            tool_calls=[{"type": "call", "name": "greet"}],
        )
        self.assertEqual(mgr.state.turn_count, 2)
        self.assertEqual(mgr.state.turns[1].role, "model")
        self.assertEqual(mgr.state.turns[1].text, "Hello user!")
        self.assertEqual(mgr.state.turns[1].thoughts, "Thinking about greeting...")
        self.assertEqual(len(mgr.state.turns[1].tool_calls), 1)

    def test_session_reset(self):
        mgr = SessionManager(session_id="old_sess", user_id="u1", engine_id="e1")
        mgr.add_user_message("test")
        self.assertEqual(mgr.state.turn_count, 1)

        mgr.reset("new_sess")
        self.assertEqual(mgr.state.session_id, "new_sess")
        self.assertEqual(mgr.state.turn_count, 0)


if __name__ == "__main__":
    unittest.main()
