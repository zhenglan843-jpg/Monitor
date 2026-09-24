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


class TestJitter(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.app = QApplication.instance() or QApplication([])

    def test_dynamic_values_no_jitter(self):
        bar = FloatingBar()
        bar.set_mode(HUDMode.HORIZONTAL)

        test_cases = [
            ("0%", "0%", "0%", "0 B/s", "0 B/s"),
            ("9%", "14%", "5%·42°C", "850 B/s", "120 B/s"),
            ("100%", "98%", "99%·82°C", "1023.5 MB/s", "12.4 MB/s"),
            ("1%", "8%", "12%·50°C", "45.2 KB/s", "1.1 KB/s"),
        ]

        widths = []
        for cpu, ram, gpu, down, up in test_cases:
            d = MetricData(
                cpu_percent=float(cpu.replace('%', '')),
                ram_percent=float(ram.replace('%', '')),
                gpu_available=True,
                gpu_percent=float(gpu.split('%')[0]),
                gpu_temp=50,
                net_recv_str=down,
                net_sent_str=up
            )
            bar.update_metrics(d)
            self.app.processEvents()
            widths.append(bar.width())

        self.assertEqual(len(set(widths)), 1, f"悬浮窗宽度发生抖动: {widths}")
        bar.close()


if __name__ == "__main__":
    unittest.main()
