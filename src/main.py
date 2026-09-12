import sys
import os
from PyQt6.QtWidgets import QApplication
from PyQt6.QtCore import Qt

from .collector import SystemCollector
from .antigravity_collector import AntigravityCollector
from .floating_bar import FloatingBar, HUDMode
from .dashboard import DashboardWindow
from .tray import TrayManager


def main():
    # 启用高 DPI 缩放优化
    if hasattr(Qt.ApplicationAttribute, 'AA_EnableHighDpiScaling'):
        QApplication.setAttribute(Qt.ApplicationAttribute.AA_EnableHighDpiScaling, True)
    if hasattr(Qt.ApplicationAttribute, 'AA_UseHighDpiPixmaps'):
        QApplication.setAttribute(Qt.ApplicationAttribute.AA_UseHighDpiPixmaps, True)

    app = QApplication(sys.argv)
    app.setQuitOnLastWindowClosed(False)
    app.setApplicationName("Monitor")

    # 1. 初始化深度硬件采集与 Antigravity AI 采集核心线程
    collector = SystemCollector(interval=1.0)
    agy_collector = AntigravityCollector(interval=1.0)

    # 2. 初始化专业级悬浮 HUD
    floating_bar = FloatingBar()

    # 3. 初始化详细中枢仪表盘 (Pro Hub 2.0)
    dashboard = DashboardWindow()

    # 4. 初始化系统托盘管理
    tray = TrayManager(app, floating_bar, dashboard, collector)

    # 5. 绑定数据流与槽函数
    def on_metrics_updated(data):
        floating_bar.update_metrics(data)
        tray.update_tooltip(data=data)
        if dashboard.isVisible():
            dashboard.update_metrics(data)

    collector.metrics_updated.connect(on_metrics_updated)

    def on_antigravity_updated(agy_data):
        floating_bar.update_antigravity_metrics(agy_data)
        tray.update_tooltip(agy_data=agy_data)
        if dashboard.isVisible():
            dashboard.update_antigravity_metrics(agy_data)

    agy_collector.metrics_updated.connect(on_antigravity_updated)

    # 悬浮窗与仪表盘联动控制
    def toggle_dashboard():
        if dashboard.isVisible():
            dashboard.hide()
            collector.set_detailed_mode(False)
        else:
            dashboard.show()
            dashboard.raise_()
            dashboard.activateWindow()
            collector.set_detailed_mode(True)
            # 打开仪表盘时立即刷新一次 AI 状态
            dashboard.update_antigravity_metrics(agy_collector.sample_once())

    floating_bar.toggle_dashboard_signal.connect(toggle_dashboard)
    floating_bar.quit_signal.connect(app.quit)

    # 仪表盘控制信号
    def on_select_conversation(cid):
        agy_collector.select_conversation(cid)
        m = agy_collector.sample_once()
        floating_bar.update_antigravity_metrics(m)
        dashboard.update_antigravity_metrics(m)

    dashboard.select_conversation_signal.connect(on_select_conversation)
    dashboard.closed_signal.connect(lambda: collector.set_detailed_mode(False))
    dashboard.interval_changed_signal.connect(collector.set_interval)

    # HUD 形态跨组件联动
    def on_dashboard_hud_mode(mode_str):
        mode_map = {
            "HORIZONTAL": HUDMode.HORIZONTAL,
            "VERTICAL": HUDMode.VERTICAL,
            "MINI": HUDMode.MINI
        }
        if mode_str in mode_map:
            floating_bar.set_mode(mode_map[mode_str])

    dashboard.hud_mode_signal.connect(on_dashboard_hud_mode)

    # 鼠标穿透跨组件状态同步
    def on_click_thru_changed(enabled):
        floating_bar.set_click_through(enabled)
        tray.act_click_through.setChecked(enabled)

    dashboard.click_through_signal.connect(on_click_thru_changed)
    floating_bar.click_through_signal.connect(lambda en: tray.act_click_through.setChecked(en))

    # 应用退出时优雅终止采集线程
    app.aboutToQuit.connect(collector.stop)
    app.aboutToQuit.connect(agy_collector.stop)

    # 6. 计算屏幕初始显示位置（默认置于屏幕右上角，避开主视线）
    primary_screen = app.primaryScreen()
    if primary_screen:
        geom = primary_screen.availableGeometry()
        bar_width = floating_bar.width() or 185
        initial_x = geom.right() - bar_width - 25
        initial_y = geom.top() + 35
        floating_bar.move(initial_x, initial_y)

    floating_bar.show()
    collector.start()
    agy_collector.start()

    sys.exit(app.exec())


if __name__ == "__main__":
    main()
