import sys
import os
import time

if sys.stdout and hasattr(sys.stdout, "reconfigure"):
    try:
        sys.stdout.reconfigure(encoding="utf-8")
    except Exception:
        pass

# Add project root to sys.path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

from PyQt6.QtWidgets import QApplication
from PyQt6.QtCore import Qt
from src.collector import MetricData
from src.floating_bar import FloatingBar, HUDMode
from src.dashboard import DashboardWindow

def run_stress_test():
    app = QApplication(sys.argv)
    
    # Generate extreme stress test data
    history_len = 60
    stress_data = MetricData(
        cpu_name="Intel(R) Core(TM) Ultra 5 125H (14P / 18T)",
        cpu_percent=100.0,
        cpu_freq_mhz=4850.0,
        cpu_physical_cores=14,
        cpu_logical_cores=18,
        cpu_cores=[98.5, 100.0, 95.2, 99.0, 97.4, 100.0, 96.1, 94.8, 99.9, 100.0, 98.2, 97.1, 95.5, 99.2, 96.0, 98.8, 100.0, 99.5],
        
        ram_percent=98.5,
        ram_used_gb=31.1,
        ram_total_gb=31.6,
        ram_committed_gb=31.0,
        ram_commit_total_gb=33.6,
        ram_commit_percent=92.4,
        
        gpu_available=True,
        gpu_name="NVIDIA GeForce RTX 4050 Laptop GPU",
        gpu_percent=100.0,
        gpu_clock_core_mhz=2450,
        gpu_clock_mem_mhz=8500,
        gpu_power_w=115.5,
        gpu_power_limit_w=115.0,
        gpu_pstate="P0",
        gpu_mem_percent=99.3,
        gpu_mem_used_mb=6100.0,
        gpu_mem_total_mb=6141.0,
        gpu_temp=89,
        
        net_recv_speed=128.5 * 1024 * 1024,
        net_sent_speed=54.2 * 1024 * 1024,
        net_recv_str="128.5 MB/s",
        net_sent_str="54.2 MB/s",
        net_ping_ms=125.0,
        
        disk_read_speed=450.2 * 1024 * 1024,
        disk_write_speed=380.5 * 1024 * 1024,
        disk_read_str="450.2 MB/s",
        disk_write_str="380.5 MB/s",
        disks=[
            {'mount': 'C:', 'total_gb': 952.0, 'used_gb': 920.0, 'percent': 96.6},
            {'mount': 'D:', 'total_gb': 954.0, 'used_gb': 890.0, 'percent': 93.3}
        ],
        
        history_cpu=[95.0 + (i % 5) for i in range(history_len)],
        history_gpu=[90.0 + (i % 10) for i in range(history_len)],
        history_ram=[98.0 for _ in range(history_len)],
        history_power=[100.0 + (i % 15) for i in range(history_len)],
        history_net_down=[125000.0 + (i * 100) for i in range(history_len)],
        
        top_processes=[
            {"name": "Cyberpunk2077.exe", "pid": 12844, "cpu_percent": 85.6, "mem_mb": 14520.5},
            {"name": "BlenderRender.exe", "pid": 19482, "cpu_percent": 12.4, "mem_mb": 8420.0},
            {"name": "chrome.exe", "pid": 8421, "cpu_percent": 1.5, "mem_mb": 2150.3},
            {"name": "Antigravity.exe", "pid": 45340, "cpu_percent": 0.2, "mem_mb": 420.0},
            {"name": "System.exe", "pid": 4, "cpu_percent": 0.3, "mem_mb": 180.2}
        ]
    )
    
    out_dir = os.path.join(os.path.dirname(__file__), "screenshots")
    os.makedirs(out_dir, exist_ok=True)
    
    floating_bar = FloatingBar()
    dashboard = DashboardWindow()
    
    # 1. Update with extreme metrics
    floating_bar.update_metrics(stress_data)
    dashboard.update_metrics(stress_data)
    app.processEvents()
    
    # 2. Capture Horizontal HUD under stress
    floating_bar.set_mode(HUDMode.HORIZONTAL)
    floating_bar.show()
    app.processEvents()
    time.sleep(0.1)
    floating_bar.grab().save(os.path.join(out_dir, "stress_01_horizontal.png"))
    
    # 3. Capture Vertical HUD under stress
    floating_bar.set_mode(HUDMode.VERTICAL)
    app.processEvents()
    time.sleep(0.1)
    floating_bar.grab().save(os.path.join(out_dir, "stress_02_vertical.png"))
    
    # 4. Capture Mini HUD under stress
    floating_bar.set_mode(HUDMode.MINI)
    app.processEvents()
    time.sleep(0.1)
    floating_bar.grab().save(os.path.join(out_dir, "stress_03_mini.png"))
    
    # 5. Dashboard Tab 1 (Curves) under stress
    dashboard.show()
    dashboard.tabs.setCurrentIndex(0)
    app.processEvents()
    time.sleep(0.1)
    dashboard.grab().save(os.path.join(out_dir, "stress_04_dash_curves.png"))
    
    # 6. Dashboard Tab 2 (Hardware) under stress
    dashboard.tabs.setCurrentIndex(1)
    app.processEvents()
    time.sleep(0.1)
    dashboard.grab().save(os.path.join(out_dir, "stress_05_dash_hardware.png"))
    
    # 7. Dashboard Tab 3 (Processes) under stress
    dashboard.tabs.setCurrentIndex(2)
    app.processEvents()
    time.sleep(0.1)
    dashboard.grab().save(os.path.join(out_dir, "stress_06_dash_procs.png"))
    
    print("ALL_STRESS_SCREENSHOTS_CAPTURED")
    app.quit()

if __name__ == "__main__":
    run_stress_test()
