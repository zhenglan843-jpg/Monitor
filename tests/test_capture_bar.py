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
from src.floating_bar import FloatingBar
from src.collector import MetricData


class TestCaptureBar(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.app = QApplication.instance() or QApplication([])

    def test_grab_bar(self):
        bar = FloatingBar()
        d = MetricData(
            cpu_percent=19,
            ram_percent=28,
            gpu_available=True,
            gpu_percent=11,
            gpu_temp=52,
            gpu_power_w=18.8,
            gpu_power_limit_w=95,
            net_recv_str='532.0 KB/s',
            net_ping_ms=28.0
        )
        bar.update_metrics(d)
        self.app.processEvents()

        pix = bar.grab()
        self.assertFalse(pix.isNull())
        self.assertGreater(pix.width(), 0)
        self.assertGreater(pix.height(), 0)
        bar.close()


if __name__ == "__main__":
    unittest.main()
