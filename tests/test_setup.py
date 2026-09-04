"""Unit tests for the setup wizard."""

import unittest
import tempfile
from pathlib import Path
from unittest.mock import patch
from ae_cli.setup import has_adc_credentials, save_env_file


class TestSetup(unittest.TestCase):
    def test_has_adc_credentials_custom_env(self):
        with tempfile.NamedTemporaryFile() as tmp:
            with patch.dict("os.environ", {"GOOGLE_APPLICATION_CREDENTIALS": tmp.name}):
                self.assertTrue(has_adc_credentials())

    def test_save_env_file(self):
        with tempfile.TemporaryDirectory() as tmp_dir:
            orig_cwd = Path.cwd()
            try:
                import os
                os.chdir(tmp_dir)
                save_env_file(
                    project_id="test-project",
                    location="us-central1",
                    engine_id="123456",
                    app_name="Test Agent",
                )
                env_file = Path(tmp_dir) / ".env"
                self.assertTrue(env_file.exists())
                content = env_file.read_text(encoding="utf-8")
                self.assertIn("GOOGLE_CLOUD_PROJECT=test-project", content)
                self.assertIn("GOOGLE_CLOUD_LOCATION=us-central1", content)
                self.assertIn("AGENT_ENGINE_ID=123456", content)
                self.assertIn("APP_NAME=Test Agent", content)
            finally:
                os.chdir(orig_cwd)


if __name__ == "__main__":
    unittest.main()
