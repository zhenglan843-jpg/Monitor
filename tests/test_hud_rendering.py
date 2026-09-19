import sys
import os
import unittest

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

from PyQt6.QtWidgets import QApplication
from src.collector import MetricData
from src.floating_bar import FloatingBar, HUDMode
from src.dashboard import DashboardWindow


class TestHudRendering(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.app = QApplication.instance() or QApplication(sys.argv)

    def test_hud_modes_and_sizes(self):
        bar = FloatingBar()
        
        # 验证垂直模式及尺寸
        bar.set_mode(HUDMode.VERTICAL)
        self.assertEqual(bar.size().width(), 185)
        self.assertEqual(bar.size().height(), 310)

        # 验证横向胶囊模式及尺寸
        bar.set_mode(HUDMode.HORIZONTAL)
        self.assertEqual(bar.size().width(), 1060)
        self.assertEqual(bar.size().height(), 36)

        # 验证极简徽章模式及尺寸
        bar.set_mode(HUDMode.MINI)
        self.assertEqual(bar.size().width(), 600)
        self.assertEqual(bar.size().height(), 32)

    def test_hud_metrics_rendering(self):
        bar = FloatingBar()
        mock_data = MetricData(
            cpu_percent=42.0,
            ram_percent=65.0,
            ram_used_gb=10.4,
            gpu_available=True,
            gpu_name="NVIDIA GeForce RTX 4050",
            gpu_percent=78.0,
            gpu_power_w=65.0,
            gpu_power_limit_w=95.0,
            gpu_clock_core_mhz=2250,
            gpu_temp=58,
            net_recv_str="3.5 MB/s",
            net_sent_str="450 KB/s",
            net_ping_ms=18.0
        )
        bar.update_metrics(mock_data)

        # 垂直模式验证
        bar.set_mode(HUDMode.VERTICAL)
        self.assertEqual(bar.v_cpu.lbl_val.text(), "42%")
        self.assertEqual(bar.v_ram.lbl_val.text(), "10.4G")
        self.assertEqual(bar.v_gpu.lbl_val.text(), "78%")
        self.assertEqual(bar.v_pwr.lbl_val.text(), "65.0 W")
        self.assertEqual(bar.v_clk.lbl_val.text(), "2250 MHz")
        self.assertEqual(bar.v_net.lbl_val.text(), "3.5 MB/s")
        self.assertEqual(bar.v_ping.lbl_val.text(), "18 ms")

        # 横向胶囊模式验证
        bar.set_mode(HUDMode.HORIZONTAL)
        self.assertEqual(bar.h_cpu.lbl_val.text(), "42%")
        self.assertEqual(bar.h_ram.lbl_val.text(), "65%")
        self.assertEqual(bar.h_gpu.lbl_val.text(), "78%·58°C")
        self.assertEqual(bar.h_pwr.lbl_val.text(), "65.0W")
        self.assertEqual(bar.h_net.lbl_val.text(), "3.5 MB/s")
        self.assertEqual(bar.h_ping.lbl_val.text(), "18ms")

        # 极简徽章模式验证
        bar.set_mode(HUDMode.MINI)
        self.assertEqual(bar.m_cpu.lbl_val.text(), "42%")
        self.assertEqual(bar.m_ram.lbl_val.text(), "65%")
        self.assertEqual(bar.m_gpu.lbl_val.text(), "78%·58°C")

    def test_hud_without_gpu(self):
        bar = FloatingBar()
        mock_no_gpu = MetricData(
            cpu_percent=15.0,
            ram_percent=30.0,
            gpu_available=False
        )
        bar.update_metrics(mock_no_gpu)

        bar.set_mode(HUDMode.VERTICAL)
        self.assertEqual(bar.v_gpu.lbl_val.text(), "--")
        self.assertEqual(bar.v_pwr.lbl_val.text(), "--")

        bar.set_mode(HUDMode.HORIZONTAL)
        self.assertFalse(bar.h_gpu.isVisible())
        self.assertFalse(bar.h_pwr.isVisible())

        bar.set_mode(HUDMode.MINI)
        self.assertEqual(bar.m_gpu.lbl_val.text(), "--")

    def test_dashboard_rendering(self):
        dash = DashboardWindow()
        mock_data = MetricData(
            cpu_name="Intel Core Ultra 5 125H",
            cpu_percent=35.0,
            cpu_freq_mhz=3200.0,
            cpu_physical_cores=14,
            cpu_logical_cores=18,
            cpu_cores=[30.0] * 18,
            gpu_available=True,
            gpu_name="NVIDIA GeForce RTX 4050 Laptop GPU",
            gpu_percent=60.0,
            gpu_power_w=55.0,
            gpu_power_limit_w=95.0,
            gpu_clock_core_mhz=2100,
            gpu_clock_mem_mhz=8000,
            gpu_temp=55,
            history_cpu=[30.0] * 60,
            history_gpu=[50.0] * 60,
            history_power=[45.0] * 60,
            history_net_down=[200.0] * 60,
            net_recv_str="2.1 MB/s",
            net_sent_str="120 KB/s",
            net_ping_ms=25.0
        )
        dash.update_metrics(mock_data)

        self.assertIn("Intel Core Ultra 5 125H", dash.lbl_cpu_model.text())
        self.assertIn("35.0%", dash.lbl_cpu_stat.text())
        self.assertIn("RTX 4050", dash.lbl_gpu_name.text())
        self.assertIn("55°C", dash.lbl_gpu_name.text())


if __name__ == "__main__":
    unittest.main()
