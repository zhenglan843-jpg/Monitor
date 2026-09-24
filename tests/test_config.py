import unittest
import os
import tempfile
from unittest.mock import patch

from src.config import AppConfig, ConfigManager


class TestConfig(unittest.TestCase):
    def test_default_config(self):
        cfg = AppConfig()
        self.assertEqual(cfg.hud_mode, "VERTICAL")
        self.assertAlmostEqual(cfg.opacity, 0.92)
        self.assertTrue(cfg.is_pinned)
        self.assertFalse(cfg.click_through)
        self.assertEqual(cfg.sample_interval, 1.0)
        self.assertAlmostEqual(cfg.hud_scale, 1.0)
        self.assertFalse(cfg.auto_game_mode)
        self.assertEqual(cfg.hotkey_click_through, "Ctrl+Shift+P")

    def test_save_and_load(self):
        with tempfile.TemporaryDirectory() as tmpdir:
            test_file = os.path.join(tmpdir, "test_config.json")
            with patch("src.config.CONFIG_FILE", test_file), patch("src.config.CONFIG_DIR", tmpdir):
                cfg = AppConfig(
                    hud_mode="HORIZONTAL",
                    pos_x=120,
                    pos_y=240,
                    opacity=0.75,
                    is_pinned=False,
                    click_through=True,
                    sample_interval=0.5,
                    hud_scale=1.2,
                    auto_game_mode=True
                )
                ConfigManager.save(cfg)
                self.assertTrue(os.path.exists(test_file))

                loaded = ConfigManager.load()
                self.assertEqual(loaded.hud_mode, "HORIZONTAL")
                self.assertEqual(loaded.pos_x, 120)
                self.assertEqual(loaded.pos_y, 240)
                self.assertAlmostEqual(loaded.opacity, 0.75)
                self.assertFalse(loaded.is_pinned)
                self.assertTrue(loaded.click_through)
                self.assertAlmostEqual(loaded.sample_interval, 0.5)
                self.assertAlmostEqual(loaded.hud_scale, 1.2)
                self.assertTrue(loaded.auto_game_mode)

    def test_corrupt_config_fallback(self):
        with tempfile.TemporaryDirectory() as tmpdir:
            test_file = os.path.join(tmpdir, "corrupt_config.json")
            with open(test_file, "w") as f:
                f.write("{invalid json...")
            with patch("src.config.CONFIG_FILE", test_file):
                loaded = ConfigManager.load()
                self.assertEqual(loaded.hud_mode, "VERTICAL")
                self.assertAlmostEqual(loaded.opacity, 0.92)


if __name__ == "__main__":
    unittest.main()
