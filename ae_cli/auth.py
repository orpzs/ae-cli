"""Authentication resolver for Google Cloud / Vertex AI Agent Engine."""

import os
import shutil
import subprocess
from typing import Tuple, Optional


def get_gcloud_token() -> Optional[str]:
    """Attempts to obtain an OAuth2 access token via gcloud CLI."""
    gcloud_path = shutil.which("gcloud") or shutil.which("gcloud.cmd")
    if not gcloud_path:
        return None
    try:
        result = subprocess.run(
            [gcloud_path, "auth", "print-access-token"],
            capture_output=True,
            text=True,
            check=True,
            timeout=10,
        )
        token = result.stdout.strip()
        return token if token else None
    except Exception:
        return None


def get_gcloud_project() -> Optional[str]:
    """Attempts to read the active gcloud project."""
    gcloud_path = shutil.which("gcloud") or shutil.which("gcloud.cmd")
    if not gcloud_path:
        return None
    try:
        result = subprocess.run(
            [gcloud_path, "config", "get-value", "project"],
            capture_output=True,
            text=True,
            check=True,
            timeout=5,
        )
        proj = result.stdout.strip()
        if proj and "(unset)" not in proj:
            return proj
    except Exception:
        pass
    return None


def get_access_token(explicit_token: Optional[str] = None) -> Tuple[str, Optional[str]]:
    """Resolves an OAuth2 access token and detected project ID.

    Returns:
        Tuple[token, detected_project_id]

    Raises:
        RuntimeError: If no valid token could be acquired.
    """
    if explicit_token:
        return explicit_token, None

    detected_project = None

    # 1. Try google.auth Application Default Credentials (ADC)
    try:
        import google.auth
        from google.auth.transport.requests import Request

        creds, proj = google.auth.default(
            scopes=["https://www.googleapis.com/auth/cloud-platform"]
        )
        if proj:
            detected_project = proj

        if not creds.valid:
            creds.refresh(Request())

        if creds.token:
            return creds.token, detected_project
    except Exception:
        pass

    # 2. Try gcloud CLI auth
    gcloud_tok = get_gcloud_token()
    if gcloud_tok:
        if not detected_project:
            detected_project = get_gcloud_project()
        return gcloud_tok, detected_project

    # 3. If everything failed, raise informative error
    raise RuntimeError(
        "Could not authenticate with Google Cloud.\n"
        "Please authenticate using one of the following methods:\n"
        "  1. Run: gcloud auth application-default login\n"
        "  2. Or set environment variable: GOOGLE_APPLICATION_CREDENTIALS=/path/to/key.json\n"
        "  3. Or pass an access token via: --token <TOKEN> or AE_ACCESS_TOKEN=<TOKEN>\n"
    )
