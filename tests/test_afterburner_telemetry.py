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


class TestAfterburnerTelemetry(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.app = QApplication.instance() or QApplication([])

    def test_afterburner_telemetry_fields(self):
        collector = SystemCollector(interval=0.1)
        collector.set_detailed_mode(True)
        results = []

        collector.metrics_updated.connect(lambda d: results.append(d))
        collector.start()

        end_t = time.time() + 0.4
        while time.time() < end_t:
            self.app.processEvents()
            time.sleep(0.02)

        collector.stop()
        self.app.processEvents()

        self.assertGreater(len(results), 0, "未采集到数据帧")
        d = results[-1]

        # 验证 Afterburner 关键遥测指标字段完整性
        self.assertIsInstance(d.cpu_name, str)
        self.assertGreater(d.cpu_logical_cores, 0)
        self.assertGreaterEqual(d.cpu_percent, 0.0)
        self.assertGreaterEqual(d.ram_used_gb, 0.0)
        self.assertGreaterEqual(d.ram_total_gb, 0.0)
        self.assertGreaterEqual(d.ram_commit_percent, 0.0)
        self.assertIsInstance(d.gpu_name, str)
        self.assertIsInstance(d.history_cpu, list)
        self.assertIsInstance(d.history_gpu, list)
        self.assertIsInstance(d.history_power, list)
        self.assertEqual(len(d.history_cpu), 60)


if __name__ == "__main__":
    unittest.main()
