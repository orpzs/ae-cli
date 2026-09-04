"""Client for communicating with Vertex AI Agent Engines (Reasoning Engines).

Supports streaming responses over HTTP/REST SSE and provides robust event normalization
(handling text, thoughts, function calls, and session management).
"""

import json
import logging
import uuid
from dataclasses import dataclass, field
from typing import Generator, List, Dict, Any, Optional
import httpx

from ae_cli.config import AEConfig
from ae_cli.auth import get_access_token

logger = logging.getLogger(__name__)


@dataclass
class FunctionCall:
    name: str
    args: Dict[str, Any] = field(default_factory=dict)


@dataclass
class FunctionResponse:
    name: str
    response: Dict[str, Any] = field(default_factory=dict)


@dataclass
class AgentStreamChunk:
    """Normalized stream chunk yielded during an agent query."""
    text: Optional[str] = None
    thought: Optional[str] = None
    function_call: Optional[FunctionCall] = None
    function_response: Optional[FunctionResponse] = None
    raw: Optional[Dict[str, Any]] = None
    error: Optional[str] = None


class AgentEngineClient:
    """Direct REST and SSE client for Vertex AI Agent Engine."""

    def __init__(self, config: AEConfig):
        self.config = config
        self._token: Optional[str] = config.token
        self._detected_project: Optional[str] = None
        self._ensure_auth()

    def _ensure_auth(self):
        """Resolves authentication token and project ID if not already set."""
        if not self._token:
            token, detected_proj = get_access_token(self.config.token)
            self._token = token
            if not self.config.project_id and detected_proj:
                self.config.project_id = detected_proj

    def _get_headers(self) -> Dict[str, str]:
        """Headers required for Vertex AI REST calls."""
        self._ensure_auth()
        return {
            "Authorization": f"Bearer {self._token}",
            "Content-Type": "application/json; charset=utf-8",
            "Accept": "text/event-stream, application/json",
        }

    def list_agent_engines(self) -> List[Dict[str, Any]]:
        """Lists all deployed Agent Engines (Reasoning Engines) in the configured project/location."""
        if not self.config.project_id:
            raise ValueError("Google Cloud Project ID is required to list Agent Engines.")

        url = (
            f"{self.config.get_api_host()}/{self.config.api_version}/"
            f"projects/{self.config.project_id}/locations/{self.config.location}/reasoningEngines"
        )

        with httpx.Client(timeout=30.0) as client:
            resp = client.get(url, headers=self._get_headers())
            if resp.status_code != 200:
                raise RuntimeError(
                    f"Failed to list Agent Engines ({resp.status_code}): {resp.text}"
                )
            data = resp.json()
            return data.get("reasoningEngines", [])

    def get_agent_engine(self, engine_id: Optional[str] = None) -> Dict[str, Any]:
        """Retrieves details of a specific deployed Agent Engine."""
        target_id = engine_id or self.config.engine_id
        if not target_id:
            raise ValueError("Agent Engine ID is required.")

        resource_name = target_id
        if not resource_name.startswith("projects/"):
            resource_name = f"projects/{self.config.project_id}/locations/{self.config.location}/reasoningEngines/{target_id}"

        url = f"{self.config.get_api_host()}/{self.config.api_version}/{resource_name}"

        with httpx.Client(timeout=30.0) as client:
            resp = client.get(url, headers=self._get_headers())
            if resp.status_code != 200:
                raise RuntimeError(
                    f"Failed to get Agent Engine details ({resp.status_code}): {resp.text}"
                )
            return resp.json()

    def resolve_engine(self) -> str:
        """Finds or validates the target Agent Engine resource name."""
        if self.config.engine_id:
            if self.config.engine_id.startswith("projects/"):
                return self.config.engine_id
            return f"projects/{self.config.project_id}/locations/{self.config.location}/reasoningEngines/{self.config.engine_id}"

        # If app_name is provided, search by display name
        if self.config.app_name:
            engines = self.list_agent_engines()
            for eng in engines:
                display = eng.get("displayName", "")
                if display.lower() == self.config.app_name.lower():
                    self.config.engine_id = eng["name"].split("/")[-1]
                    return eng["name"]

            # Partial match
            for eng in engines:
                if self.config.app_name.lower() in eng.get("displayName", "").lower():
                    self.config.engine_id = eng["name"].split("/")[-1]
                    return eng["name"]

            names = [e.get("displayName", "Unnamed") for e in engines]
            raise ValueError(
                f"No Agent Engine found matching '{self.config.app_name}'. Available: {names}"
            )

        raise ValueError(
            "No Agent Engine specified. Provide --engine <ID>, set AGENT_ENGINE_ID, or APP_NAME in .env"
        )

    def create_session(self, user_id: Optional[str] = None) -> Dict[str, Any]:
        """Attempts to create a new session on the remote Agent Engine.

        If the deployed agent implements create_session, calls it.
        Otherwise falls back to generating a local session identifier.
        """
        user_id = user_id or self.config.user_id
        resource_name = self.resolve_engine()

        url = f"{self.config.get_api_host()}/{self.config.api_version}/{resource_name}:query"
        payload = {
            "classMethod": "create_session",
            "input": {
                "user_id": user_id
            }
        }

        try:
            with httpx.Client(timeout=30.0) as client:
                resp = client.post(url, headers=self._get_headers(), json=payload)
                if resp.status_code == 200:
                    data = resp.json()
                    # Output can be dict with 'id' or session object
                    output = data.get("output", data)
                    if isinstance(output, dict) and "id" in output:
                        return output
                    if isinstance(output, str):
                        return {"id": output}
                    return {"id": str(output)}
        except Exception as e:
            logger.debug(f"Remote create_session not supported or failed: {e}")

        # Fallback to local session ID
        local_id = f"s_{uuid.uuid4().hex[:8]}"
        return {"id": local_id, "user_id": user_id, "local": True}

    def stream_query(
        self,
        message: str,
        user_id: Optional[str] = None,
        session_id: Optional[str] = None,
        class_method: str = "stream_query",
        extra_inputs: Optional[Dict[str, Any]] = None,
    ) -> Generator[AgentStreamChunk, None, None]:
        """Streams queries to the deployed Agent Engine and yields normalized chunks.

        Handles:
        - text deltas
        - thought tokens (Gemini 2.0 / 2.5 thought parts)
        - function calls & tool executions
        - JSON stream parsing / SSE events
        """
        resource_name = self.resolve_engine()
        user_id = user_id or self.config.user_id
        session_id = session_id or self.config.session_id

        # Prepare payload - accommodates standard ADK and custom reasoning engine signatures
        query_input: Dict[str, Any] = {
            "message": message,
            "user_id": user_id,
        }
        if session_id:
            query_input["session_id"] = session_id

        # Merge additional custom inputs if any
        if extra_inputs:
            query_input.update(extra_inputs)

        # Also support engines expecting "input" or "prompt" instead of "message"
        query_input["input"] = message

        payload = {
            "classMethod": class_method,
            "input": query_input,
        }

        url = f"{self.config.get_api_host()}/{self.config.api_version}/{resource_name}:streamQuery"

        with httpx.Client(timeout=180.0) as client:
            with client.stream("POST", url, headers=self._get_headers(), json=payload) as response:
                if response.status_code != 200:
                    error_text = response.read().decode("utf-8", errors="replace")
                    yield AgentStreamChunk(
                        error=f"Agent Engine API returned HTTP {response.status_code}: {error_text}"
                    )
                    return

                buffer = ""
                for raw_chunk in response.iter_raw():
                    if not raw_chunk:
                        continue

                    chunk_str = raw_chunk.decode("utf-8", errors="replace")
                    buffer += chunk_str

                    # Parse Server-Sent Events or newline-delimited JSON objects
                    while "\n" in buffer:
                        line, buffer = buffer.split("\n", 1)
                        line = line.strip()
                        if not line:
                            continue

                        # Strip SSE "data:" prefix if present
                        if line.startswith("data:"):
                            line = line[5:].strip()

                        if not line or line == "[DONE]":
                            continue

                        try:
                            parsed_json = json.loads(line)
                            for normalized in self._normalize_event(parsed_json):
                                yield normalized
                        except json.JSONDecodeError:
                            # Incomplete JSON line, put back to buffer
                            buffer = line + "\n" + buffer
                            break

                # Process any trailing data left in buffer
                if buffer.strip():
                    line = buffer.strip()
                    if line.startswith("data:"):
                        line = line[5:].strip()
                    try:
                        parsed_json = json.loads(line)
                        for normalized in self._normalize_event(parsed_json):
                            yield normalized
                    except json.JSONDecodeError:
                        pass

    def _normalize_event(self, event: Any) -> Generator[AgentStreamChunk, None, None]:
        """Normalizes various Vertex AI / ADK event structures into AgentStreamChunk."""
        if not isinstance(event, dict):
            yield AgentStreamChunk(raw={"value": event})
            return

        # 1. Check for errors
        if "error" in event:
            err = event["error"]
            msg = err.get("message", str(err)) if isinstance(err, dict) else str(err)
            yield AgentStreamChunk(error=msg, raw=event)
            return

        # 2. Standard Vertex AI / ADK event format:
        # event["content"]["parts"] -> list of parts
        content = event.get("content")
        if isinstance(content, dict) and "parts" in content:
            for part in content["parts"]:
                if not isinstance(part, dict):
                    continue

                # Model Thought / Reasoning
                if part.get("thought") is True and "text" in part:
                    yield AgentStreamChunk(thought=part["text"], raw=event)
                elif "thought" in part and isinstance(part["thought"], str):
                    yield AgentStreamChunk(thought=part["thought"], raw=event)

                # Function / Tool Call
                elif "function_call" in part or "functionCall" in part:
                    fc = part.get("function_call") or part.get("functionCall")
                    yield AgentStreamChunk(
                        function_call=FunctionCall(
                            name=fc.get("name", "unknown_tool"),
                            args=fc.get("args", {})
                        ),
                        raw=event
                    )

                # Function / Tool Result
                elif "function_response" in part or "functionResponse" in part:
                    fr = part.get("function_response") or part.get("functionResponse")
                    yield AgentStreamChunk(
                        function_response=FunctionResponse(
                            name=fr.get("name", "unknown_tool"),
                            response=fr.get("response", {})
                        ),
                        raw=event
                    )

                # Streaming text
                elif "text" in part:
                    yield AgentStreamChunk(text=part["text"], raw=event)

            return

        # 3. Direct text delta or message delta
        if "text" in event and isinstance(event["text"], str):
            yield AgentStreamChunk(text=event["text"], raw=event)
            return

        if "message" in event and isinstance(event["message"], str):
            yield AgentStreamChunk(text=event["message"], raw=event)
            return

        # 4. Fallback: yield as raw event
        yield AgentStreamChunk(raw=event)
