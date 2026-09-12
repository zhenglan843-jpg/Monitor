import sys
import os
import unittest
from PyQt6.QtWidgets import QApplication

# 确保能正确导入 src 模块
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

from src.antigravity_collector import AntigravityCollector, AntigravityMetrics, estimate_tokens, get_model_rate_per_million
from src.floating_bar import FloatingBar, HUDMode
from src.dashboard import DashboardWindow
from src.tray import TrayManager
from src.collector import SystemCollector, MetricData


class TestAntigravityIntegration(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.app = QApplication.instance() or QApplication(sys.argv)

    def test_estimate_tokens(self):
        # 英文
        en_text = "Hello world, this is a test for token estimation."
        tok_en = estimate_tokens(en_text)
        self.assertGreater(tok_en, 5)
        self.assertLess(tok_en, 25)

        # 中文
        zh_text = "这是一段中文测试句子，用于验证模型分词估算器。"
        tok_zh = estimate_tokens(zh_text)
        self.assertGreater(tok_zh, 20)
        self.assertLess(tok_zh, 40)

        # 空文本
        self.assertEqual(estimate_tokens(""), 0)

    def test_antigravity_collector_sample(self):
        collector = AntigravityCollector()
        metrics = collector.sample_once()
        self.assertIsInstance(metrics, AntigravityMetrics)
        self.assertIsInstance(metrics.is_running, bool)
        self.assertIsInstance(metrics.context_tokens, int)
        self.assertIsInstance(metrics.today_tokens, int)
        self.assertIsInstance(metrics.total_tokens, int)
        self.assertIsInstance(metrics.today_cost_usd, float)
        self.assertIsInstance(metrics.total_cost_usd, float)
        self.assertIsInstance(metrics.model_breakdown, dict)
        self.assertIsInstance(metrics.recent_conversations, list)

    def test_model_pricing_rates(self):
        self.assertEqual(get_model_rate_per_million("Gemini 3.8 Flash (High)"), 1.35)
        self.assertEqual(get_model_rate_per_million("Gemini 3.7 Flash"), 1.20)
        self.assertEqual(get_model_rate_per_million("Gemini 3.1 Pro (High)"), 4.50)
        self.assertEqual(get_model_rate_per_million("Claude 3.5 Sonnet"), 6.00)
        self.assertEqual(get_model_rate_per_million("GPT-4o"), 5.00)

    def test_floating_bar_ai_update(self):
        bar = FloatingBar()
        metrics = AntigravityMetrics(
            is_running=True,
            active_conversation_id="test-12345",
            active_title="测试对话会话",
            context_tokens=65400,
            context_limit=1048576,
            context_percent=6.2,
            last_turn_input=120,
            last_turn_output=350,
            last_turn_total=470,
            today_tokens=150000,
            total_tokens=1850000,
            agent_status="待机就绪"
        )
        bar.update_antigravity_metrics(metrics)

        # 检查水平模式
        bar.set_mode(HUDMode.HORIZONTAL)
        self.assertEqual(bar.h_ai.lbl_val.text(), "65.4k")
        self.assertEqual(bar.h_tok.lbl_val.text(), "150k/1.85M")

        # 检查垂直模式
        bar.set_mode(HUDMode.VERTICAL)
        self.assertEqual(bar.v_ai.lbl_val.text(), "6.2% (65.4k)")
        self.assertEqual(bar.v_tok_today.lbl_val.text(), "150k")
        self.assertEqual(bar.v_tok_total.lbl_val.text(), "1.85M")

        # 检查微型模式
        bar.set_mode(HUDMode.MINI)
        self.assertEqual(bar.m_ai.lbl_val.text(), "65.4k")
        self.assertEqual(bar.m_tok.lbl_val.text(), "150k/1.85M")

    def test_dashboard_ai_tab_update(self):
        dash = DashboardWindow()
        metrics = AntigravityMetrics(
            is_running=True,
            active_conversation_id="f21a740c-5ba7-4c57-9990-c1d92e825967",
            active_title="开发Antigravity用量监控软件",
            step_count=135,
            context_tokens=78900,
            context_limit=1048576,
            context_percent=7.5,
            user_tokens=500,
            model_tokens=3000,
            thinking_tokens=2500,
            tool_tokens=50900,
            base_system_tokens=22000,
            last_turn_input=60,
            last_turn_output=140,
            last_turn_total=200,
            today_tokens=680000,
            total_tokens=1800000,
            total_conversations=88,
            agent_status="待机就绪",
            status_color="#22c55e",
            recent_conversations=[
                {"title": "开发Antigravity用量监控软件", "tokens": 78900, "mtime": "09-11 21:15"}
            ]
        )
        dash.update_antigravity_metrics(metrics)

        self.assertEqual(dash.agy_title_lbl.text(), "开发Antigravity用量监控软件")
        self.assertIn("78,900", dash.agy_ctx_lbl.text())
        self.assertEqual(dash.bar_agy_ctx.value(), 7)
        self.assertIn("200", dash.agy_turn_lbl.text())
        self.assertIn("680,000", dash.agy_today_lbl.text())
        self.assertEqual(dash.table_agy_recent.rowCount(), 1)

    def test_tray_tooltip_with_ai(self):
        bar = FloatingBar()
        dash = DashboardWindow()
        sys_collector = SystemCollector()
        tray = TrayManager(self.app, bar, dash, sys_collector)

        m_data = MetricData(cpu_name="Intel Core Ultra 5", cpu_percent=25.0, ram_percent=45.0)
        a_data = AntigravityMetrics(
            is_running=True,
            agent_status="待机就绪",
            context_tokens=85000,
            context_percent=8.1
        )
        tray.update_tooltip(data=m_data, agy_data=a_data)
        tooltip = tray.tray.toolTip()
        self.assertIn("Intel Core Ultra 5", tooltip)
        self.assertIn("Antigravity: 待机就绪", tooltip)
        self.assertIn("85,000 tok", tooltip)


if __name__ == "__main__":
    unittest.main()
