from enum import Enum
from PyQt6.QtCore import Qt, QPoint, pyqtSignal
from PyQt6.QtWidgets import (
    QWidget, QHBoxLayout, QVBoxLayout, QLabel, QMenu, QStackedWidget, QApplication
)
from PyQt6.QtGui import QColor, QFont, QCursor, QPainter
from .collector import MetricData
from .antigravity_collector import AntigravityMetrics
from .sparkline import MiniSparkline


class HUDMode(Enum):
    VERTICAL = "垂直侧边 HUD (默认)"
    HORIZONTAL = "横向胶囊栏"
    MINI = "极简微型徽章"


def format_tokens_compact(tokens: int) -> str:
    """将 Token 数量格式化为紧凑高可读性字符串 (如 0, 850, 4.5k, 65.4k, 150k, 1.85M)"""
    if tokens <= 0:
        return "0"
    elif tokens < 1000:
        return str(tokens)
    elif tokens < 1_000_000:
        k = tokens / 1000.0
        if k < 100.0:
            return f"{k:.1f}k"
        else:
            return f"{k:.0f}k"
    else:
        m = tokens / 1_000_000.0
        if m < 10.0:
            return f"{m:.2f}M"
        else:
            return f"{m:.1f}M"


class MetricItem(QWidget):
    """单项指标微组件（定宽、等宽字体、右对齐，彻底消除抖动与毛边）"""
    def __init__(self, label_text: str, default_val: str = "--", val_width: int = 38, is_vertical: bool = False, parent=None):
        super().__init__(parent)
        self.val_width = val_width
        self._current_tier = 0

        pad_left = 2
        pad_right = 8
        spacing = 6
        if is_vertical:
            layout = QHBoxLayout(self)
            layout.setContentsMargins(4, 2, 4, 2)
            layout.setSpacing(6)
        else:
            layout = QHBoxLayout(self)
            layout.setContentsMargins(pad_left, 0, pad_right, 0)
            layout.setSpacing(spacing)

        # 标签
        self.lbl_title = QLabel(label_text)
        font_title = QFont("Segoe UI", 8 if is_vertical else 9, QFont.Weight.DemiBold)
        font_title.setStyleStrategy(QFont.StyleStrategy.PreferAntialias | QFont.StyleStrategy.NoSubpixelAntialias)
        self.lbl_title.setFont(font_title)
        self.lbl_title.setStyleSheet("color: #94a3b8; background: transparent;")

        # 数值标签
        self.lbl_val = QLabel(default_val)
        font_val = QFont("Cascadia Code", 9, QFont.Weight.Bold)
        font_val.setStyleHint(QFont.StyleHint.Monospace)
        font_val.setStyleStrategy(QFont.StyleStrategy.PreferAntialias | QFont.StyleStrategy.NoSubpixelAntialias)
        self.lbl_val.setFont(font_val)
        if is_vertical:
            self.lbl_val.setMinimumWidth(val_width)
        else:
            self.lbl_val.setFixedWidth(val_width)
        self.lbl_val.setAlignment(Qt.AlignmentFlag.AlignRight | Qt.AlignmentFlag.AlignVCenter)
        self.lbl_val.setStyleSheet("color: #38bdf8; background: transparent;")

        layout.addWidget(self.lbl_title)
        if is_vertical:
            layout.addStretch()
        layout.addWidget(self.lbl_val)

        if not is_vertical:
            # 精确锁定组件定宽，保证左右留白完全对称，杜绝文字粘连分割线
            self.lbl_title.adjustSize()
            tw = self.lbl_title.sizeHint().width()
            self.setFixedWidth(pad_left + tw + spacing + val_width + pad_right)

    def set_value(self, text: str, percent: float = 0.0, custom_color: str = None):
        self.lbl_val.setText(text)
        if custom_color:
            self.lbl_val.setStyleSheet(f"color: {custom_color}; background: transparent;")
            return

        tier = 2 if percent >= 85 else (1 if percent >= 70 else 0)
        if tier != self._current_tier:
            self._current_tier = tier
            if tier == 2:
                self.lbl_val.setStyleSheet("color: #ef4444; background: transparent;")
            elif tier == 1:
                self.lbl_val.setStyleSheet("color: #f59e0b; background: transparent;")
            else:
                self.lbl_val.setStyleSheet("color: #38bdf8; background: transparent;")


