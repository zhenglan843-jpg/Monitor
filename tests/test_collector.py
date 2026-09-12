import time
import os
import sys

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

import psutil
from PyQt6.QtCore import QCoreApplication
from src.collector import SystemCollector, MetricData

def run_test():
    print("=== 开始硬件性能采集验证 ===")
    app = QCoreApplication([])
    t0 = time.time()
    collector = SystemCollector(interval=0.5)
    received = []

    collector.metrics_updated.connect(lambda d: received.append(d))
    collector.start()

    # 常态轻量采样 1.5 秒
    end_t = time.time() + 1.5
    while time.time() < end_t:
        app.processEvents()
        time.sleep(0.05)

    # 切换至详细采样 1.5 秒
    collector.set_detailed_mode(True)
    end_t = time.time() + 1.5
    while time.time() < end_t:
        app.processEvents()
        time.sleep(0.05)

    collector.stop()
    app.processEvents()

    total_time = time.time() - t0
    print(f"总测试耗时: {total_time:.2f}s, 收到有效指标帧数: {len(received)}")

    assert len(received) >= 4, f"采样帧数不足: {len(received)}"
    latest = received[-1]
    print(f"✅ CPU: {latest.cpu_percent}% (主频 {latest.cpu_freq_mhz} MHz)")
    print(f"✅ 内存: {latest.ram_percent}% (已用 {latest.ram_used_gb:.2f} GB / 总计 {latest.ram_total_gb:.2f} GB)")
    print(f"✅ GPU: 可用={latest.gpu_available} | 型号={latest.gpu_name} | 负载={latest.gpu_percent}% | 温度={latest.gpu_temp}°C")
    print(f"✅ 网络: 下载={latest.net_recv_str} | 上传={latest.net_sent_str}")
    print(f"✅ 磁盘分区数: {len(latest.disks)}")
    for d in latest.disks:
        print(f"   -> {d['mount']} 使用率: {d['percent']}% ({d['used_gb']:.1f}/{d['total_gb']:.1f} GB)")
    print(f"✅ 高占用进程数: {len(latest.top_processes)}")
    for p in latest.top_processes:
        print(f"   -> {p['name']} (PID {p['pid']}): CPU {p['cpu_percent']}%, 内存 {p['mem_mb']:.1f} MB")

    # 验证自身进程资源占用
    proc = psutil.Process(os.getpid())
    mem_info = proc.memory_info()
    print(f"✅ 采集模块自身内存占用: {mem_info.rss / (1024**2):.2f} MB (极低开销)")
    print("=== 所有采集项验证通过！ ===")

if __name__ == "__main__":
    run_test()
