"""Unit tests for configuration loading and validation."""

import unittest
from ae_cli.config import AEConfig


class TestConfig(unittest.TestCase):
    def test_default_config(self):
        cfg = AEConfig()
        self.assertEqual(cfg.location, "us-central1")
        self.assertTrue(cfg.show_thoughts)
        self.assertFalse(cfg.raw_mode)
        self.assertEqual(cfg.get_api_host(), "https://us-central1-aiplatform.googleapis.com")

    def test_overrides(self):
        cfg = AEConfig.load(
            project_id="test-proj",
            location="europe-west1",
            engine_id="12345",
            show_thoughts=False,
        )
        self.assertEqual(cfg.project_id, "test-proj")
        self.assertEqual(cfg.location, "europe-west1")
        self.assertEqual(cfg.engine_id, "12345")
        self.assertFalse(cfg.show_thoughts)
        self.assertEqual(cfg.get_api_host(), "https://europe-west1-aiplatform.googleapis.com")

    def test_resource_name_generation(self):
        cfg = AEConfig(project_id="my-proj", location="us-central1", engine_id="99999")
        expected = "projects/my-proj/locations/us-central1/reasoningEngines/99999"
        self.assertEqual(cfg.get_resource_name(), expected)

    def test_full_resource_name_preservation(self):
        full_res = "projects/custom/locations/us-central1/reasoningEngines/111"
        cfg = AEConfig(project_id="my-proj", location="us-central1", engine_id=full_res)
        self.assertEqual(cfg.get_resource_name(), full_res)


if __name__ == "__main__":
    unittest.main()
