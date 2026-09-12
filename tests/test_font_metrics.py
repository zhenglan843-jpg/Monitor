import os
os.environ['QT_SCALE_FACTOR'] = '1.5'

from PyQt6.QtWidgets import QApplication, QLabel
from PyQt6.QtGui import QFont, QFontMetrics

def run():
    app = QApplication([])
    font = QFont('Cascadia Code', 9, QFont.Weight.Bold)
    fm = QFontMetrics(font)

    tests = ['11%·52°C', '100%·85°C', '18.8W', '100.0W', '1023.9 MB/s']
    for text in tests:
        print(f'At 1.5x, "{text}": width={fm.horizontalAdvance(text)}px')

if __name__ == "__main__":
    run()
