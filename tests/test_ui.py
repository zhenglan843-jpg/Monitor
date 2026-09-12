import sys
import os
import time

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

from PyQt6.QtWidgets import QApplication
from PyQt6.QtCore import QTimer
from src.collector import SystemCollector, MetricData
from src.floating_bar import FloatingBar
from src.dashboard import DashboardWindow
from src.tray import TrayManager

def smoke_test_ui():
    print("=== 开始 UI 界面与交互烟雾测试 ===")
    app = QApplication(sys.argv)

    collector = SystemCollector(interval=0.5)
    floating_bar = FloatingBar()
    dashboard = DashboardWindow()
    tray = TrayManager(app, floating_bar, dashboard, collector)

    # 模拟数据更新
    mock_data = MetricData(
        cpu_percent=24.5,
        cpu_freq_mhz=2800.0,
        ram_percent=45.2,
        ram_used_gb=14.2,
        ram_total_gb=32.0,
        gpu_available=True,
        gpu_name="NVIDIA GeForce RTX 4050 Laptop GPU",
        gpu_percent=18.0,
        gpu_temp=52,
        gpu_mem_percent=22.0,
        gpu_mem_used_mb=1300,
        gpu_mem_total_mb=6144,
        net_recv_str="1.2 MB/s",
        net_sent_str="128 KB/s",
        disks=[{'mount': 'C:\\', 'used_gb': 120, 'total_gb': 500, 'percent': 24.0}],
        top_processes=[{'pid': 1234, 'name': 'test.exe', 'cpu_percent': 12.0, 'mem_mb': 150.0}]
    )

    floating_bar.show()
    floating_bar.update_metrics(mock_data)
    dashboard.show()
    dashboard.update_metrics(mock_data)
    tray.update_tooltip(mock_data)

    print("✅ 悬浮窗显示正常，尺寸:", floating_bar.size())
    print("✅ 仪表盘显示正常，尺寸:", dashboard.size())

    # 定时 1 秒后自动关闭退出测试
    QTimer.singleShot(1000, lambda: (floating_bar.close(), dashboard.close(), app.quit()))

    app.exec()
    print("=== UI 烟雾测试顺利通过！ ===")

if __name__ == "__main__":
    smoke_test_ui()
