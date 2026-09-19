from PyQt6.QtWidgets import QWidget
from PyQt6.QtGui import QPainter, QColor, QPen, QFont, QPainterPath, QLinearGradient
from PyQt6.QtCore import Qt, QRectF


class StackedContextBar(QWidget):
    """
    Antigravity AI 彩色分段堆叠式上下文水位图微组件
    - 将 1,048,576 Token 窗口按来源精准细分为彩色色块：
      1. 灰蓝 #64748b: 系统基底提示词 (System Base)
      2. 天青 #38bdf8: 用户输入 (User Input)
      3. 翡翠 #10b981: 模型回答 (Model Output)
      4. 紫罗兰 #c084fc: 深度思考推理 (Thinking)
      5. 琥珀橙 #f59e0b: 工具执行与返回 (Tool Results)
    - 纯原生 QPainter 抗锯齿绘制，自带圆角与暗黑半透明背景
    """
    def __init__(self, parent=None):
        super().__init__(parent)
        self.total_limit = 1_048_576
        self.user_tokens = 0
        self.model_tokens = 0
        self.thinking_tokens = 0
        self.tool_tokens = 0
        self.base_system_tokens = 0
        self.total_context_tokens = 0
        self.context_percent = 0.0

        self.setFixedHeight(20)
        self.setAttribute(Qt.WidgetAttribute.WA_OpaquePaintEvent, False)

    def value(self) -> int:
        return int(self.context_percent)

    def set_data(
        self,
        user_tokens: int,
        model_tokens: int,
        thinking_tokens: int,
        tool_tokens: int,
        base_system_tokens: int = 22_000,
        total_limit: int = 1_048_576
    ):
        self.user_tokens = max(0, user_tokens)
        self.model_tokens = max(0, model_tokens)
        self.thinking_tokens = max(0, thinking_tokens)
        self.tool_tokens = max(0, tool_tokens)
        self.base_system_tokens = max(0, base_system_tokens)
        self.total_limit = max(1, total_limit)

        self.total_context_tokens = (
            self.base_system_tokens +
            self.user_tokens +
            self.model_tokens +
            self.thinking_tokens +
            self.tool_tokens
        )
        self.context_percent = (self.total_context_tokens / self.total_limit) * 100.0

        # 构建高信息量 Tooltip
        rem = max(0, self.total_limit - self.total_context_tokens)
        pct = self.context_percent
        self.setToolTip(
            f"📊 Antigravity 上下文容量深度剖析\n"
            f"━━━━━━━━━━━━━━━━━━━━━━━━━━━━\n"
            f"总水位: {self.total_context_tokens:,} / {self.total_limit:,} Tokens ({pct:.1f}%)\n"
            f"----------------------------\n"
            f"👤 用户输入: {self.user_tokens:,} ({(self.user_tokens / max(1, self.total_context_tokens))*100:.1f}%)\n"
            f"🤖 模型输出: {self.model_tokens:,} ({(self.model_tokens / max(1, self.total_context_tokens))*100:.1f}%)\n"
            f"💭 深度思考: {self.thinking_tokens:,} ({(self.thinking_tokens / max(1, self.total_context_tokens))*100:.1f}%)\n"
            f"⚙️ 工具返回: {self.tool_tokens:,} ({(self.tool_tokens / max(1, self.total_context_tokens))*100:.1f}%)\n"
            f"🛡️ 系统基底: {self.base_system_tokens:,} ({(self.base_system_tokens / max(1, self.total_context_tokens))*100:.1f}%)\n"
            f"📦 剩余额度: {rem:,} ({100.0 - min(100.0, pct):.1f}%)"
        )
        self.update()

    def paintEvent(self, event):
        painter = QPainter(self)
        painter.setRenderHint(QPainter.RenderHint.Antialiasing)

        w = self.width()
        h = self.height()
        r = 6.0

        rect = QRectF(1.0, 1.0, w - 2.0, h - 2.0)

        # 1. 绘制背景暗槽
        painter.setBrush(QColor(19, 26, 38))
        border_color = QColor(239, 68, 68) if self.context_percent >= 80 else (
            QColor(245, 158, 11) if self.context_percent >= 50 else QColor(45, 59, 78)
        )
        painter.setPen(QPen(border_color, 1))
        painter.drawRoundedRect(rect, r, r)

        # 2. 建立圆角剪裁路径，保证分段在两端完美贴合圆角
        clip_path = QPainterPath()
        clip_path.addRoundedRect(rect, r, r)
        painter.setClipPath(clip_path)

        # 3. 逐段绘制堆叠色块
        # 顺序: 系统基底 -> 用户 -> AI -> 思考 -> 工具
        segments = [
            (self.base_system_tokens, QColor("#64748b")),   # 灰蓝
            (self.user_tokens, QColor("#38bdf8")),          # 天青蓝
            (self.model_tokens, QColor("#10b981")),         # 翡翠绿
            (self.thinking_tokens, QColor("#c084fc")),      # 紫罗兰
            (self.tool_tokens, QColor("#f59e0b")),          # 琥珀橙
        ]

        cur_x = 1.0
        avail_w = w - 2.0
        for tok, color in segments:
            if tok <= 0:
                continue
            seg_w = (tok / self.total_limit) * avail_w
            # 最小保证 1px 可见度
            seg_w = max(1.5, seg_w)
            if cur_x + seg_w > w - 1.0:
                seg_w = max(0.0, (w - 1.0) - cur_x)

            painter.fillRect(QRectF(cur_x, 1.0, seg_w, h - 2.0), color)
            cur_x += seg_w
            if cur_x >= w - 1.0:
                break

        # 解除剪裁
        painter.setClipping(False)

        # 4. 绘制居中文本与细微文本阴影
        if self.total_context_tokens > 0:
            if self.total_context_tokens >= 1000:
                k_val = f"{self.total_context_tokens / 1000.0:.1f}k"
            else:
                k_val = str(self.total_context_tokens)

            pct_text = f"{k_val} / {self.total_limit:,} ({self.context_percent:.1f}%)"
            font = QFont("Cascadia Code", 8, QFont.Weight.Bold)
            font.setStyleStrategy(QFont.StyleStrategy.PreferAntialias | QFont.StyleStrategy.NoSubpixelAntialias)
            painter.setFont(font)

            # 黑色投影增强可读性
            painter.setPen(QColor(0, 0, 0, 200))
            painter.drawText(QRectF(2.0, 2.0, w, h), Qt.AlignmentFlag.AlignCenter, pct_text)
            # 白色前景
            painter.setPen(QColor(255, 255, 255, 240))
            painter.drawText(QRectF(1.0, 1.0, w, h), Qt.AlignmentFlag.AlignCenter, pct_text)
