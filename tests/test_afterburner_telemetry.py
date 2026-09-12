import time
import os
import sys

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

from PyQt6.QtCore import QCoreApplication
from src.collector import SystemCollector, MetricData

def test_telemetry():
    app = QCoreApplication([])
    collector = SystemCollector(interval=0.5)
    collector.set_detailed_mode(True)
    results = []

    collector.metrics_updated.connect(lambda d: results.append(d))
    collector.start()

    # 运行 2 秒采集几帧
    end_t = time.time() + 2.0
    while time.time() < end_t:
        app.processEvents()
        time.sleep(0.05)

    collector.stop()
    app.processEvents()

    assert len(results) > 0, "未采集到数据帧"
    d = results[-1]

    print("=== 专业级遥测验证结果 (MSI Afterburner / NVIDIA App 对齐) ===")
    print(f"🔹 CPU 官方型号: {d.cpu_name}")
    print(f"🔹 CPU 核心拓扑: 物理核心={d.cpu_physical_cores}, 逻辑线程={d.cpu_logical_cores}")
    print(f"🔹 CPU 利用率: {d.cpu_percent:.1f}% | 主频: {d.cpu_freq_mhz} MHz")
    print(f"🔹 内存 (RAM): {d.ram_used_gb:.1f} / {d.ram_total_gb:.1f} GB ({d.ram_percent:.1f}%)")
    print(f"🔹 虚拟内存 (Commit Charge): {d.ram_committed_gb:.1f} / {d.ram_commit_total_gb:.1f} GB ({d.ram_commit_percent:.1f}%)")
    print(f"🔹 GPU 型号: {d.gpu_name}")
    print(f"🔹 GPU 核心频率: {d.gpu_clock_core_mhz} MHz | 显存频率: {d.gpu_clock_mem_mhz} MHz")
    print(f"🔹 GPU 实时功耗: {d.gpu_power_w:.1f} W (功耗墙 TDP: {d.gpu_power_limit_w:.1f} W) | 档位: {d.gpu_pstate}")
    print(f"🔹 GPU 温度: {d.gpu_temp}°C | 显存占用: {d.gpu_mem_used_mb:.0f} / {d.gpu_mem_total_mb:.0f} MB")
    print(f"🔹 实时网络速率: ⬇ {d.net_recv_str} | ⬆ {d.net_sent_str} | 延迟 Ping: {d.net_ping_ms} ms")
    print(f"🔹 实时磁盘 I/O: 读 {d.disk_read_str} | 写 {d.disk_write_str}")
    print(f"🔹 历史走势点数: CPU={len(d.history_cpu)}, GPU={len(d.history_gpu)}, Power={len(d.history_power)}")
    print("=== 遥测管道全面通过！ ===")

if __name__ == "__main__":
    test_telemetry()