class FloatingBar(QWidget):
    """
    专业级性能监控悬浮 HUD (使用 QStackedWidget 保证形态切换 100% 稳定可靠)
    - 预建 3 种 HUD 视图页面，绝不动态销毁控件，彻底根除模式切换导致的参数失踪与尺寸塌陷
    - 支持鼠标穿透模式 (游戏防误触)
    - 纯原生 QPainter 抗锯齿，零抖动、零毛边
    """
    toggle_dashboard_signal = pyqtSignal()
    quit_signal = pyqtSignal()
    mode_changed_signal = pyqtSignal(HUDMode)
    click_through_signal = pyqtSignal(bool)
    position_changed_signal = pyqtSignal(int, int)
    opacity_changed_signal = pyqtSignal(float)
    pin_changed_signal = pyqtSignal(bool)
    lock_changed_signal = pyqtSignal(bool)
    scale_changed_signal = pyqtSignal(float)

    def __init__(self, parent=None):
        super().__init__(parent)
        self.hud_mode = HUDMode.VERTICAL
        self.is_dragging = False
        self.drag_position = QPoint()
        self.locked_position = False
        self.is_pinned = True
        self.click_through = False
        self.opacity_val = 0.92
        self.scale_factor = 1.0

        self._init_window()
        self._init_pages()
        self.set_mode(HUDMode.VERTICAL)

    def _init_window(self):
        flags = (
            Qt.WindowType.FramelessWindowHint |
            Qt.WindowType.WindowStaysOnTopHint |
            Qt.WindowType.Tool
        )
        if self.click_through:
            flags |= Qt.WindowType.WindowTransparentForInput

        self.setWindowFlags(flags)
        self.setAttribute(Qt.WidgetAttribute.WA_TranslucentBackground)
        self.setAutoFillBackground(False)

    def paintEvent(self, event):
        painter = QPainter(self)
        painter.setRenderHint(QPainter.RenderHint.Antialiasing)

        rect = self.rect().adjusted(1, 1, -1, -1)
        alpha = int(255 * self.opacity_val)

        # 深邃黑半透明科技感背景
        painter.setBrush(QColor(16, 20, 28, alpha))
        # 极细明亮科技描边
        painter.setPen(QColor(255, 255, 255, 38))
        radius = 12 if self.hud_mode != HUDMode.VERTICAL else 8
        painter.drawRoundedRect(rect, radius, radius)

    def _create_separator(self) -> QLabel:
        sep = QLabel("|")
        font_sep = QFont("Segoe UI", 9)
        font_sep.setStyleStrategy(QFont.StyleStrategy.PreferAntialias | QFont.StyleStrategy.NoSubpixelAntialias)
        sep.setFont(font_sep)
        sep.setStyleSheet("color: rgba(255, 255, 255, 0.22); background: transparent;")
        sep.setFixedWidth(6)
        sep.setAlignment(Qt.AlignmentFlag.AlignCenter)
        return sep

    def _init_pages(self):
        """一次性构建 3 种形态页面容器并放入 QStackedWidget，保证生命周期稳定"""
        master_layout = QVBoxLayout(self)
        master_layout.setContentsMargins(0, 0, 0, 0)
        master_layout.setSpacing(0)

        self.stack = QStackedWidget(self)
        self.stack.setStyleSheet("background: transparent;")
        master_layout.addWidget(self.stack)

        # -------------------------------------------------------------
        # 页面 0: 经典横向流线型胶囊栏 (HORIZONTAL)
        # -------------------------------------------------------------
        self.page_h = QWidget()
        self.page_h.setStyleSheet("background: transparent;")
        layout_h = QHBoxLayout(self.page_h)
        layout_h.setContentsMargins(12, 4, 12, 4)
        layout_h.setSpacing(10)

        self.h_cpu = MetricItem("CPU", "0%", val_width=38)
        layout_h.addWidget(self.h_cpu)

        self.h_spark_cpu = MiniSparkline("#38bdf8", max_val=100.0)
        layout_h.addWidget(self.h_spark_cpu)

        layout_h.addWidget(self._create_separator())

        self.h_ram = MetricItem("RAM", "0%", val_width=38)
        layout_h.addWidget(self.h_ram)

        self.h_sep_gpu = self._create_separator()
        layout_h.addWidget(self.h_sep_gpu)

        self.h_gpu = MetricItem("GPU", "0%", val_width=82)
        layout_h.addWidget(self.h_gpu)

        self.h_sep_pwr = self._create_separator()
        layout_h.addWidget(self.h_sep_pwr)

        self.h_pwr = MetricItem("PWR", "0W", val_width=50)
        layout_h.addWidget(self.h_pwr)

        layout_h.addWidget(self._create_separator())

        self.h_net = MetricItem("⬇", "0 B/s", val_width=80)
        layout_h.addWidget(self.h_net)

        self.h_sep_ping = self._create_separator()
        layout_h.addWidget(self.h_sep_ping)

        self.h_ping = MetricItem("PING", "--", val_width=42)
        layout_h.addWidget(self.h_ping)

        self.h_sep_ai = self._create_separator()
        layout_h.addWidget(self.h_sep_ai)

        self.h_ai = MetricItem("AI", "--", val_width=52)
        layout_h.addWidget(self.h_ai)

        self.h_sep_quo = self._create_separator()
        layout_h.addWidget(self.h_sep_quo)

        self.h_quo = MetricItem("QUOTA", "--/--", val_width=76)
        layout_h.addWidget(self.h_quo)

        self.stack.addWidget(self.page_h)

        # -------------------------------------------------------------
        # 页面 1: 垂直侧边 HUD (VERTICAL)
        # -------------------------------------------------------------
        self.page_v = QWidget()
        self.page_v.setStyleSheet("background: transparent;")
        layout_v = QVBoxLayout(self.page_v)
        layout_v.setContentsMargins(10, 8, 10, 8)
        layout_v.setSpacing(4)

        hdr = QLabel("HUD")
        hdr.setStyleSheet("color: #22c55e; font-weight: 800; font-size: 10px; letter-spacing: 1px;")
        layout_v.addWidget(hdr)

        self.v_gpu = MetricItem("GPU 负载", "0%", val_width=60, is_vertical=True)
        layout_v.addWidget(self.v_gpu)

        self.v_pwr = MetricItem("GPU 功耗", "0 W", val_width=60, is_vertical=True)
        layout_v.addWidget(self.v_pwr)

        self.v_clk = MetricItem("GPU 频率", "0 MHz", val_width=60, is_vertical=True)
        layout_v.addWidget(self.v_clk)

        self.v_cpu = MetricItem("CPU 负载", "0%", val_width=60, is_vertical=True)
        layout_v.addWidget(self.v_cpu)

        self.v_ram = MetricItem("RAM 已用", "0 GB", val_width=60, is_vertical=True)
        layout_v.addWidget(self.v_ram)

        self.v_net = MetricItem("下行网速", "0 B/s", val_width=60, is_vertical=True)
        layout_v.addWidget(self.v_net)

        self.v_ping = MetricItem("网络延迟", "-- ms", val_width=60, is_vertical=True)
        layout_v.addWidget(self.v_ping)

        self.v_ai = MetricItem("AI 上下文", "--", val_width=60, is_vertical=True)
        layout_v.addWidget(self.v_ai)

        self.v_quo_5h = MetricItem("5h 额度", "--", val_width=60, is_vertical=True)
        layout_v.addWidget(self.v_quo_5h)

        self.v_quo_wk = MetricItem("周度额度", "--", val_width=60, is_vertical=True)
        layout_v.addWidget(self.v_quo_wk)

        self.stack.addWidget(self.page_v)

        # -------------------------------------------------------------
        # 页面 2: 极简微型徽章 (MINI) - 清晰呈现 CPU、GPU(含温度)、RAM、AI、QUOTA
        # -------------------------------------------------------------
        self.page_m = QWidget()
        self.page_m.setStyleSheet("background: transparent;")
        layout_m = QHBoxLayout(self.page_m)
        layout_m.setContentsMargins(10, 2, 10, 2)
        layout_m.setSpacing(8)

        self.m_cpu = MetricItem("CPU", "0%", val_width=38)
        layout_m.addWidget(self.m_cpu)

        layout_m.addWidget(self._create_separator())

        self.m_gpu = MetricItem("GPU", "0%", val_width=82)
        layout_m.addWidget(self.m_gpu)

        layout_m.addWidget(self._create_separator())

        self.m_ram = MetricItem("RAM", "0%", val_width=38)
        layout_m.addWidget(self.m_ram)

        layout_m.addWidget(self._create_separator())

        self.m_ai = MetricItem("AI", "--", val_width=44)
        layout_m.addWidget(self.m_ai)

        self.m_sep_quo = self._create_separator()
        layout_m.addWidget(self.m_sep_quo)

        self.m_quo = MetricItem("QUO", "--/--", val_width=72)
        layout_m.addWidget(self.m_quo)

        self.stack.addWidget(self.page_m)

    def set_mode(self, mode: HUDMode):
        self.hud_mode = mode
        sf = getattr(self, "scale_factor", 1.0)
        if mode == HUDMode.HORIZONTAL:
            self.stack.setCurrentIndex(0)
            self.setFixedSize(int(1060 * sf), int(36 * sf))
        elif mode == HUDMode.VERTICAL:
            self.stack.setCurrentIndex(1)
            self.setFixedSize(int(185 * sf), int(310 * sf))
        else:  # MINI
            self.stack.setCurrentIndex(2)
            self.setFixedSize(int(600 * sf), int(32 * sf))

        # 确保形态切换后窗口始终完整位于当前屏幕可见区域内 (多屏幕感知)
        center = self.pos() + QPoint(self.width() // 2, self.height() // 2)
        screen = QApplication.screenAt(center) or self.screen() or QApplication.primaryScreen()
        if screen:
            geom = screen.availableGeometry()
            new_x = min(self.x(), geom.right() - self.width() - 5)
            new_y = min(self.y(), geom.bottom() - self.height() - 5)
            self.move(max(geom.left() + 5, new_x), max(geom.top() + 5, new_y))

        self.update()
        self.mode_changed_signal.emit(mode)

    def set_scale(self, factor: float):
        """调整 HUD 缩放比例 (0.8 ~ 1.4)"""
        self.scale_factor = max(0.7, min(1.6, factor))
        self.set_mode(self.hud_mode)
        self.scale_changed_signal.emit(self.scale_factor)

    def reset_to_primary_screen(self):
        """一键复位至主屏右上角安全停靠位置"""
        primary = QApplication.primaryScreen()
        if primary:
            geom = primary.availableGeometry()
            x = geom.right() - self.width() - 25
            y = geom.top() + 35
            self.move(x, y)
            self.position_changed_signal.emit(x, y)

    def set_click_through(self, enabled: bool):
        self.click_through = enabled
        self._init_window()
        self.show()
        self.click_through_signal.emit(enabled)

    def update_metrics(self, data: MetricData):
        """统一刷新所有形态下的监控控件"""
        # ==================== 1. 刷新 HORIZONTAL 页面 ====================
        self.h_cpu.set_value(f"{data.cpu_percent:.0f}%", data.cpu_percent)
        self.h_spark_cpu.set_data(data.history_cpu)
        self.h_ram.set_value(f"{data.ram_percent:.0f}%", data.ram_percent)

        if data.gpu_available:
            self.h_gpu.setVisible(True)
            self.h_sep_gpu.setVisible(True)
            gpu_str = f"{data.gpu_percent:.0f}%"
            if data.gpu_temp > 0:
                gpu_str += f"·{data.gpu_temp}°C"
            self.h_gpu.set_value(gpu_str, data.gpu_percent)

            if data.gpu_power_w > 0:
                self.h_pwr.setVisible(True)
                self.h_sep_pwr.setVisible(True)
                pwr_pct = (data.gpu_power_w / max(1.0, data.gpu_power_limit_w)) * 100.0
                self.h_pwr.set_value(f"{data.gpu_power_w:.1f}W", pwr_pct)
            else:
                self.h_pwr.setVisible(False)
                self.h_sep_pwr.setVisible(False)
        else:
            self.h_gpu.setVisible(False)
            self.h_pwr.setVisible(False)
            self.h_sep_gpu.setVisible(False)
            self.h_sep_pwr.setVisible(False)

        self.h_net.set_value(data.net_recv_str, 0)
        if data.net_ping_ms >= 0:
            p_color = "#22c55e" if data.net_ping_ms < 45 else ("#f59e0b" if data.net_ping_ms < 90 else "#ef4444")
            ping_text = "<1ms" if data.net_ping_ms < 1.0 else f"{data.net_ping_ms:.0f}ms"
            self.h_ping.set_value(ping_text, 0, p_color)
        else:
            self.h_ping.set_value("--", 0, "#64748b")

        # ==================== 2. 刷新 VERTICAL 页面 ====================
        self.v_cpu.set_value(f"{data.cpu_percent:.0f}%", data.cpu_percent)
        self.v_ram.set_value(f"{data.ram_used_gb:.1f}G", data.ram_percent)

        if data.gpu_available:
            self.v_gpu.set_value(f"{data.gpu_percent:.0f}%", data.gpu_percent)
            self.v_pwr.set_value(f"{data.gpu_power_w:.1f} W", 0, "#10b981")
            self.v_clk.set_value(f"{data.gpu_clock_core_mhz} MHz", 0, "#34d399")
        else:
            self.v_gpu.set_value("--", 0)
            self.v_pwr.set_value("--", 0)
            self.v_clk.set_value("--", 0)

        self.v_net.set_value(data.net_recv_str, 0)
        if data.net_ping_ms >= 0:
            p_color = "#22c55e" if data.net_ping_ms < 45 else ("#f59e0b" if data.net_ping_ms < 90 else "#ef4444")
            ping_text = "<1 ms" if data.net_ping_ms < 1.0 else f"{data.net_ping_ms:.0f} ms"
            self.v_ping.set_value(ping_text, 0, p_color)
        else:
            self.v_ping.set_value("--", 0, "#64748b")

        # ==================== 3. 刷新 MINI 页面 ====================
        self.m_cpu.set_value(f"{data.cpu_percent:.0f}%", data.cpu_percent)
        self.m_ram.set_value(f"{data.ram_percent:.0f}%", data.ram_percent)

        if data.gpu_available:
            m_gpu_str = f"{data.gpu_percent:.0f}%"
            if data.gpu_temp > 0:
                m_gpu_str += f"·{data.gpu_temp}°C"
            self.m_gpu.set_value(m_gpu_str, data.gpu_percent)
        else:
            self.m_gpu.set_value("--", 0)
        self.update()

    def update_antigravity_metrics(self, data: AntigravityMetrics):
        """刷新 HUD 上的 Antigravity AI 状态与上下文指标"""
        if not data.is_running:
            ai_text = "OFF"
            color = "#64748b"
            tooltip = "Antigravity 未运行"
        elif data.context_tokens <= 0:
            ai_text = "IDLE"
            color = "#22c55e"
            tooltip = f"Antigravity 状态: {data.agent_status}\n暂无活跃对话"
        else:
            if data.context_tokens >= 1000:
                ai_text = f"{data.context_tokens / 1000:.1f}k"
            else:
                ai_text = str(data.context_tokens)

            pct = data.context_percent
            if pct >= 80.0:
                color = "#ef4444"
            elif pct >= 50.0:
                color = "#f59e0b"
            else:
                color = "#38bdf8"

            tooltip = (
                f"🤖 Antigravity AI 状态: {data.agent_status}\n"
                f"💬 活跃会话: {data.active_title}\n"
                f"📊 上下文用量: {data.context_tokens:,} / {data.context_limit:,} ({data.context_percent:.1f}%)\n"
                f"⚡ 单轮增量: +{data.last_turn_total:,} (In: {data.last_turn_input} | Out: {data.last_turn_output})"
            )

        quota_str = ""
        if data.is_running and data.gemini_5h_percent >= 0:
            quota_lines = ["\n🌟 官方实时配额:"]
            if data.user_tier_name:
                quota_lines.append(f"  • 订阅级别: {data.user_tier_name}")
            rst_5h = f" ({data.gemini_5h_reset_str})" if data.gemini_5h_reset_str else ""
            quota_lines.append(f"  • Gemini 5h 限额: {data.gemini_5h_percent:.1f}% 剩余{rst_5h}")
            rst_wk = f" ({data.gemini_weekly_reset_str})" if data.gemini_weekly_reset_str else ""
            quota_lines.append(f"  • Gemini 周度限额: {data.gemini_weekly_percent:.1f}% 剩余{rst_wk}")
            if data.third_party_5h_percent >= 0:
                quota_lines.append(f"  • 第三方模型: 5h {data.third_party_5h_percent:.0f}% | 周 {data.third_party_weekly_percent:.0f}%")
            quota_str = "\n".join(quota_lines)
            tooltip += quota_str

        # 配额数据显示与色彩
        if not data.is_running or data.gemini_5h_percent < 0:
            quo_text = "--/--"
            v_5h_text = "--"
            v_wk_text = "--"
            quo_color = "#64748b"
            v_5h_color = "#64748b"
            v_wk_color = "#64748b"
            quo_tip = "官方配额: 未获取或离线"
        else:
            quo_text = f"{data.gemini_5h_percent:.0f}%/{data.gemini_weekly_percent:.0f}%"
            v_5h_text = f"{data.gemini_5h_percent:.0f}%"
            v_wk_text = f"{data.gemini_weekly_percent:.0f}%"

            # 5h 额度颜色
            if data.gemini_5h_percent <= 20.0:
                v_5h_color = "#ef4444"
                quo_color = "#ef4444"
            elif data.gemini_5h_percent <= 50.0:
                v_5h_color = "#f59e0b"
                quo_color = "#f59e0b"
            else:
                v_5h_color = "#10b981"
                quo_color = "#10b981"

            # 周度额度颜色
            if data.gemini_weekly_percent <= 20.0:
                v_wk_color = "#ef4444"
            elif data.gemini_weekly_percent <= 50.0:
                v_wk_color = "#f59e0b"
            else:
                v_wk_color = "#38bdf8"

            rst_5h = f" ({data.gemini_5h_reset_str})" if data.gemini_5h_reset_str else ""
            rst_wk = f" ({data.gemini_weekly_reset_str})" if data.gemini_weekly_reset_str else ""
            quo_tip = (
                f"🌟 Antigravity 官方云端实时配额\n"
                f"━━━━━━━━━━━━━━━━━━━━━━\n"
                f"⏳ 5小时滑动限额: {data.gemini_5h_percent:.1f}% 剩余{rst_5h}\n"
                f"📅 周度总体限额: {data.gemini_weekly_percent:.1f}% 剩余{rst_wk}\n"
                f"💎 会员订阅等级: {data.user_tier_name or '默认'}\n"
                f"💡 格式说明: [5小时剩余%] / [周度剩余%]"
            )

        # 刷新 HORIZONTAL
        self.h_ai.set_value(ai_text, 0, color)
        self.h_ai.setToolTip(tooltip)
        self.h_quo.set_value(quo_text, 0, quo_color)
        self.h_quo.setToolTip(quo_tip)

        # 刷新 VERTICAL
        if not data.is_running:
            v_text = "OFF"
        elif data.context_tokens <= 0:
            v_text = "IDLE"
        else:
            v_text = f"{data.context_percent:.1f}% ({ai_text})"
        self.v_ai.set_value(v_text, 0, color)
        self.v_ai.setToolTip(tooltip)
        self.v_quo_5h.set_value(v_5h_text, 0, v_5h_color)
        self.v_quo_5h.setToolTip(quo_tip)
        self.v_quo_wk.set_value(v_wk_text, 0, v_wk_color)
        self.v_quo_wk.setToolTip(quo_tip)

        # 刷新 MINI
        self.m_ai.set_value(ai_text, 0, color)
        self.m_ai.setToolTip(tooltip)
        self.m_quo.set_value(quo_text, 0, quo_color)
        self.m_quo.setToolTip(quo_tip)

        self.update()

    # 鼠标拖动与吸附
    def mousePressEvent(self, event):
        if event.button() == Qt.MouseButton.LeftButton and not self.locked_position and not self.click_through:
            self.is_dragging = True
            self.drag_position = event.globalPosition().toPoint() - self.frameGeometry().topLeft()
            event.accept()

    def mouseMoveEvent(self, event):
        if self.is_dragging and event.buttons() == Qt.MouseButton.LeftButton:
            new_pos = event.globalPosition().toPoint() - self.drag_position
            center = new_pos + QPoint(self.width() // 2, self.height() // 2)
            screen = QApplication.screenAt(center) or self.screen() or QApplication.primaryScreen()
            if screen:
                geom = screen.availableGeometry()
                snap_dist = 15
                if abs(new_pos.x() - geom.left()) < snap_dist:
                    new_pos.setX(geom.left() + 6)
                elif abs(new_pos.x() + self.width() - geom.right()) < snap_dist:
                    new_pos.setX(geom.right() - self.width() - 6)

                if abs(new_pos.y() - geom.top()) < snap_dist:
                    new_pos.setY(geom.top() + 6)
                elif abs(new_pos.y() + self.height() - geom.bottom()) < snap_dist:
                    new_pos.setY(geom.bottom() - self.height() - 6)

            self.move(new_pos)
            event.accept()

    def mouseReleaseEvent(self, event):
        if self.is_dragging:
            self.is_dragging = False
            self.position_changed_signal.emit(self.x(), self.y())
        else:
            self.is_dragging = False

    def mouseDoubleClickEvent(self, event):
        if event.button() == Qt.MouseButton.LeftButton and not self.click_through:
            self.toggle_dashboard_signal.emit()

    # 右键菜单
    def contextMenuEvent(self, event):
        if self.click_through:
            return

        menu = QMenu(self)
        menu.setStyleSheet("""
            QMenu {
                background-color: #1e293b;
                color: #e2e8f0;
                border: 1px solid #334155;
                border-radius: 8px;
                padding: 4px;
                font-size: 12px;
            }
            QMenu::item {
                padding: 6px 20px;
                border-radius: 4px;
            }
            QMenu::item:selected {
                background-color: #3b82f6;
                color: #ffffff;
            }
            QMenu::separator {
                height: 1px;
                background-color: #334155;
                margin: 4px 6px;
            }
        """)

        action_dashboard = menu.addAction("📊 详细仪表盘 (Ctrl+Shift+D)")
        action_dashboard.triggered.connect(self.toggle_dashboard_signal.emit)

        menu.addSeparator()

        # HUD 形态切换子菜单
        mode_menu = menu.addMenu("📐 HUD 布局形态")
        for m in [HUDMode.VERTICAL, HUDMode.HORIZONTAL, HUDMode.MINI]:
            act = mode_menu.addAction(m.value)
            act.setCheckable(True)
            act.setChecked(self.hud_mode == m)
            act.triggered.connect(lambda checked, mode=m: self.set_mode(mode))

        # HUD 缩放比例
        scale_menu = menu.addMenu("🔍 HUD 缩放比例")
        for sc, sc_lbl in [(0.8, "80% (紧凑)"), (1.0, "100% (默认)"), (1.2, "120% (放大)"), (1.4, "140% (超大)")]:
            act = scale_menu.addAction(sc_lbl)
            act.setCheckable(True)
            act.setChecked(abs(self.scale_factor - sc) < 0.05)
            act.triggered.connect(lambda checked, s=sc: self.set_scale(s))

        # 鼠标穿透开关 (适合游戏无干扰)
        act_click_thru = menu.addAction("🖱️ 鼠标穿透模式 (Ctrl+Shift+P)")
        act_click_thru.setCheckable(True)
        act_click_thru.setChecked(self.click_through)
        act_click_thru.triggered.connect(lambda checked: self.set_click_through(checked))

        # 置顶切换
        action_pin = menu.addAction("📌 窗口置顶")
        action_pin.setCheckable(True)
        action_pin.setChecked(self.is_pinned)
        action_pin.triggered.connect(self._toggle_pin)

        # 锁定位置
        action_lock = menu.addAction("🔒 锁定位置")
        action_lock.setCheckable(True)
        action_lock.setChecked(self.locked_position)
        action_lock.triggered.connect(self._toggle_lock)

        # 重置位置
        act_reset = menu.addAction("📍 重置位置至主屏右上角")
        act_reset.triggered.connect(self.reset_to_primary_screen)

        # 透明度
        opacity_menu = menu.addMenu("🌓 透明度")
        for val, label in [(1.0, "100%"), (0.92, "92% (默认)"), (0.75, "75%"), (0.6, "60%"), (0.45, "45%")]:
            act = opacity_menu.addAction(label)
            act.setCheckable(True)
            act.setChecked(abs(self.opacity_val - val) < 0.05)
            act.triggered.connect(lambda checked, v=val: self._set_opacity(v))

        menu.addSeparator()

        action_quit = menu.addAction("❌ 退出程序")
        action_quit.triggered.connect(self.quit_signal.emit)

        menu.exec(QCursor.pos())

    def _toggle_pin(self, checked: bool):
        self.is_pinned = checked
        if checked:
            self.setWindowFlags(self.windowFlags() | Qt.WindowType.WindowStaysOnTopHint)
        else:
            self.setWindowFlags(self.windowFlags() & ~Qt.WindowType.WindowStaysOnTopHint)
        self.show()
        self.pin_changed_signal.emit(checked)

    def _toggle_lock(self, checked: bool):
        self.locked_position = checked
        self.lock_changed_signal.emit(checked)

    def _set_opacity(self, val: float):
        self.opacity_val = val
        self.opacity_changed_signal.emit(val)
        self.update()
