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
from src.floating_bar import FloatingBar, HUDMode
from src.collector import MetricData


class TestModeSwitchFix(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.app = QApplication.instance() or QApplication([])

    def test_mode_switch_values_preserved(self):
        bar = FloatingBar()
        mock_data = MetricData(
            cpu_percent=15.0,
            ram_percent=32.0,
            gpu_available=True,
            gpu_name="NVIDIA GeForce RTX 4050",
            gpu_percent=24.0,
            gpu_temp=53,
            gpu_power_w=35.0,
            gpu_power_limit_w=95.0,
            gpu_clock_core_mhz=2100,
            net_recv_str="1.5 MB/s",
            net_sent_str="120 KB/s",
            net_ping_ms=25.0
        )

        # 1. 垂直模式
        bar.set_mode(HUDMode.VERTICAL)
        bar.update_metrics(mock_data)
        self.app.processEvents()
        self.assertEqual(bar.size().width(), 185)
        self.assertEqual(bar.size().height(), 310)
        self.assertEqual(bar.v_cpu.lbl_val.text(), "15%")
        self.assertEqual(bar.v_gpu.lbl_val.text(), "24%")

        # 2. 切换至 MINI 模式
        bar.set_mode(HUDMode.MINI)
        bar.update_metrics(mock_data)
        self.app.processEvents()
        self.assertGreaterEqual(bar.size().width(), 200)
        self.assertEqual(bar.m_cpu.lbl_val.text(), "15%")
        self.assertEqual(bar.m_ram.lbl_val.text(), "32%")
        self.assertIn("24%", bar.m_gpu.lbl_val.text())

        # 3. 切换至横向模式
        bar.set_mode(HUDMode.HORIZONTAL)
        bar.update_metrics(mock_data)
        self.app.processEvents()
        self.assertGreater(bar.size().width(), 500)
        self.assertEqual(bar.h_cpu.lbl_val.text(), "15%")
        self.assertEqual(bar.h_ram.lbl_val.text(), "32%")
        self.assertIn("24%", bar.h_gpu.lbl_val.text())

        # 4. 切回垂直模式
        bar.set_mode(HUDMode.VERTICAL)
        bar.update_metrics(mock_data)
        self.app.processEvents()
        self.assertEqual(bar.size().width(), 185)
        self.assertEqual(bar.size().height(), 310)
        self.assertEqual(bar.v_gpu.lbl_val.text(), "24%")
        self.assertEqual(bar.v_cpu.lbl_val.text(), "15%")

        bar.close()


if __name__ == "__main__":
    unittest.main()
