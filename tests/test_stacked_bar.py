import unittest
from PyQt6.QtWidgets import QApplication
from PyQt6.QtGui import QPixmap, QPainter
from src.stacked_bar import StackedContextBar


class TestStackedBar(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.app = QApplication.instance() or QApplication([])

    def test_stacked_bar_data_and_render(self):
        bar = StackedContextBar()
        bar.resize(400, 20)
        bar.set_data(
            user_tokens=5000,
            model_tokens=15000,
            thinking_tokens=30000,
            tool_tokens=10000,
            base_system_tokens=22000,
            total_limit=1_048_576
        )

        self.assertEqual(bar.total_context_tokens, 82000)
        self.assertAlmostEqual(bar.context_percent, (82000 / 1_048_576) * 100.0, places=2)
        self.assertIn("82,000", bar.toolTip())

        # 触发无头渲染验证无崩溃
        pix = QPixmap(400, 20)
        bar.render(pix)
        self.assertFalse(pix.isNull())


if __name__ == "__main__":
    unittest.main()
