"""Configuration loader for ae-cli."""

import os
import json
from pathlib import Path
from dataclasses import dataclass, field, asdict
from typing import Optional

try:
    from dotenv import load_dotenv
    # Load .env from current directory or parents
    load_dotenv()
except ImportError:
    pass

CONFIG_DIR = Path.home() / ".ae"
CONFIG_FILE = CONFIG_DIR / "config.json"


@dataclass
class AEConfig:
    project_id: Optional[str] = None
    location: str = "us-central1"
    engine_id: Optional[str] = None
    app_name: Optional[str] = None
    user_id: str = "user_default"
    session_id: Optional[str] = None
    api_version: str = "v1beta1"
    show_thoughts: bool = True
    show_tool_calls: bool = True
    raw_mode: bool = False
    endpoint_override: Optional[str] = None
    token: Optional[str] = None

    @classmethod
    def load(cls, **cli_overrides) -> "AEConfig":
        """Load configuration with priority: CLI flags > .env > ~/.ae/config.json > defaults."""
        config_data = {}

        # 1. Load from ~/.ae/config.json
        if CONFIG_FILE.exists():
            try:
                with open(CONFIG_FILE, "r", encoding="utf-8") as f:
                    config_data = json.load(f)
            except Exception:
                pass

        # 2. Overlay environment variables
        env_project = (
            os.getenv("GOOGLE_CLOUD_PROJECT")
            or os.getenv("PROJECT_ID")
            or os.getenv("CLOUD_ML_PROJECT_ID")
        )
        if env_project:
            config_data["project_id"] = env_project

        env_location = (
            os.getenv("GOOGLE_CLOUD_LOCATION")
            or os.getenv("REGION")
            or os.getenv("LOCATION")
            or os.getenv("CLOUD_ML_REGION")
        )
        if env_location:
            config_data["location"] = env_location

        env_engine = os.getenv("AGENT_ENGINE_ID") or os.getenv("REASONING_ENGINE_ID")
        if env_engine:
            config_data["engine_id"] = env_engine

        env_app_name = os.getenv("APP_NAME") or os.getenv("AGENT_APP_NAME")
        if env_app_name:
            config_data["app_name"] = env_app_name

        env_user = os.getenv("AE_USER_ID") or os.getenv("USER") or os.getenv("USERNAME")
        if env_user:
            config_data["user_id"] = env_user

        env_session = os.getenv("AE_SESSION_ID")
        if env_session:
            config_data["session_id"] = env_session

        env_token = os.getenv("AE_ACCESS_TOKEN") or os.getenv("GOOGLE_ACCESS_TOKEN")
        if env_token:
            config_data["token"] = env_token

        # 3. Apply CLI overrides (filter out None)
        for k, v in cli_overrides.items():
            if v is not None:
                config_data[k] = v

        return cls(**{k: v for k, v in config_data.items() if k in cls.__dataclass_fields__})

    def save(self):
        """Save current configuration to ~/.ae/config.json."""
        CONFIG_DIR.mkdir(parents=True, exist_ok=True)
        data = asdict(self)
        # Avoid saving sensitive temporary bearer token to disk
        data.pop("token", None)
        with open(CONFIG_FILE, "w", encoding="utf-8") as f:
            json.dump(data, f, indent=2)

    def get_api_host(self) -> str:
        """Returns the base API endpoint for Vertex AI in this location."""
        if self.endpoint_override:
            return self.endpoint_override.rstrip("/")
        return f"https://{self.location}-aiplatform.googleapis.com"

    def get_resource_name(self) -> Optional[str]:
        """Returns full resource name if project, location, and engine_id are present."""
        if not (self.project_id and self.location and self.engine_id):
            return None
        if self.engine_id.startswith("projects/"):
            return self.engine_id
        return f"projects/{self.project_id}/locations/{self.location}/reasoningEngines/{self.engine_id}"
