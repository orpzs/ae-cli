"""Unit tests for event stream normalization."""

import unittest
from ae_cli.config import AEConfig
from ae_cli.client import AgentEngineClient, AgentStreamChunk


class TestStreamNormalization(unittest.TestCase):
    def setUp(self):
        cfg = AEConfig(project_id="dummy", location="us-central1", engine_id="123", token="mock_token")
        self.client = AgentEngineClient(cfg)

    def test_normalize_text_part(self):
        event = {
            "content": {
                "role": "model",
                "parts": [
                    {"text": "Hello world"}
                ]
            }
        }
        chunks = list(self.client._normalize_event(event))
        self.assertEqual(len(chunks), 1)
        self.assertEqual(chunks[0].text, "Hello world")
        self.assertIsNone(chunks[0].thought)

    def test_normalize_thought_part(self):
        # Format 1: thought=True with text
        event1 = {
            "content": {
                "parts": [
                    {"thought": True, "text": "Plan steps"}
                ]
            }
        }
        chunks1 = list(self.client._normalize_event(event1))
        self.assertEqual(len(chunks1), 1)
        self.assertEqual(chunks1[0].thought, "Plan steps")

        # Format 2: thought as string
        event2 = {
            "content": {
                "parts": [
                    {"thought": "Direct thought content"}
                ]
            }
        }
        chunks2 = list(self.client._normalize_event(event2))
        self.assertEqual(len(chunks2), 1)
        self.assertEqual(chunks2[0].thought, "Direct thought content")

    def test_normalize_function_call(self):
        event = {
            "content": {
                "parts": [
                    {
                        "function_call": {
                            "name": "search_db",
                            "args": {"query": "vertex ai"}
                        }
                    }
                ]
            }
        }
        chunks = list(self.client._normalize_event(event))
        self.assertEqual(len(chunks), 1)
        self.assertIsNotNone(chunks[0].function_call)
        self.assertEqual(chunks[0].function_call.name, "search_db")
        self.assertEqual(chunks[0].function_call.args["query"], "vertex ai")

    def test_normalize_function_response(self):
        event = {
            "content": {
                "parts": [
                    {
                        "function_response": {
                            "name": "search_db",
                            "response": {"results": [1, 2, 3]}
                        }
                    }
                ]
            }
        }
        chunks = list(self.client._normalize_event(event))
        self.assertEqual(len(chunks), 1)
        self.assertIsNotNone(chunks[0].function_response)
        self.assertEqual(chunks[0].function_response.name, "search_db")
        self.assertEqual(chunks[0].function_response.response["results"], [1, 2, 3])

    def test_normalize_error(self):
        event = {"error": {"message": "Resource exhausted"}}
        chunks = list(self.client._normalize_event(event))
        self.assertEqual(len(chunks), 1)
        self.assertEqual(chunks[0].error, "Resource exhausted")


if __name__ == "__main__":
    unittest.main()
