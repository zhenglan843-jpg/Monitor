import sys
import os
from PyQt6.QtWidgets import QApplication
from PyQt6.QtCore import QTimer

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

from src.floating_bar import FloatingBar, HUDMode
from src.dashboard import DashboardWindow
from src.antigravity_collector import AntigravityCollector
from src.collector import SystemCollector

app = QApplication.instance() or QApplication(sys.argv)

bar = FloatingBar()
dash = DashboardWindow()
agy = AntigravityCollector()
sys_c = SystemCollector()

from src.collector import MetricData

# 采样一次真实数据
m_sys = MetricData(
    cpu_name="Intel(R) Core(TM) Ultra 5 125H",
    cpu_percent=12.5,
    ram_percent=32.0,
    ram_used_gb=10.1,
    ram_total_gb=31.6,
    gpu_available=True,
    gpu_name="NVIDIA GeForce RTX 4050 Laptop GPU",
    gpu_percent=18.0,
    gpu_temp=54,
    gpu_power_w=38.5,
    gpu_power_limit_w=85.0,
    gpu_clock_core_mhz=1890,
    net_recv_str="1.2 MB/s",
    net_ping_ms=18.5
)
m_agy = agy.sample_once()

bar.update_metrics(m_sys)
bar.update_antigravity_metrics(m_agy)

dash.update_metrics(m_sys)
dash.update_antigravity_metrics(m_agy)
# 切换到 Antigravity AI tab (第 4 个 tab，索引 3)
dash.tabs.setCurrentIndex(3)

shots_dir = os.path.join(os.path.dirname(__file__), "screenshots")
os.makedirs(shots_dir, exist_ok=True)

# 1. 截取胶囊栏
bar.set_mode(HUDMode.HORIZONTAL)
bar.show()
bar.repaint()
bar.grab().save(os.path.join(shots_dir, "hud_horizontal_ai.png"))

# 2. 截取垂直 HUD
bar.set_mode(HUDMode.VERTICAL)
bar.repaint()
bar.grab().save(os.path.join(shots_dir, "hud_vertical_ai.png"))

# 3. 截取微型徽章 HUD
bar.set_mode(HUDMode.MINI)
bar.repaint()
bar.grab().save(os.path.join(shots_dir, "hud_mini_ai.png"))

# 4. 截取仪表盘 Antigravity AI 面板
dash.show()
dash.repaint()
dash.grab().save(os.path.join(shots_dir, "dashboard_antigravity_tab.png"))

print("Screenshots saved successfully!")
app.quit()
