from PyQt6.QtWidgets import QApplication
from PyQt6.QtGui import QImage, QPainter
from src.floating_bar import FloatingBar
from src.collector import MetricData

def run():
    app = QApplication([])
    bar = FloatingBar()
    bar.show()
    d = MetricData(
        cpu_percent=19,
        ram_percent=28,
        gpu_available=True,
        gpu_percent=11,
        gpu_temp=52,
        gpu_power_w=18.8,
        gpu_power_limit_w=95,
        net_recv_str='532.0 KB/s',
        net_ping_ms=-1
    )
    bar.update_metrics(d)
    app.processEvents()

    # Grab h_gpu
    pix = bar.h_gpu.grab()
    pix.save("d:/test/tests/h_gpu_render.png")
    print("Saved h_gpu_render.png, size:", pix.size())

if __name__ == "__main__":
    run()
