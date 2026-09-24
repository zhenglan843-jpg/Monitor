import sys
import os
import time
import unittest

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

if sys.stdout and hasattr(sys.stdout, "reconfigure"):
    try:
        sys.stdout.reconfigure(encoding="utf-8")
    except Exception:
        pass

from PyQt6.QtWidgets import QApplication
from src.collector import SystemCollector, MetricData


class TestCollector(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.app = QApplication.instance() or QApplication([])

    def test_collector_lifecycle_and_metrics(self):
        collector = SystemCollector(interval=0.1)
        received = []
        collector.metrics_updated.connect(lambda d: received.append(d))
        collector.start()

        # 轻量模式采样
        t_end = time.time() + 0.35
        while time.time() < t_end:
            self.app.processEvents()
            time.sleep(0.02)

        # 详细模式采样
        collector.set_detailed_mode(True)
        t_end = time.time() + 0.35
        while time.time() < t_end:
            self.app.processEvents()
            time.sleep(0.02)

        collector.stop()
        self.app.processEvents()

        self.assertGreaterEqual(len(received), 2, "采样帧数不足")
        latest = received[-1]
        self.assertIsInstance(latest.cpu_name, str)
        self.assertGreaterEqual(latest.cpu_percent, 0.0)
        self.assertGreaterEqual(latest.ram_percent, 0.0)
        self.assertIsInstance(latest.net_recv_str, str)
        self.assertIsInstance(latest.net_sent_str, str)
        self.assertIsInstance(latest.history_cpu, list)
        self.assertGreater(len(latest.history_cpu), 0)

    def test_collector_init_and_stop(self):
        collector = SystemCollector(interval=0.5)
        self.assertIsNotNone(collector)
        self.assertIsInstance(collector._cpu_name, str)
        collector.stop()


if __name__ == "__main__":
    unittest.main()
