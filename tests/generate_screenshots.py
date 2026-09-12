import sys
import os
import math
import time

from PyQt6.QtWidgets import QApplication
from PyQt6.QtCore import Qt

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

from src.collector import MetricData
from src.antigravity_collector import AntigravityMetrics
from src.floating_bar import FloatingBar, HUDMode
from src.dashboard import DashboardWindow


def generate():
    app = QApplication.instance() or QApplication(sys.argv)
    out_dir = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "assets", "screenshots"))
    os.makedirs(out_dir, exist_ok=True)

    # 1. 模拟平滑逼真的 60 秒历史波形
    history_len = 60
    hist_cpu = [25.0 + 15.0 * math.sin(i * 0.15) + (i % 5) for i in range(history_len)]
    hist_gpu = [55.0 + 20.0 * math.cos(i * 0.12) + (i % 7) for i in range(history_len)]
    hist_power = [60.0 + 18.0 * math.sin(i * 0.18) for i in range(history_len)]
    hist_net = [1200.0 + 800.0 * math.sin(i * 0.2) + 300.0 * (i % 3) for i in range(history_len)]

    mock_hw = MetricData(
        cpu_name="Intel(R) Core(TM) Ultra 5 125H",
        cpu_percent=32.4,
        cpu_freq_mhz=3600.0,
        cpu_physical_cores=14,
        cpu_logical_cores=18,
        cpu_cores=[
            45.0, 52.0, 68.0, 41.0,
            55.0, 62.0, 38.0, 48.0,
            22.0, 18.0, 25.0, 20.0,
            19.0, 24.0, 16.0, 21.0,
            15.0, 18.0
        ],
        ram_percent=45.6,
        ram_used_gb=14.4,
        ram_total_gb=31.6,
        ram_committed_gb=18.5,
        ram_commit_total_gb=33.6,
        ram_commit_percent=55.0,
        gpu_available=True,
        gpu_name="NVIDIA GeForce RTX 4050 Laptop GPU",
        gpu_percent=68.0,
        gpu_clock_core_mhz=2150,
        gpu_clock_mem_mhz=8000,
        gpu_power_w=68.4,
        gpu_power_limit_w=95.0,
        gpu_pstate="P0",
        gpu_temp=58,
        gpu_mem_used_mb=2800.0,
        gpu_mem_total_mb=6141.0,
        gpu_mem_percent=45.6,
        net_recv_speed=2.4 * 1024 * 1024,
        net_sent_speed=180.0 * 1024,
        net_recv_str="2.4 MB/s",
        net_sent_str="180 KB/s",
        net_ping_ms=18.0,
        disk_read_str="12.5 MB/s",
        disk_write_str="4.8 MB/s",
        disks=[
            {'mount': 'C:\\', 'used_gb': 330, 'total_gb': 950, 'percent': 34.7},
            {'mount': 'D:\\', 'used_gb': 620, 'total_gb': 950, 'percent': 65.3}
        ],
        history_cpu=hist_cpu,
        history_gpu=hist_gpu,
        history_power=hist_power,
        history_net_down=hist_net,
        top_processes=[
            {'pid': 14208, 'name': 'chrome.exe', 'cpu_percent': 14.5, 'mem_mb': 2450.0},
            {'pid': 28560, 'name': 'Antigravity.exe', 'cpu_percent': 8.2, 'mem_mb': 820.0},
            {'pid': 9824, 'name': 'Code.exe', 'cpu_percent': 5.1, 'mem_mb': 1120.0},
            {'pid': 44720, 'name': 'explorer.exe', 'cpu_percent': 1.8, 'mem_mb': 410.0},
            {'pid': 38328, 'name': 'dwm.exe', 'cpu_percent': 1.2, 'mem_mb': 375.0}
        ]
    )

    mock_agy = AntigravityMetrics(
        is_running=True,
        active_conversation_id="f21a740c-5ba7-4c57-9990-c1d92e825967",
        active_title="开发Antigravity用量监控软件",
        step_count=135,
        context_tokens=78900,
        context_limit=1048576,
        context_percent=7.5,
        user_tokens=1200,
        model_tokens=6500,
        thinking_tokens=5200,
        tool_tokens=50200,
        base_system_tokens=15800,
        last_turn_input=180,
        last_turn_output=420,
        last_turn_total=600,
        today_tokens=680000,
        total_tokens=1850000,
        today_cost_usd=0.92,
        total_cost_usd=2.50,
        total_conversations=88,
        agent_status="待机就绪",
        status_color="#22c55e",
        model_breakdown={
            "Gemini 3.8 Flash (High)": {"cost_usd": 1.92, "count": 65, "tokens": 1420000},
            "Claude 3.5 Sonnet": {"cost_usd": 1.68, "count": 15, "tokens": 280000},
            "GPT-4o": {"cost_usd": 0.75, "count": 8, "tokens": 150000}
        },
        recent_conversations=[
            {"title": "开发Antigravity用量监控软件", "tokens": 78900, "mtime": "09-12 09:40"},
            {"title": "优化硬件采样引擎与波形走势", "tokens": 125400, "mtime": "09-12 08:30"},
            {"title": "实现极简微型徽章与HUD穿透模式", "tokens": 64200, "mtime": "09-11 22:15"},
            {"title": "重构系统托盘与内存释放工具", "tokens": 45800, "mtime": "09-11 20:05"},
            {"title": "设计NVML独立显卡驱动直读模块", "tokens": 92300, "mtime": "09-11 18:40"}
        ]
    )

    bar = FloatingBar()
    bar.show()

    # 1. 横向胶囊栏 - 硬件监控态
    bar.set_mode(HUDMode.HORIZONTAL)
    bar.update_metrics(mock_hw)
    bar.update_antigravity_metrics(AntigravityMetrics(is_running=False))
    app.processEvents()
    time.sleep(0.05)
    p_h = os.path.join(out_dir, "hud_horizontal.png")
    bar.grab().save(p_h)
    print(f"✅ 保存: {p_h}")

    # 2. 横向胶囊栏 - AI 活跃态
    bar.update_antigravity_metrics(mock_agy)
    app.processEvents()
    time.sleep(0.05)
    p_h_ai = os.path.join(out_dir, "hud_horizontal_ai.png")
    bar.grab().save(p_h_ai)
    print(f"✅ 保存: {p_h_ai}")

    # 3. 垂直侧边栏 - 硬件监控态
    bar.set_mode(HUDMode.VERTICAL)
    bar.update_metrics(mock_hw)
    bar.update_antigravity_metrics(AntigravityMetrics(is_running=False))
    app.processEvents()
    time.sleep(0.05)
    p_v = os.path.join(out_dir, "hud_vertical.png")
    bar.grab().save(p_v)
    print(f"✅ 保存: {p_v}")

    # 4. 垂直侧边栏 - AI 活跃态
    bar.update_antigravity_metrics(mock_agy)
    app.processEvents()
    time.sleep(0.05)
    p_v_ai = os.path.join(out_dir, "hud_vertical_ai.png")
    bar.grab().save(p_v_ai)
    print(f"✅ 保存: {p_v_ai}")

    # 5. 极简微型徽章 - 硬件监控态
    bar.set_mode(HUDMode.MINI)
    bar.update_metrics(mock_hw)
    bar.update_antigravity_metrics(AntigravityMetrics(is_running=False))
    app.processEvents()
    time.sleep(0.05)
    p_m = os.path.join(out_dir, "hud_mini.png")
    bar.grab().save(p_m)
    print(f"✅ 保存: {p_m}")

    # 6. 极简微型徽章 - AI 活跃态
    bar.update_antigravity_metrics(mock_agy)
    app.processEvents()
    time.sleep(0.05)
    p_m_ai = os.path.join(out_dir, "hud_mini_ai.png")
    bar.grab().save(p_m_ai)
    print(f"✅ 保存: {p_m_ai}")

    bar.close()

    # 7. 专业性能中枢仪表盘 - 4 大面板
    dash = DashboardWindow()
    dash.show()
    dash.update_metrics(mock_hw)
    dash.update_antigravity_metrics(mock_agy)

    # Tab 0: 曲线走势 (Curves)
    dash.tabs.setCurrentIndex(0)
    app.processEvents()
    time.sleep(0.05)
    p_c = os.path.join(out_dir, "dashboard_curves.png")
    dash.grab().save(p_c)
    print(f"✅ 保存: {p_c}")

    # Tab 1: 硬件全景 (Hardware)
    dash.tabs.setCurrentIndex(1)
    app.processEvents()
    time.sleep(0.05)
    p_hw = os.path.join(out_dir, "dashboard_hardware.png")
    dash.grab().save(p_hw)
    print(f"✅ 保存: {p_hw}")

    # Tab 2: 进程追踪 (Processes)
    dash.tabs.setCurrentIndex(2)
    app.processEvents()
    time.sleep(0.05)
    p_pr = os.path.join(out_dir, "dashboard_processes.png")
    dash.grab().save(p_pr)
    print(f"✅ 保存: {p_pr}")

    # Tab 3: Antigravity AI 面板
    dash.tabs.setCurrentIndex(3)
    app.processEvents()
    time.sleep(0.05)
    p_agy = os.path.join(out_dir, "dashboard_antigravity.png")
    dash.grab().save(p_agy)
    print(f"✅ 保存: {p_agy}")

    dash.close()
    app.quit()
    print("=== 全部 10 张高清截图重新生成完毕 ===")


if __name__ == "__main__":
    generate()
