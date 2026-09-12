import sys
import os

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

from PyQt6.QtWidgets import QApplication
from PyQt6.QtCore import QTimer
from src.collector import SystemCollector, MetricData
from src.floating_bar import FloatingBar, HUDMode
from src.dashboard import DashboardWindow
from src.tray import TrayManager

def test_full_hud_system():
    print("=== 开始全新 HUD 多形态与专业中枢测试 ===")
    app = QApplication(sys.argv)

    collector = SystemCollector(interval=0.5)
    floating_bar = FloatingBar()
    dashboard = DashboardWindow()
    tray = TrayManager(app, floating_bar, dashboard, collector)

    # 构造专业级模拟遥测数据
    mock_data = MetricData(
        cpu_name="Intel(R) Core(TM) Ultra 5 125H",
        cpu_percent=32.4,
        cpu_freq_mhz=2400.0,
        cpu_physical_cores=14,
        cpu_logical_cores=18,
        cpu_cores=[12.0, 45.0, 78.0, 90.0, 22.0, 15.0, 30.0, 5.0, 60.0, 40.0, 10.0, 8.0, 95.0, 33.0, 18.0, 25.0, 14.0, 6.0],
        ram_percent=42.1,
        ram_used_gb=13.3,
        ram_total_gb=31.6,
        ram_committed_gb=16.5,
        ram_commit_total_gb=33.6,
        ram_commit_percent=49.1,
        gpu_available=True,
        gpu_name="NVIDIA GeForce RTX 4050 Laptop GPU",
        gpu_percent=65.0,
        gpu_clock_core_mhz=2055,
        gpu_clock_mem_mhz=8000,
        gpu_power_w=68.4,
        gpu_power_limit_w=97.7,
        gpu_pstate="P0",
        gpu_temp=62,
        gpu_mem_used_mb=2800.0,
        gpu_mem_total_mb=6141.0,
        gpu_mem_percent=45.6,
        net_recv_str="2.4 MB/s",
        net_sent_str="180 KB/s",
        net_ping_ms=28.0,
        disk_read_str="12.5 MB/s",
        disk_write_str="4.8 MB/s",
        disks=[{'mount': 'C:\\', 'used_gb': 330, 'total_gb': 950, 'percent': 34.7}],
        history_cpu=[10.0, 15.0, 25.0, 32.0, 40.0, 32.4] * 10,
        history_gpu=[20.0, 35.0, 50.0, 65.0, 70.0, 65.0] * 10,
        history_power=[25.0, 40.0, 55.0, 68.0, 72.0, 68.4] * 10,
        history_net_down=[100.0, 500.0, 1200.0, 2400.0] * 15,
        top_processes=[
            {'pid': 1001, 'name': 'Cyberpunk2077.exe', 'cpu_percent': 24.5, 'mem_mb': 4500.0},
            {'pid': 2002, 'name': 'Antigravity.exe', 'cpu_percent': 4.2, 'mem_mb': 350.0}
        ]
    )

    # 1. 验证横向胶囊形态
    floating_bar.set_mode(HUDMode.HORIZONTAL)
    floating_bar.show()
    floating_bar.update_metrics(mock_data)
    print("✅ 形态 1 [横向胶囊] 渲染成功，尺寸:", floating_bar.size())

    # 2. 验证垂直侧边 HUD
    floating_bar.set_mode(HUDMode.VERTICAL)
    floating_bar.update_metrics(mock_data)
    print("✅ 形态 2 [垂直侧边 HUD] 渲染成功，尺寸:", floating_bar.size())

    # 3. 验证极简微型徽章
    floating_bar.set_mode(HUDMode.MINI)
    floating_bar.update_metrics(mock_data)
    print("✅ 形态 3 [极简微型徽章] 渲染成功，尺寸:", floating_bar.size())

    # 4. 恢复默认横向
    floating_bar.set_mode(HUDMode.HORIZONTAL)

    # 5. 验证鼠标穿透模式
    floating_bar.set_click_through(True)
    assert floating_bar.click_through is True
    floating_bar.set_click_through(False)
    assert floating_bar.click_through is False
    print("✅ 鼠标穿透 (游戏免打扰) 切换正常")

    # 6. 验证仪表盘 3 大页面
    dashboard.show()
    dashboard.update_metrics(mock_data)
    print("✅ 专业中枢仪表盘渲染成功，尺寸:", dashboard.size())

    # 定时 1 秒关闭
    QTimer.singleShot(1000, lambda: (floating_bar.close(), dashboard.close(), app.quit()))
    app.exec()
    print("=== 所有 HUD 形态与专业中枢测试 100% 顺利通过！ ===")

if __name__ == "__main__":
    test_full_hud_system()
