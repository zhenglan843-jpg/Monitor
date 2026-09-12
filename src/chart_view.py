from PyQt6.QtWidgets import QWidget, QVBoxLayout, QHBoxLayout, QLabel
from PyQt6.QtGui import QPainter, QColor, QPen, QPainterPath, QLinearGradient, QFont
from PyQt6.QtCore import Qt
from typing import List, Optional


class PerformanceGraph(QWidget):
    """
    MSI Afterburner 风格实时平滑走势图表
    - 60 秒历史波形平滑渲染
    - 动态网格背景、实时 Min / Avg / Max 统计
    - 原生 QPainter 硬件加速，零延迟、极低开销
    """
    def __init__(
        self,
        title: str,
        unit: str = "%",
        line_color: str = "#38bdf8",
        max_scale: float = 100.0,
        height: int = 120,
        parent=None
    ):
        super().__init__(parent)
        self.title = title
        self.unit = unit
        self.line_color = QColor(line_color)
        self.max_scale = max_scale
        self.setFixedHeight(height)
        self.setAttribute(Qt.WidgetAttribute.WA_OpaquePaintEvent, False)

        self.data_points: List[float] = [0.0] * 60
        self.cur_val = 0.0
        self.min_val = 0.0
        self.avg_val = 0.0
        self.max_val = 0.0

    def set_data(self, points: List[float], custom_max: Optional[float] = None):
        if points:
            self.data_points = points[-60:] if len(points) >= 60 else [0.0] * (60 - len(points)) + points
            self.cur_val = self.data_points[-1]
            valid_points = [p for p in self.data_points if p > 0.0]
            if valid_points:
                self.min_val = min(valid_points)
                self.max_val = max(valid_points)
                self.avg_val = sum(valid_points) / len(valid_points)
            else:
                self.min_val = 0.0
                self.max_val = 0.0
                self.avg_val = 0.0

            if custom_max and custom_max > 0:
                self.max_scale = max(custom_max, self.max_val * 1.1)

            self.update()

    def paintEvent(self, event):
        painter = QPainter(self)
        painter.setRenderHint(QPainter.RenderHint.Antialiasing)

        w = self.width()
        h = self.height()

        # 1. 绘制暗黑背景与圆角边框
        rect = self.rect().adjusted(1, 1, -1, -1)
        painter.setBrush(QColor(15, 20, 28))
        painter.setPen(QColor(40, 48, 62))
        painter.drawRoundedRect(rect, 8, 8)

        # 2. 绘制微弱网格参考线 (25%, 50%, 75%)
        graph_top = 26
        graph_bottom = h - 10
        graph_h = max(1, graph_bottom - graph_top)
        graph_w = w - 24
        graph_left = 12

        grid_pen = QPen(QColor(255, 255, 255, 14), 1, Qt.PenStyle.DashLine)
        painter.setPen(grid_pen)
        for pct in [0.25, 0.5, 0.75]:
            gy = int(graph_bottom - graph_h * pct)
            painter.drawLine(graph_left, gy, graph_left + graph_w, gy)

        # 3. 绘制顶部信息栏 (标题、当前值、Min/Avg/Max)
        font_hdr = QFont("Segoe UI", 9, QFont.Weight.Bold)
        font_hdr.setStyleStrategy(QFont.StyleStrategy.PreferAntialias | QFont.StyleStrategy.NoSubpixelAntialias)
        painter.setFont(font_hdr)
        painter.setPen(QColor(226, 232, 240))
        painter.drawText(12, 18, self.title)
        title_w = painter.fontMetrics().horizontalAdvance(self.title)

        font_stats = QFont("Cascadia Code", 8)
        font_stats.setStyleStrategy(QFont.StyleStrategy.PreferAntialias | QFont.StyleStrategy.NoSubpixelAntialias)
        painter.setFont(font_stats)

        def _fmt_val(v: float) -> str:
            if v >= 10000:
                return f"{v:.0f}"
            elif v >= 100:
                return f"{v:.1f}"
            return f"{v:.1f}"

        clean_unit = self.unit.strip()
        stats_text = (
            f"NOW: {_fmt_val(self.cur_val)}{clean_unit}  |  "
            f"MIN: {_fmt_val(self.min_val)}  AVG: {_fmt_val(self.avg_val)}  MAX: {_fmt_val(self.max_val)}{clean_unit}"
        )
        sw = painter.fontMetrics().horizontalAdvance(stats_text)

        # 智能防重叠：若视口较窄或字符较长，自动精简 MIN 显示，确保永不挤压标题
        if w - sw - 14 < title_w + 24:
            stats_text = (
                f"NOW: {_fmt_val(self.cur_val)}{clean_unit}  |  "
                f"AVG: {_fmt_val(self.avg_val)}  MAX: {_fmt_val(self.max_val)}{clean_unit}"
            )
            sw = painter.fontMetrics().horizontalAdvance(stats_text)

        painter.setPen(self.line_color)
        painter.drawText(w - sw - 14, 18, stats_text)

        # 4. 绘制平滑动态折线与渐变发光填充
        n = len(self.data_points)
        if n < 2:
            return

        dx = graph_w / (n - 1)
        scale = max(1.0, self.max_scale)

        path = QPainterPath()
        for i, val in enumerate(self.data_points):
            clamped = max(0.0, min(scale, val))
            py = graph_bottom - (clamped / scale) * graph_h
            px = graph_left + i * dx
            if i == 0:
                path.moveTo(px, py)
            else:
                path.lineTo(px, py)

        # 区域渐变填充
        fill_path = QPainterPath(path)
        fill_path.lineTo(graph_left + graph_w, graph_bottom)
        fill_path.lineTo(graph_left, graph_bottom)
        fill_path.closeSubpath()

        grad = QLinearGradient(0, graph_top, 0, graph_bottom)
        c = self.line_color
        grad.setColorAt(0.0, QColor(c.red(), c.green(), c.blue(), 75))
        grad.setColorAt(1.0, QColor(c.red(), c.green(), c.blue(), 5))
        painter.fillPath(fill_path, grad)

        # 高光主折线
        pen_line = QPen(self.line_color, 1.8)
        painter.setPen(pen_line)
        painter.drawPath(path)
