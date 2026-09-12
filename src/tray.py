from PyQt6.QtWidgets import QSystemTrayIcon, QMenu
from PyQt6.QtGui import QIcon, QPixmap, QPainter, QColor
from PyQt6.QtCore import Qt
from .collector import MetricData
from .antigravity_collector import AntigravityMetrics
from .floating_bar import HUDMode
import os


def create_tray_icon() -> QIcon:
    """动态绘制高质感青蓝心跳脉冲托盘图标"""
    pixmap = QPixmap(64, 64)
    pixmap.fill(Qt.GlobalColor.transparent)

    painter = QPainter(pixmap)
    painter.setRenderHint(QPainter.RenderHint.Antialiasing)

    # 深色背景圆角方块
    painter.setBrush(QColor(15, 23, 42))
    painter.setPen(QColor(56, 189, 248))
    painter.drawRoundedRect(4, 4, 56, 56, 14, 14)

    # 绘制高亮科技心跳曲线
    painter.setPen(QColor(56, 189, 248))
    points = [
        (10, 36), (20, 36), (26, 18), (34, 46), (42, 26), (48, 36), (54, 36)
    ]
    for i in range(len(points) - 1):
        painter.drawLine(points[i][0], points[i][1], points[i + 1][0], points[i + 1][1])

    painter.end()
    return QIcon(pixmap)


class TrayManager:
    """系统托盘管理器 (集成 HUD 快速切换与免干扰模式)"""
    def __init__(self, app, floating_bar, dashboard, collector):
        self.app = app
        self.floating_bar = floating_bar
        self.dashboard = dashboard
        self.collector = collector

        self._last_data = None
        self._last_agy = None

        self.tray = QSystemTrayIcon(create_tray_icon(), self.app)
        self.tray.setToolTip("Monitor 专业性能与AI监控运行中")

        self._create_menu()
        self.tray.activated.connect(self._on_tray_activated)
        self.tray.show()

    def _create_menu(self):
        menu = QMenu()
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

        act_float = menu.addAction("📌 显示/隐藏 悬浮 HUD")
        act_float.triggered.connect(self._toggle_floating_bar)

        act_dash = menu.addAction("📊 详细仪表盘 (Pro Hub)")
        act_dash.triggered.connect(self._show_dashboard)

        menu.addSeparator()

        # HUD 形态切换菜单
        hud_sub = menu.addMenu("📐 HUD 布局形态")
        act_v = hud_sub.addAction("垂直侧边 HUD (默认)")
        act_v.triggered.connect(lambda: self.floating_bar.set_mode(HUDMode.VERTICAL))
        act_h = hud_sub.addAction("横向胶囊栏")
        act_h.triggered.connect(lambda: self.floating_bar.set_mode(HUDMode.HORIZONTAL))
        act_m = hud_sub.addAction("极简微型徽章")
        act_m.triggered.connect(lambda: self.floating_bar.set_mode(HUDMode.MINI))

        # 鼠标穿透开关 (游戏玩家专属免干扰模式)
        self.act_click_through = menu.addAction("🖱️ 鼠标穿透模式 (游戏防误触)")
        self.act_click_through.setCheckable(True)
        self.act_click_through.setChecked(self.floating_bar.click_through)
        self.act_click_through.triggered.connect(self._toggle_click_through)

        menu.addSeparator()

        act_opt = menu.addAction("🧹 整理内存")
        act_opt.triggered.connect(self._optimize_memory)

        act_open_agy = menu.addAction("🤖 打开 Antigravity 脑区")
        act_open_agy.triggered.connect(self._open_agy_dir)

        menu.addSeparator()

        act_quit = menu.addAction("❌ 退出程序")
        act_quit.triggered.connect(self.app.quit)

        self.tray.setContextMenu(menu)

    def _toggle_click_through(self, checked: bool):
        self.floating_bar.set_click_through(checked)

    def _on_tray_activated(self, reason):
        if reason == QSystemTrayIcon.ActivationReason.Trigger:
            self._toggle_floating_bar()
        elif reason == QSystemTrayIcon.ActivationReason.DoubleClick:
            self._show_dashboard()

    def _toggle_floating_bar(self):
        if self.floating_bar.isVisible():
            self.floating_bar.hide()
        else:
            self.floating_bar.show()

    def _show_dashboard(self):
        self.dashboard.show()
        self.dashboard.raise_()
        self.dashboard.activateWindow()
        self.collector.set_detailed_mode(True)

    def _optimize_memory(self):
        import ctypes
        try:
            ctypes.windll.psapi.EmptyWorkingSet(ctypes.windll.kernel32.GetCurrentProcess())
        except Exception:
            pass

    def _open_agy_dir(self):
        b_dir = os.path.expanduser(r"~/.gemini/antigravity/brain")
        if os.path.exists(b_dir):
            os.startfile(b_dir)

    def update_tooltip(self, data: MetricData = None, agy_data: AntigravityMetrics = None):
        if data is not None:
            self._last_data = data
        if agy_data is not None:
            self._last_agy = agy_data

        tip_lines = []
        if self._last_data:
            d = self._last_data
            tip_lines.append(f"{d.cpu_name[:24]}")
            line1 = f"CPU: {d.cpu_percent:.0f}% | RAM: {d.ram_percent:.0f}%"
            if d.gpu_available:
                line1 += f" | GPU: {d.gpu_percent:.0f}% ({d.gpu_temp}°C {d.gpu_power_w:.0f}W)"
            tip_lines.append(line1)
            ping_str = "<1ms" if d.net_ping_ms < 1.0 else f"{d.net_ping_ms:.0f}ms"
            tip_lines.append(f"⬇ {d.net_recv_str} | ⬆ {d.net_sent_str}" + (f" | Ping: {ping_str}" if d.net_ping_ms >= 0 else ""))

        if self._last_agy and self._last_agy.is_running:
            a = self._last_agy
            tip_lines.append(f"🤖 Antigravity: {a.agent_status} ({a.context_tokens:,} tok / {a.context_percent:.1f}%)")

        self.tray.setToolTip("\n".join(tip_lines) if tip_lines else "Monitor 专业性能与AI监控运行中")
