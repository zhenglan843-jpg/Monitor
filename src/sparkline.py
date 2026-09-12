from PyQt6.QtWidgets import QWidget
from PyQt6.QtGui import QPainter, QColor, QPen, QPainterPath, QLinearGradient
from PyQt6.QtCore import Qt
from typing import List


class MiniSparkline(QWidget):
    """
    超轻量微型实时走势折线图
    - 用于悬浮窗或卡片内，零卡顿、纯原生 QPainter 绘制
    - 呈现类似 MSI Afterburner 的发光动态走势
    """
    def __init__(self, color_hex: str = "#38bdf8", max_val: float = 100.0, parent=None):
        super().__init__(parent)
        self.color = QColor(color_hex)
        self.max_val = max(1.0, max_val)
        self.data_points: List[float] = [0.0] * 30
        self.setFixedSize(50, 18)
        self.setAttribute(Qt.WidgetAttribute.WA_TranslucentBackground)

    def set_data(self, points: List[float]):
        if points:
            # 截取最近 30 点
            self.data_points = points[-30:] if len(points) >= 30 else [0.0] * (30 - len(points)) + points
            self.update()

    def paintEvent(self, event):
        if not self.data_points:
            return

        painter = QPainter(self)
        painter.setRenderHint(QPainter.RenderHint.Antialiasing)

        w = self.width()
        h = self.height()
        n = len(self.data_points)
        if n < 2:
            return

        dx = w / (n - 1)
        path = QPainterPath()

        # 归一化 Y 坐标
        for i, val in enumerate(self.data_points):
            clamped = max(0.0, min(self.max_val, val))
            y = h - (clamped / self.max_val) * (h - 2) - 1
            x = i * dx
            if i == 0:
                path.moveTo(x, y)
            else:
                path.lineTo(x, y)

        # 绘制底部微弱渐变填充
        fill_path = QPainterPath(path)
        fill_path.lineTo(w, h)
        fill_path.lineTo(0, h)
        fill_path.closeSubpath()

        grad = QLinearGradient(0, 0, 0, h)
        grad.setColorAt(0.0, QColor(self.color.red(), self.color.green(), self.color.blue(), 60))
        grad.setColorAt(1.0, QColor(self.color.red(), self.color.green(), self.color.blue(), 5))
        painter.fillPath(fill_path, grad)

        # 绘制高亮折线
        pen = QPen(self.color, 1.2)
        painter.setPen(pen)
        painter.drawPath(path)
