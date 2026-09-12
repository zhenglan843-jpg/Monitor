import sys
import os
import unittest

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

from PyQt6.QtWidgets import QApplication
from src.fps_collector import calculate_percentile_lows, FpsProvider, FpsData
from src.collector import MetricData
from src.floating_bar import FloatingBar, HUDMode
from src.dashboard import DashboardWindow


class TestFpsCollector(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.app = QApplication.instance() or QApplication(sys.argv)

    def test_calculate_percentile_lows_normal(self):
        # 模拟稳定 60 FPS (约 16.6ms)，偶发 1% 掉帧到 33.3ms (30 FPS)
        frametimes = [16.6] * 99 + [33.3] * 1
        low_1p, low_01p = calculate_percentile_lows(frametimes)
        self.assertGreater(low_1p, 0.0)
        # 1000 / 33.3 ≈ 30.0
        self.assertAlmostEqual(low_1p, 30.0, delta=1.5)

    def test_calculate_percentile_lows_144fps(self):
        # 模拟 144 FPS (约 6.94ms)，长尾卡顿到 20ms (50 FPS)
        frametimes = [6.94] * 990 + [20.0] * 10
        low_1p, low_01p = calculate_percentile_lows(frametimes)
        self.assertGreater(low_1p, 45.0)
        self.assertLess(low_1p, 65.0)

    def test_calculate_percentile_lows_edge_cases(self):
        # 空或过少样本返回 0.0
        self.assertEqual(calculate_percentile_lows([]), (0.0, 0.0))
        self.assertEqual(calculate_percentile_lows([16.6, 16.7]), (0.0, 0.0))
        # 异常数据过滤
        self.assertEqual(calculate_percentile_lows([-5.0, 0.0, 2000.0]), (0.0, 0.0))

    def test_fps_provider_standby(self):
        provider = FpsProvider()
        data = provider.sample()
        self.assertIsInstance(data, FpsData)
        # 未启动 3D 游戏或 RTSS 时，应平稳待机
        if not data.available:
            self.assertEqual(data.fps, 0.0)
            self.assertEqual(data.engine_source, "Standby")

    def test_hud_fps_rendering(self):
        bar = FloatingBar()
        mock_data = MetricData(
            fps_available=True,
            fps=120.0,
            fps_1percent_low=85.0,
            fps_avg=118.0,
            frametime_ms=8.33,
            game_process_name="TestGame.exe"
        )
        bar.update_metrics(mock_data)

        # 验证垂直 HUD
        bar.set_mode(HUDMode.VERTICAL)
        self.assertEqual(bar.v_fps.lbl_val.text(), "120 FPS")
        self.assertEqual(bar.v_fps_low.lbl_val.text(), "85 FPS")

        # 验证横向胶囊栏
        bar.set_mode(HUDMode.HORIZONTAL)
        self.assertEqual(bar.h_fps.lbl_val.text(), "120·85L")

        # 验证微型徽章
        bar.set_mode(HUDMode.MINI)
        self.assertEqual(bar.m_fps.lbl_val.text(), "120")

        # 验证待机状态展示 "--"
        standby_data = MetricData(fps_available=False)
        bar.update_metrics(standby_data)
        self.assertEqual(bar.v_fps.lbl_val.text(), "--")
        self.assertEqual(bar.v_fps_low.lbl_val.text(), "--")
        self.assertEqual(bar.h_fps.lbl_val.text(), "--")
        self.assertEqual(bar.m_fps.lbl_val.text(), "--")

    def test_dashboard_fps_rendering(self):
        dash = DashboardWindow()
        mock_data = MetricData(
            fps_available=True,
            fps=144.0,
            fps_1percent_low=102.0,
            fps_avg=141.0,
            frametime_ms=6.94,
            game_process_name="Cyberpunk2077.exe",
            history_fps=[120.0, 130.0, 144.0] * 20
        )
        dash.update_metrics(mock_data)
        self.assertIn("Cyberpunk2077.exe", dash.lbl_fps_name.text())
        self.assertIn("144.0 FPS", dash.lbl_fps_stat.text())
        self.assertIn("102.0 FPS", dash.lbl_fps_stat.text())

        # 待机状态验证
        dash.update_metrics(MetricData(fps_available=False))
        self.assertIn("待机中", dash.lbl_fps_name.text())


if __name__ == "__main__":
    unittest.main()
