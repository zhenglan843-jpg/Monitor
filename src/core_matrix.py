from PyQt6.QtWidgets import QWidget, QGridLayout, QLabel
from PyQt6.QtGui import QFont, QColor
from PyQt6.QtCore import Qt
from typing import List


class CoreMatrixWidget(QWidget):
    """
    CPU 多核心热力图矩阵微组件
    - 将 18 个逻辑核心可视化为整齐的微型热力网格
    - 颜色随核心独立负载动态从暗灰过度到科技蓝、亮橙与赤红
    """
    def __init__(self, core_count: int = 18, parent=None):
        super().__init__(parent)
        self.core_count = core_count
        self.core_labels: List[QLabel] = []
        self._init_ui()

    def _init_ui(self):
        grid = QGridLayout(self)
        grid.setContentsMargins(4, 4, 4, 4)
        grid.setSpacing(6)

        cols = 6
        font = QFont("Cascadia Code", 8)
        font.setStyleStrategy(QFont.StyleStrategy.PreferAntialias | QFont.StyleStrategy.NoSubpixelAntialias)

        for i in range(self.core_count):
            lbl = QLabel(f"#{i+1:02d}: 0%")
            lbl.setFont(font)
            lbl.setAlignment(Qt.AlignmentFlag.AlignCenter)
            lbl.setFixedHeight(22)
            lbl.setStyleSheet("""
                QLabel {
                    background-color: #1a2230;
                    color: #94a3b8;
                    border: 1px solid #2d3748;
                    border-radius: 4px;
                }
            """)
            r = i // cols
            c = i % cols
            grid.addWidget(lbl, r, c)
            self.core_labels.append(lbl)

    def update_cores(self, cores_percent: List[float]):
        if not cores_percent:
            return

        # 若核心数动态变化则扩展
        while len(self.core_labels) < len(cores_percent):
            idx = len(self.core_labels)
            lbl = QLabel(f"#{idx+1:02d}: 0%")
            lbl.setFont(self.core_labels[0].font() if self.core_labels else QFont("Cascadia Code", 8))
            lbl.setAlignment(Qt.AlignmentFlag.AlignCenter)
            lbl.setFixedHeight(22)
            self.layout().addWidget(lbl, idx // 6, idx % 6)
            self.core_labels.append(lbl)

        for i, pct in enumerate(cores_percent):
            if i >= len(self.core_labels):
                break
            lbl = self.core_labels[i]
            lbl.setText(f"#{i+1:02d}: {pct:.0f}%")

            if pct >= 85:
                # 极端高负载 (赤红)
                lbl.setStyleSheet("background-color: #7f1d1d; color: #fecaca; border: 1px solid #ef4444; border-radius: 4px;")
            elif pct >= 60:
                # 中高负载 (琥珀橙)
                lbl.setStyleSheet("background-color: #78350f; color: #fef08a; border: 1px solid #f59e0b; border-radius: 4px;")
            elif pct >= 25:
                # 中等活跃 (科技青)
                lbl.setStyleSheet("background-color: #0c4a6e; color: #bae6fd; border: 1px solid #0284c7; border-radius: 4px;")
            else:
                # 低载闲置 (低调深灰)
                lbl.setStyleSheet("background-color: #18202c; color: #64748b; border: 1px solid #242f40; border-radius: 4px;")
