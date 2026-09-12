import sys
import os
import time

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

from PyQt6.QtWidgets import QApplication
from PyQt6.QtCore import QTimer

from src.collector import SystemCollector, MetricData
from src.floating_bar import FloatingBar, HUDMode
from src.dashboard import DashboardWindow

def capture_ui():
    out_dir = os.path.join(os.path.dirname(__file__), "screenshots")
    os.makedirs(out_dir, exist_ok=True)
    app = QApplication(sys.argv)

    # 真实数据采集 1 秒
    collector = SystemCollector(interval=0.5)
    collector.set_detailed_mode(True)
    collected_data = []
    collector.metrics_updated.connect(lambda d: collected_data.append(d))
    collector.start()

    end_time = time.time() + 1.5
    while time.time() < end_time:
        app.processEvents()
        time.sleep(0.05)

    collector.stop()
    app.processEvents()

    data = collected_data[-1] if collected_data else MetricData()
    print("采集到的实时硬件指标:", f"CPU={data.cpu_percent}%, GPU={data.gpu_percent}%, PWR={data.gpu_power_w}W, PING={data.net_ping_ms}ms")

    # 1. 截取 横向胶囊栏
    bar = FloatingBar()
    bar.set_mode(HUDMode.HORIZONTAL)
    bar.show()
    bar.update_metrics(data)
    app.processEvents()
    time.sleep(0.1)
    pix_h = bar.grab()
    path_h = os.path.join(out_dir, "01_horizontal_bar.png")
    pix_h.save(path_h)
    print(f"✅ 保存横向胶囊截屏: {path_h}, 尺寸: {pix_h.size()}")

    # 2. 截取 垂直侧边 HUD
    bar.set_mode(HUDMode.VERTICAL)
    bar.update_metrics(data)
    app.processEvents()
    time.sleep(0.1)
    pix_v = bar.grab()
    path_v = os.path.join(out_dir, "02_vertical_hud.png")
    pix_v.save(path_v)
    print(f"✅ 保存垂直侧边 HUD 截屏: {path_v}, 尺寸: {pix_v.size()}")

    # 3. 截取 极简微型徽章
    bar.set_mode(HUDMode.MINI)
    bar.update_metrics(data)
    app.processEvents()
    time.sleep(0.1)
    pix_m = bar.grab()
    path_m = os.path.join(out_dir, "03_mini_badge.png")
    pix_m.save(path_m)
    print(f"✅ 保存微型徽章截屏: {path_m}, 尺寸: {pix_m.size()}")

    bar.close()

    # 4. 截取 详细中枢仪表盘 Tab 1: 性能曲线
    dash = DashboardWindow()
    dash.show()
    dash.update_metrics(data)
    dash.tabs.setCurrentIndex(0)
    app.processEvents()
    time.sleep(0.1)
    pix_d1 = dash.grab()
    path_d1 = os.path.join(out_dir, "04_dashboard_tab1_curves.png")
    pix_d1.save(path_d1)
    print(f"✅ 保存仪表盘 Tab 1 曲线页: {path_d1}, 尺寸: {pix_d1.size()}")

    # 5. 截取 详细中枢仪表盘 Tab 2: 硬件全景与 18 核心热力图
    dash.tabs.setCurrentIndex(1)
    app.processEvents()
    time.sleep(0.1)
    pix_d2 = dash.grab()
    path_d2 = os.path.join(out_dir, "05_dashboard_tab2_hardware.png")
    pix_d2.save(path_d2)
    print(f"✅ 保存仪表盘 Tab 2 硬件全景页: {path_d2}, 尺寸: {pix_d2.size()}")

    # 6. 截取 详细中枢仪表盘 Tab 3: 进程追踪与设置
    dash.tabs.setCurrentIndex(2)
    app.processEvents()
    time.sleep(0.1)
    pix_d3 = dash.grab()
    path_d3 = os.path.join(out_dir, "06_dashboard_tab3_processes.png")
    pix_d3.save(path_d3)
    print(f"✅ 保存仪表盘 Tab 3 进程设置页: {path_d3}, 尺寸: {pix_d3.size()}")

    dash.close()
    app.quit()
    print("=== 全套截屏导出完成 ===")

if __name__ == "__main__":
    capture_ui()
