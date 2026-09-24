import sys
import os
import unittest

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

if sys.stdout and hasattr(sys.stdout, "reconfigure"):
    try:
        sys.stdout.reconfigure(encoding="utf-8")
    except Exception:
        pass

from PyQt6.QtWidgets import QApplication
from src.collector import MetricData
from src.floating_bar import FloatingBar, HUDMode
from src.dashboard import DashboardWindow


class TestHudModes(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.app = QApplication.instance() or QApplication([])

    def setUp(self):
        self.bar = FloatingBar()
        self.mock_data = MetricData(
            cpu_name="Intel Core Ultra 5",
            cpu_percent=32.4,
            cpu_freq_mhz=2400.0,
            cpu_physical_cores=14,
            cpu_logical_cores=18,
            cpu_cores=[20.0] * 18,
            ram_percent=42.1,
            ram_used_gb=13.3,
            ram_total_gb=31.6,
            ram_committed_gb=16.5,
            ram_commit_total_gb=33.6,
            ram_commit_percent=49.1,
            gpu_available=True,
            gpu_name="NVIDIA GeForce RTX 4050",
            gpu_percent=65.0,
            gpu_clock_core_mhz=2055,
            gpu_power_w=68.4,
            gpu_power_limit_w=97.7,
            gpu_pstate="P0",
            gpu_temp=62,
            net_recv_str="2.4 MB/s",
            net_sent_str="180 KB/s",
            net_ping_ms=28.0,
            disk_read_str="12.5 MB/s",
            disk_write_str="4.8 MB/s"
        )

    def tearDown(self):
        self.bar.close()

    def test_hud_mode_transitions(self):
        # 1. 垂直模式
        self.bar.set_mode(HUDMode.VERTICAL)
        self.bar.update_metrics(self.mock_data)
        self.assertEqual(self.bar.hud_mode, HUDMode.VERTICAL)
        self.assertEqual(self.bar.width(), 185)
        self.assertEqual(self.bar.height(), 310)

        # 2. 横向模式
        self.bar.set_mode(HUDMode.HORIZONTAL)
        self.bar.update_metrics(self.mock_data)
        self.assertEqual(self.bar.hud_mode, HUDMode.HORIZONTAL)
        self.assertEqual(self.bar.width(), 1060)
        self.assertEqual(self.bar.height(), 36)

        # 3. MINI 模式
        self.bar.set_mode(HUDMode.MINI)
        self.bar.update_metrics(self.mock_data)
        self.assertEqual(self.bar.hud_mode, HUDMode.MINI)
        self.assertEqual(self.bar.width(), 600)
        self.assertEqual(self.bar.height(), 32)

    def test_hud_scale(self):
        self.bar.set_mode(HUDMode.VERTICAL)
        self.bar.set_scale(1.2)
        self.assertAlmostEqual(self.bar.scale_factor, 1.2, places=2)
        self.assertEqual(self.bar.width(), int(185 * 1.2))
        self.assertEqual(self.bar.height(), int(310 * 1.2))

        self.bar.set_scale(0.8)
        self.assertAlmostEqual(self.bar.scale_factor, 0.8, places=2)
        self.assertEqual(self.bar.width(), int(185 * 0.8))
        self.assertEqual(self.bar.height(), int(310 * 0.8))

    def test_click_through_toggle(self):
        self.bar.set_click_through(True)
        self.assertTrue(self.bar.click_through)
        self.bar.set_click_through(False)
        self.assertFalse(self.bar.click_through)

    def test_reset_to_primary_screen(self):
        self.bar.reset_to_primary_screen()
        # Should position within screen coordinates
        self.assertGreater(self.bar.x(), 0)
        self.assertGreater(self.bar.y(), 0)


if __name__ == "__main__":
    unittest.main()
