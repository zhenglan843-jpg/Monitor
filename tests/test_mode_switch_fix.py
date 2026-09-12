import sys
import os

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

from PyQt6.QtWidgets import QApplication
from src.floating_bar import FloatingBar, HUDMode
from src.collector import MetricData

def verify_mode_switch():
    app = QApplication(sys.argv)
    bar = FloatingBar()
    bar.show()

    mock_data = MetricData(
        cpu_percent=15.0,
        ram_percent=32.0,
        gpu_available=True,
        gpu_name="NVIDIA GeForce RTX 4050",
        gpu_percent=24.0,
        gpu_temp=53,
        gpu_power_w=35.0,
        gpu_power_limit_w=95.0,
        gpu_clock_core_mhz=2100,
        net_recv_str="1.5 MB/s",
        net_sent_str="120 KB/s",
        net_ping_ms=25.0
    )

    # 1. 初始为垂直侧边 HUD (默认)
    bar.update_metrics(mock_data)
    app.processEvents()
    print("1. 初始垂直侧边 HUD 尺寸:", bar.size())
    assert bar.size().width() == 185 and bar.size().height() == 362, f"垂直 HUD 尺寸异常: {bar.size()}"
    assert bar.v_cpu.lbl_val.text() == "15%", "垂直 CPU 数值未显示"
    assert bar.v_gpu.lbl_val.text() == "24%", "垂直 GPU 数值未显示"

    # 2. 切换到极简微型徽章模式
    bar.set_mode(HUDMode.MINI)
    bar.update_metrics(mock_data)
    app.processEvents()
    print("2. 切换至微型徽章尺寸:", bar.size())
    assert bar.size().width() >= 200, f"微型徽章塌陷异常: {bar.size()}"
    assert bar.m_cpu.lbl_val.text() == "15%", "微型徽章 CPU 数值丢失"
    assert bar.m_ram.lbl_val.text() == "32%", "微型徽章 RAM 数值丢失"
    assert "24%" in bar.m_gpu.lbl_val.text(), "微型徽章 GPU 数值丢失"
    print("   微型徽章各指标内容: CPU =", bar.m_cpu.lbl_val.text(), ", GPU =", bar.m_gpu.lbl_val.text(), ", RAM =", bar.m_ram.lbl_val.text())

    # 3. 切换至横向胶囊栏
    bar.set_mode(HUDMode.HORIZONTAL)
    bar.update_metrics(mock_data)
    app.processEvents()
    print("3. 切换至横向胶囊尺寸:", bar.size())
    assert bar.size().width() > 500, f"切回横向尺寸异常: {bar.size()}"
    assert bar.h_cpu.lbl_val.text() == "15%", "切回横向 CPU 数值丢失"
    assert bar.h_ram.lbl_val.text() == "32%", "切回横向 RAM 数值丢失"
    assert "24%" in bar.h_gpu.lbl_val.text(), "切回横向 GPU 数值丢失"
    print("   横向各指标内容: CPU =", bar.h_cpu.lbl_val.text(), ", GPU =", bar.h_gpu.lbl_val.text(), ", ⬇ =", bar.h_net.lbl_val.text())

    # 4. 切换回垂直侧边 HUD
    bar.set_mode(HUDMode.VERTICAL)
    bar.update_metrics(mock_data)
    app.processEvents()
    print("4. 切回垂直侧边 HUD 尺寸:", bar.size())
    assert bar.size().width() == 185 and bar.size().height() == 362
    assert bar.v_gpu.lbl_val.text() == "24%"
    assert bar.v_cpu.lbl_val.text() == "15%"

    # 5. 再切换回横向胶囊
    bar.set_mode(HUDMode.HORIZONTAL)
    bar.update_metrics(mock_data)
    app.processEvents()
    print("5. 再次切回横向胶囊尺寸:", bar.size())
    assert bar.size().width() > 500

    bar.close()
    print("=== 模式切换与参数显示彻底验证通过！无任何塌陷与丢失！ ===")

if __name__ == "__main__":
    verify_mode_switch()
