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
from PyQt6.QtGui import QFont, QFontMetrics


class TestFontMetrics(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.app = QApplication.instance() or QApplication([])

    def test_font_horizontal_advance(self):
        font = QFont('Cascadia Code', 9, QFont.Weight.Bold)
        fm = QFontMetrics(font)

        tests = ['11%·52°C', '100%·85°C', '18.8W', '100.0W', '1023.9 MB/s']
        for text in tests:
            w = fm.horizontalAdvance(text)
            self.assertGreater(w, 0, f"Font advance for '{text}' should be positive")


if __name__ == "__main__":
    unittest.main()
