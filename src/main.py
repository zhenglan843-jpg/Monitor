import sys
import os
from PyQt6.QtWidgets import QApplication
from PyQt6.QtCore import Qt

from .collector import SystemCollector
from .antigravity_collector import AntigravityCollector
from .floating_bar import FloatingBar, HUDMode
from .dashboard import DashboardWindow
from .tray import TrayManager
from .config import ConfigManager, AppConfig
from .hotkey import GlobalHotkeyManager


def main():
    # 启用高 DPI 缩放优化
    if hasattr(Qt.ApplicationAttribute, 'AA_EnableHighDpiScaling'):
        QApplication.setAttribute(Qt.ApplicationAttribute.AA_EnableHighDpiScaling, True)
    if hasattr(Qt.ApplicationAttribute, 'AA_UseHighDpiPixmaps'):
        QApplication.setAttribute(Qt.ApplicationAttribute.AA_UseHighDpiPixmaps, True)

    app = QApplication(sys.argv)
    app.setQuitOnLastWindowClosed(False)
    app.setApplicationName("Monitor")

    # 0. 读取本地持久化配置
    cfg = ConfigManager.load()

    # 1. 初始化深度硬件采集与 Antigravity AI 采集核心线程
    collector = SystemCollector(interval=cfg.sample_interval)
    agy_collector = AntigravityCollector(interval=cfg.sample_interval)

    # 2. 初始化专业级悬浮 HUD
    floating_bar = FloatingBar()

    # 3. 初始化详细中枢仪表盘 (Pro Hub 2.0)
    dashboard = DashboardWindow()

    # 4. 初始化系统托盘管理
    tray = TrayManager(app, floating_bar, dashboard, collector)

    # 5. 恢复用户历史状态与配置
    mode_map = {
        "HORIZONTAL": HUDMode.HORIZONTAL,
        "VERTICAL": HUDMode.VERTICAL,
        "MINI": HUDMode.MINI
    }
    initial_mode = mode_map.get(cfg.hud_mode, HUDMode.VERTICAL)
    floating_bar.set_mode(initial_mode)
    floating_bar._set_opacity(cfg.opacity)
    floating_bar._toggle_pin(cfg.is_pinned)
    floating_bar.locked_position = cfg.locked_position
    floating_bar.set_click_through(cfg.click_through)

    # 同步状态至仪表盘控件
    hud_idx = 1 if cfg.hud_mode == "HORIZONTAL" else (2 if cfg.hud_mode == "MINI" else 0)
    dashboard.combo_hud.setCurrentIndex(hud_idx)
    int_idx = 0 if abs(cfg.sample_interval - 0.5) < 0.1 else (2 if abs(cfg.sample_interval - 2.0) < 0.1 else 1)
    dashboard.combo_interval.setCurrentIndex(int_idx)
    dashboard.set_auto_start_ui(cfg.auto_start)
    tray.set_auto_start_checked(cfg.auto_start)
    if cfg.click_through:
        dashboard.btn_toggle_click_thru.setChecked(True)
        dashboard.btn_toggle_click_thru.setText("已开启鼠标穿透 (点击穿透至背景)")
        dashboard.btn_toggle_click_thru.setStyleSheet("background-color: #059669;")

    # 6. 绑定配置持久化保存联动
    def save_state():
        cfg.hud_mode = floating_bar.hud_mode.name
        cfg.pos_x = floating_bar.x()
        cfg.pos_y = floating_bar.y()
        cfg.opacity = floating_bar.opacity_val
        cfg.is_pinned = floating_bar.is_pinned
        cfg.locked_position = floating_bar.locked_position
        cfg.click_through = floating_bar.click_through
        cfg.sample_interval = collector.interval
        ConfigManager.save(cfg)

    floating_bar.position_changed_signal.connect(lambda x, y: save_state())
    floating_bar.mode_changed_signal.connect(lambda m: save_state())
    floating_bar.opacity_changed_signal.connect(lambda o: save_state())
    floating_bar.pin_changed_signal.connect(lambda p: save_state())
    floating_bar.lock_changed_signal.connect(lambda l: save_state())
    floating_bar.click_through_signal.connect(lambda c: save_state())
    dashboard.interval_changed_signal.connect(lambda i: save_state())

    def on_toggle_autostart(enabled: bool):
        ConfigManager.set_auto_start(enabled)
        cfg.auto_start = enabled
        dashboard.set_auto_start_ui(enabled)
        tray.set_auto_start_checked(enabled)
        save_state()

    dashboard.auto_start_signal.connect(on_toggle_autostart)
    tray.auto_start_callback = on_toggle_autostart

    # 7. 初始化 Win32 原生全局快捷键管理器
    hotkey_mgr = GlobalHotkeyManager(app)
    if cfg.hotkeys_enabled:
        hotkey_mgr.register_hotkeys(
            key_click_through=cfg.hotkey_click_through,
            key_toggle_hud=cfg.hotkey_toggle_hud,
            key_toggle_dash=cfg.hotkey_toggle_dashboard
        )

    # 8. 绑定数据流与槽函数
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
            dashboard.update_antigravity_metrics(agy_collector.sample_once(force_refresh_totals=True))

    floating_bar.toggle_dashboard_signal.connect(toggle_dashboard)
    floating_bar.quit_signal.connect(app.quit)

    # 全局快捷键响应
    def on_hotkey_click_through():
        new_state = not floating_bar.click_through
        floating_bar.set_click_through(new_state)
        tray.act_click_through.setChecked(new_state)
        dashboard.btn_toggle_click_thru.setChecked(new_state)
        if new_state:
            dashboard.btn_toggle_click_thru.setText("已开启鼠标穿透 (点击穿透至背景)")
            dashboard.btn_toggle_click_thru.setStyleSheet("background-color: #059669;")
        else:
            dashboard.btn_toggle_click_thru.setText("开启鼠标穿透 (游戏免干扰)")
            dashboard.btn_toggle_click_thru.setStyleSheet("background-color: #2563eb;")
        save_state()

    def on_hotkey_toggle_hud():
        if floating_bar.isVisible():
            floating_bar.hide()
        else:
            floating_bar.show()

    hotkey_mgr.hotkey_click_through.connect(on_hotkey_click_through)
    hotkey_mgr.hotkey_toggle_hud.connect(on_hotkey_toggle_hud)
    hotkey_mgr.hotkey_toggle_dashboard.connect(toggle_dashboard)

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
        if mode_str in mode_map:
            floating_bar.set_mode(mode_map[mode_str])

    dashboard.hud_mode_signal.connect(on_dashboard_hud_mode)

    # 鼠标穿透跨组件状态同步
    def on_click_thru_changed(enabled):
        floating_bar.set_click_through(enabled)
        tray.act_click_through.setChecked(enabled)
        save_state()

    dashboard.click_through_signal.connect(on_click_thru_changed)
    floating_bar.click_through_signal.connect(lambda en: tray.act_click_through.setChecked(en))

    # 应用退出时优雅终止采集线程与清理热键
    def on_app_quit():
        save_state()
        collector.stop()
        agy_collector.stop()
        hotkey_mgr.cleanup()

    app.aboutToQuit.connect(on_app_quit)

    # 9. 恢复或计算窗口位置
    primary_screen = app.primaryScreen()
    if primary_screen:
        geom = primary_screen.availableGeometry()
        bar_width = floating_bar.width() or 185
        bar_height = floating_bar.height() or 310
        if cfg.pos_x is not None and cfg.pos_y is not None:
            # 校验坐标确保在屏幕可见区域内
            valid_x = max(geom.left() + 5, min(cfg.pos_x, geom.right() - bar_width - 5))
            valid_y = max(geom.top() + 5, min(cfg.pos_y, geom.bottom() - bar_height - 5))
            floating_bar.move(valid_x, valid_y)
        else:
            initial_x = geom.right() - bar_width - 25
            initial_y = geom.top() + 35
            floating_bar.move(initial_x, initial_y)

    floating_bar.show()
    collector.start()
    agy_collector.start()

    sys.exit(app.exec())


if __name__ == "__main__":
    main()
