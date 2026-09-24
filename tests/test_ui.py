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
from src.collector import SystemCollector, MetricData
from src.floating_bar import FloatingBar
from src.dashboard import DashboardWindow
from src.tray import TrayManager


class TestUiSmoke(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.app = QApplication.instance() or QApplication([])

    def test_ui_components_smoke(self):
        collector = SystemCollector(interval=0.5)
        floating_bar = FloatingBar()
        dashboard = DashboardWindow()
        tray = TrayManager(self.app, floating_bar, dashboard, collector)

        mock_data = MetricData(
            cpu_percent=24.5,
            cpu_freq_mhz=2800.0,
            ram_percent=45.2,
            ram_used_gb=14.2,
            ram_total_gb=32.0,
            gpu_available=True,
            gpu_name="NVIDIA GeForce RTX 4050 Laptop GPU",
            gpu_percent=18.0,
            gpu_temp=52,
            gpu_mem_percent=22.0,
            gpu_mem_used_mb=1300,
            gpu_mem_total_mb=6144,
            net_recv_str="1.2 MB/s",
            net_sent_str="128 KB/s",
            disks=[{'mount': 'C:\\', 'used_gb': 120, 'total_gb': 500, 'percent': 24.0}],
            top_processes=[{'pid': 1234, 'name': 'test.exe', 'cpu_percent': 12.0, 'mem_mb': 150.0}]
        )

        floating_bar.update_metrics(mock_data)
        dashboard.update_metrics(mock_data)
        tray.update_tooltip(mock_data)
        self.app.processEvents()

        self.assertGreater(floating_bar.width(), 0)
        self.assertGreater(floating_bar.height(), 0)
        self.assertGreater(dashboard.width(), 0)
        self.assertGreater(dashboard.height(), 0)

        floating_bar.close()
        dashboard.close()
        collector.stop()


if __name__ == "__main__":
    unittest.main()
