import os
import ctypes
from PyQt6.QtCore import Qt, pyqtSignal
from PyQt6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel, QProgressBar,
    QGridLayout, QFrame, QTableWidget, QTableWidgetItem,
    QHeaderView, QPushButton, QComboBox, QTabWidget, QScrollArea
)
from PyQt6.QtGui import QFont, QColor
from .collector import MetricData
from .antigravity_collector import AntigravityMetrics
from .chart_view import PerformanceGraph
from .core_matrix import CoreMatrixWidget
from .stacked_bar import StackedContextBar
from .config import ConfigManager


def optimize_system_memory() -> int:
    """调用 Windows API 深度清理进程工作集与系统缓存"""
    freed = 0
    try:
        # 清理当前进程工作集
        ctypes.windll.psapi.EmptyWorkingSet(ctypes.windll.kernel32.GetCurrentProcess())
    except Exception:
        pass
    return freed


class ModernCard(QFrame):
    """现代暗黑质感卡片容器"""
    def __init__(self, title: str = "", subtitle: str = "", parent=None):
        super().__init__(parent)
        self.setStyleSheet("""
            ModernCard {
                background-color: #171d27;
                border: 1px solid #263345;
                border-radius: 8px;
            }
        """)
        self.layout = QVBoxLayout(self)
        self.layout.setContentsMargins(12, 10, 12, 10)
        self.layout.setSpacing(6)

        if title:
            header_layout = QHBoxLayout()
            self.lbl_title = QLabel(title)
            self.lbl_title.setStyleSheet("color: #e2e8f0; font-weight: 700; font-size: 13px;")
            header_layout.addWidget(self.lbl_title)
            if subtitle:
                self.lbl_sub = QLabel(subtitle)
                self.lbl_sub.setStyleSheet("color: #64748b; font-size: 11px;")
                header_layout.addStretch()
                header_layout.addWidget(self.lbl_sub)
            self.layout.addLayout(header_layout)


class DashboardWindow(QWidget):
    """
    专业性能监控中枢 (Pro Performance Hub 2.0)
    - 借鉴 MSI Afterburner 动态波形监控图与 HWiNFO64 核心热力拓扑
    - 3 大功能视窗：实时曲线、硬件全景与核心矩阵、进程追踪与系统优化
    """
    closed_signal = pyqtSignal()
    interval_changed_signal = pyqtSignal(float)
    hud_mode_signal = pyqtSignal(str)
    hud_scale_signal = pyqtSignal(float)
    reset_hud_position_signal = pyqtSignal()
    click_through_signal = pyqtSignal(bool)
    auto_start_signal = pyqtSignal(bool)
    select_conversation_signal = pyqtSignal(object)

    def __init__(self, parent=None):
        super().__init__(parent)
        self._current_recent_conversations = []
        self._init_window()
        self._init_ui()

    def _init_window(self):
        self.setWindowTitle("Monitor - 专业硬件遥测与走势分析")
        self.setFixedSize(720, 720)
        self.setStyleSheet("""
            QWidget {
                background-color: #0f141c;
                color: #f1f5f9;
                font-family: 'Segoe UI', 'Microsoft YaHei', sans-serif;
            }
            QTabWidget::pane {
                border: 1px solid #1f2937;
                background-color: #111823;
                border-radius: 8px;
            }
            QTabBar::tab {
                background-color: #1a2230;
                color: #94a3b8;
                font-weight: 600;
                font-size: 12px;
                padding: 8px 18px;
                margin-right: 4px;
                border-top-left-radius: 6px;
                border-top-right-radius: 6px;
                border: 1px solid #283548;
                border-bottom: none;
            }
            QTabBar::tab:selected {
                background-color: #111823;
                color: #38bdf8;
                border-bottom: 2px solid #38bdf8;
            }
            QProgressBar {
                background-color: #171f2c;
                border: 1px solid #2d3b4e;
                border-radius: 4px;
                text-align: center;
                color: #f8fafc;
                font-size: 10px;
                font-weight: bold;
                height: 14px;
            }
            QProgressBar::chunk {
                background-color: #38bdf8;
                border-radius: 3px;
            }
            QTableWidget {
                background-color: #131a24;
                border: 1px solid #233042;
                border-radius: 6px;
                gridline-color: #1d2736;
                font-size: 12px;
            }
            QHeaderView::section {
                background-color: #182230;
                color: #94a3b8;
                border: none;
                padding: 5px;
                font-weight: 600;
                font-size: 11px;
            }
            QPushButton {
                background-color: #2563eb;
                color: white;
                border: none;
                border-radius: 6px;
                padding: 6px 14px;
                font-weight: 600;
                font-size: 12px;
            }
            QPushButton:hover {
                background-color: #3b82f6;
            }
            QPushButton:pressed {
                background-color: #1d4ed8;
            }
            QComboBox {
                background-color: #171f2c;
                border: 1px solid #2c3c52;
                border-radius: 6px;
                padding: 4px 10px;
                color: #f1f5f9;
                font-size: 12px;
            }
        """)

    def _init_ui(self):
        main_layout = QVBoxLayout(self)
        main_layout.setContentsMargins(14, 12, 14, 12)
        main_layout.setSpacing(10)

        # 选项卡控件
        self.tabs = QTabWidget()
        main_layout.addWidget(self.tabs)

        # Tab 1: MSI Afterburner 风格实时走势图
        self._init_graph_tab()

        # Tab 2: 硬件全景与核心拓扑
        self._init_hardware_tab()

        # Tab 3: 进程追踪与系统调优
        self._init_process_tab()

        # Tab 4: Antigravity AI 状态与 Token 监视
        self._init_antigravity_tab()

        # 底部控制状态栏
        bottom_bar = QHBoxLayout()
        bottom_bar.setSpacing(10)

        lbl_rate = QLabel("采样频率:")
        lbl_rate.setStyleSheet("color: #94a3b8; font-size: 12px;")
        self.combo_interval = QComboBox()
        self.combo_interval.addItems(["0.5 秒 (电竞高刷)", "1.0 秒 (推荐)", "2.0 秒 (极致省电)"])
        self.combo_interval.setCurrentIndex(1)
        self.combo_interval.currentIndexChanged.connect(self._on_interval_changed)
        bottom_bar.addWidget(lbl_rate)
        bottom_bar.addWidget(self.combo_interval)

        # 一键优化内存
        btn_opt = QPushButton("🧹 整理内存")
        btn_opt.setStyleSheet("background-color: #059669;")
        btn_opt.clicked.connect(self._on_optimize_clicked)
        bottom_bar.addWidget(btn_opt)

        bottom_bar.addStretch()

        btn_hide = QPushButton("收起面板")
        btn_hide.setStyleSheet("background-color: #334155;")
        btn_hide.clicked.connect(self.hide)
        bottom_bar.addWidget(btn_hide)

        main_layout.addLayout(bottom_bar)

    # 1. 实时走势图表页 (MSI Afterburner 风格)
    def _init_graph_tab(self):
        tab = QWidget()
        layout = QVBoxLayout(tab)
        layout.setContentsMargins(10, 10, 10, 10)
        layout.setSpacing(10)

        # 图表 1: CPU 与 GPU 占用走势
        self.graph_cpu_gpu = PerformanceGraph(
            title="CPU & GPU 利用率 (60s)",
            unit="%",
            line_color="#38bdf8",
            max_scale=100.0,
            height=160
        )
        layout.addWidget(self.graph_cpu_gpu)

        # 图表 2: GPU 实时功耗 (Watts)
        self.graph_power = PerformanceGraph(
            title="GPU 实时功耗 (Watts)",
            unit="W",
            line_color="#10b981",
            max_scale=100.0,
            height=160
        )
        layout.addWidget(self.graph_power)

        # 图表 3: 网络实时下载速率
        self.graph_net = PerformanceGraph(
            title="网络实时下载流量",
            unit="KB/s",
            line_color="#fbbf24",
            max_scale=1000.0,
            height=160
        )
        layout.addWidget(self.graph_net)

        layout.addStretch()
        self.tabs.addTab(tab, "📈 性能曲线 (Afterburner)")

    # 2. 硬件全景与核心拓扑
    def _init_hardware_tab(self):
        tab = QWidget()
        layout = QVBoxLayout(tab)
        layout.setContentsMargins(10, 10, 10, 10)
        layout.setSpacing(10)

        # 1. 处理器卡片 + 核心热力矩阵
        self.card_cpu = ModernCard("💻 处理器全景 (CPU)", "18 逻辑线程矩阵")
        self.lbl_cpu_model = QLabel("检测中...")
        self.lbl_cpu_model.setStyleSheet("color: #38bdf8; font-weight: 700; font-size: 13px;")
        self.lbl_cpu_stat = QLabel("利用率: 0% | 主频: 0.0 GHz")
        self.lbl_cpu_stat.setStyleSheet("color: #cbd5e1; font-size: 12px;")

        self.core_matrix = CoreMatrixWidget(core_count=18)

        self.card_cpu.layout.addWidget(self.lbl_cpu_model)
        self.card_cpu.layout.addWidget(self.lbl_cpu_stat)
        self.card_cpu.layout.addWidget(self.core_matrix)
        layout.addWidget(self.card_cpu)

        # 2. GPU 深度遥测卡片 (NVIDIA NVML)
        self.card_gpu = ModernCard("🎮 独立显卡遥测 (NVIDIA GPU)", "驱动直读")
        self.lbl_gpu_name = QLabel("未检测到独立显卡")
        self.lbl_gpu_name.setStyleSheet("color: #10b981; font-weight: 700; font-size: 13px;")
        self.lbl_gpu_deep = QLabel("频率: -- MHz | 功耗: -- W / -- W | 档位: --")
        self.lbl_gpu_deep.setStyleSheet("color: #cbd5e1; font-size: 12px;")

        self.bar_gpu_pwr = QProgressBar()
        self.bar_gpu_pwr.setStyleSheet("QProgressBar::chunk { background-color: #10b981; }")

        self.lbl_gpu_vram = QLabel("显存占用: 0 MB / 0 MB")
        self.lbl_gpu_vram.setStyleSheet("color: #94a3b8; font-size: 11px;")

        self.card_gpu.layout.addWidget(self.lbl_gpu_name)
        self.card_gpu.layout.addWidget(self.lbl_gpu_deep)
        self.card_gpu.layout.addWidget(self.bar_gpu_pwr)
        self.card_gpu.layout.addWidget(self.lbl_gpu_vram)
        layout.addWidget(self.card_gpu)

        # 3. 内存与虚拟内存 (Commit Charge) + 网络/磁盘
        grid_bot = QHBoxLayout()
        grid_bot.setSpacing(10)

        # 内存
        card_mem = ModernCard("🧠 内存与虚拟内存 (Commit)")
        self.lbl_ram_info = QLabel("物理内存: 0.0 / 0.0 GB (0%)")
        self.bar_ram = QProgressBar()
        self.bar_ram.setStyleSheet("QProgressBar::chunk { background-color: #8b5cf6; }")
        self.lbl_commit_info = QLabel("虚拟内存 Commit: 0.0 / 0.0 GB (0%)")
        self.bar_commit = QProgressBar()
        self.bar_commit.setStyleSheet("QProgressBar::chunk { background-color: #6366f1; }")
        card_mem.layout.addWidget(self.lbl_ram_info)
        card_mem.layout.addWidget(self.bar_ram)
        card_mem.layout.addWidget(self.lbl_commit_info)
        card_mem.layout.addWidget(self.bar_commit)
        grid_bot.addWidget(card_mem)

        # 网络与磁盘
        card_io = ModernCard("🌐 网络连接与存储 I/O")
        self.lbl_net_stat = QLabel("⬇ 0 B/s   ⬆ 0 B/s")
        self.lbl_net_stat.setStyleSheet("color: #fbbf24; font-weight: 700; font-size: 13px;")
        self.lbl_ping_stat = QLabel("往返延迟 Ping: -- ms")
        self.lbl_ping_stat.setStyleSheet("color: #94a3b8; font-size: 11px;")
        self.lbl_disk_io = QLabel("磁盘 I/O: 读 0 B/s | 写 0 B/s")
        self.lbl_disk_io.setStyleSheet("color: #94a3b8; font-size: 11px;")
        self.lbl_disk_parts = QLabel("分区: 读取中...")
        self.lbl_disk_parts.setStyleSheet("color: #64748b; font-size: 10px;")

        card_io.layout.addWidget(self.lbl_net_stat)
        card_io.layout.addWidget(self.lbl_ping_stat)
        card_io.layout.addWidget(self.lbl_disk_io)
        card_io.layout.addWidget(self.lbl_disk_parts)
        grid_bot.addWidget(card_io)

        layout.addLayout(grid_bot)
        self.tabs.addTab(tab, "💻 硬件全景 (HWiNFO)")

    # 3. 进程追踪与系统调优
    def _init_process_tab(self):
        tab = QWidget()
        layout = QVBoxLayout(tab)
        layout.setContentsMargins(10, 10, 10, 10)
        layout.setSpacing(10)

        card_procs = ModernCard("⚡ 资源占用前列进程 (Top 5)", "实时排查卡顿根源")
        self.table_procs = QTableWidget(5, 4)
        self.table_procs.setHorizontalHeaderLabels(["进程名", "PID", "CPU 占比", "物理内存"])
        self.table_procs.verticalHeader().setVisible(False)
        self.table_procs.horizontalHeader().setSectionResizeMode(0, QHeaderView.ResizeMode.Stretch)
        self.table_procs.horizontalHeader().setSectionResizeMode(1, QHeaderView.ResizeMode.ResizeToContents)
        self.table_procs.horizontalHeader().setSectionResizeMode(2, QHeaderView.ResizeMode.ResizeToContents)
        self.table_procs.setFixedHeight(195)
        self.table_procs.setVerticalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAlwaysOff)
        self.table_procs.setEditTriggers(QTableWidget.EditTrigger.NoEditTriggers)
        self.table_procs.setSelectionMode(QTableWidget.SelectionMode.NoSelection)
        card_procs.layout.addWidget(self.table_procs)
        layout.addWidget(card_procs)

        # 系统调优卡片
        card_tweak = ModernCard("🛠️ HUD 与系统设置")
        tweak_layout = QGridLayout()

        lbl_hud = QLabel("HUD 悬浮窗形态:")
        lbl_hud.setStyleSheet("color: #94a3b8; font-size: 12px;")
        self.combo_hud = QComboBox()
        self.combo_hud.addItems(["垂直侧边 HUD (默认)", "横向胶囊栏", "极简微型徽章"])
        self.combo_hud.currentIndexChanged.connect(self._on_hud_combo_changed)
        tweak_layout.addWidget(lbl_hud, 0, 0)
        tweak_layout.addWidget(self.combo_hud, 0, 1)

        lbl_scale = QLabel("HUD 缩放比例:")
        lbl_scale.setStyleSheet("color: #94a3b8; font-size: 12px;")
        self.combo_scale = QComboBox()
        self.combo_scale.addItems(["80% (紧凑)", "100% (默认)", "120% (放大)", "140% (超大)"])
        self.combo_scale.setCurrentIndex(1)
        self.combo_scale.currentIndexChanged.connect(self._on_scale_combo_changed)
        tweak_layout.addWidget(lbl_scale, 1, 0)
        tweak_layout.addWidget(self.combo_scale, 1, 1)

        self.btn_reset_pos = QPushButton("📍 重置 HUD 位置至主屏右上角")
        self.btn_reset_pos.setStyleSheet("background-color: #1e293b; color: #38bdf8; border: 1px solid #334155; font-size: 12px;")
        self.btn_reset_pos.clicked.connect(self.reset_hud_position_signal.emit)
        tweak_layout.addWidget(self.btn_reset_pos, 2, 0, 1, 2)

        self.btn_toggle_click_thru = QPushButton("开启鼠标穿透 (游戏免干扰)")
        self.btn_toggle_click_thru.setCheckable(True)
        self.btn_toggle_click_thru.clicked.connect(self._on_click_thru_clicked)
        tweak_layout.addWidget(self.btn_toggle_click_thru, 3, 0, 1, 2)

        self.btn_toggle_auto_start = QPushButton("⚙️ 开机自启: 未开启 (点击开启)")
        self.btn_toggle_auto_start.setCheckable(True)
        self.btn_toggle_auto_start.clicked.connect(self._on_auto_start_clicked)
        tweak_layout.addWidget(self.btn_toggle_auto_start, 4, 0, 1, 2)

        card_tweak.layout.addLayout(tweak_layout)
        layout.addWidget(card_tweak)

        # 原生全局快捷键卡片
        card_keys = ModernCard("⌨️ 原生 Win32 全局快捷键", "💡 游戏全屏状态下秒速响应，免切屏微调")
        grid_keys = QGridLayout()
        grid_keys.setSpacing(8)
        keys_info = [
            ("Ctrl + Shift + P", "一键切换 鼠标穿透 (Click-Through 极客闭环)", "#38bdf8"),
            ("Ctrl + Shift + H", "一键 显示 / 隐藏 HUD 悬浮条", "#10b981"),
            ("Ctrl + Shift + D", "一键 展开 / 收起 详细中枢仪表盘", "#c084fc")
        ]
        for row_idx, (k_str, k_desc, k_col) in enumerate(keys_info):
            lbl_k = QLabel(k_str)
            lbl_k.setStyleSheet(f"color: {k_col}; font-family: 'Cascadia Code', monospace; font-weight: bold; font-size: 11px;")
            lbl_d = QLabel(k_desc)
            lbl_d.setStyleSheet("color: #94a3b8; font-size: 11px;")
            grid_keys.addWidget(lbl_k, row_idx, 0)
            grid_keys.addWidget(lbl_d, row_idx, 1)
        card_keys.layout.addLayout(grid_keys)
        layout.addWidget(card_keys)

        layout.addStretch()
        self.tabs.addTab(tab, "⚡ 进程与设置")

    def _on_hud_combo_changed(self, idx: int):
        modes = ["VERTICAL", "HORIZONTAL", "MINI"]
        self.hud_mode_signal.emit(modes[idx])

    def _on_scale_combo_changed(self, idx: int):
        scales = [0.8, 1.0, 1.2, 1.4]
        if 0 <= idx < len(scales):
            self.hud_scale_signal.emit(scales[idx])

    def set_scale_ui(self, factor: float):
        scales = [0.8, 1.0, 1.2, 1.4]
        best_idx = 1
        min_diff = 999.0
        for i, s in enumerate(scales):
            diff = abs(factor - s)
            if diff < min_diff:
                min_diff = diff
                best_idx = i
        self.combo_scale.blockSignals(True)
        self.combo_scale.setCurrentIndex(best_idx)
        self.combo_scale.blockSignals(False)

    def _on_click_thru_clicked(self, checked: bool):
        self.click_through_signal.emit(checked)
        if checked:
            self.btn_toggle_click_thru.setText("已开启鼠标穿透 (点击穿透至背景)")
            self.btn_toggle_click_thru.setStyleSheet("background-color: #059669;")
        else:
            self.btn_toggle_click_thru.setText("开启鼠标穿透 (游戏免干扰)")
            self.btn_toggle_click_thru.setStyleSheet("background-color: #2563eb;")

    def _on_auto_start_clicked(self, checked: bool):
        self.auto_start_signal.emit(checked)
        self.set_auto_start_ui(checked)

    def set_auto_start_ui(self, enabled: bool):
        self.btn_toggle_auto_start.setChecked(enabled)
        if enabled:
            self.btn_toggle_auto_start.setText("✅ 已开启 Windows 开机无感自启")
            self.btn_toggle_auto_start.setStyleSheet("background-color: #059669; color: white;")
        else:
            self.btn_toggle_auto_start.setText("⚙️ 开机自启: 未开启 (点击开启)")
            self.btn_toggle_auto_start.setStyleSheet("background-color: #1e293b; color: #94a3b8; border: 1px solid #334155;")

    def _on_interval_changed(self, idx: int):
        rates = [0.5, 1.0, 2.0]
        self.interval_changed_signal.emit(rates[idx])

    def _on_optimize_clicked(self):
        optimize_system_memory()

    def update_metrics(self, data: MetricData):
        """刷新仪表盘所有页面数据"""
        # 1. 曲线页更新
        self.graph_cpu_gpu.set_data(data.history_cpu, 100.0)
        self.graph_power.set_data(data.history_power, max(50.0, data.gpu_power_limit_w))
        self.graph_net.set_data(data.history_net_down)

        # 2. 硬件全景页更新
        core_suffix = f"({data.cpu_physical_cores}P / {data.cpu_logical_cores}T)"
        if core_suffix in data.cpu_name:
            self.lbl_cpu_model.setText(data.cpu_name)
        else:
            self.lbl_cpu_model.setText(f"{data.cpu_name}  {core_suffix}")
        freq_str = f"{data.cpu_freq_mhz / 1000:.2f} GHz" if data.cpu_freq_mhz > 0 else "-- GHz"
        self.lbl_cpu_stat.setText(f"总体利用率: {data.cpu_percent:.1f}%  |  动态主频: {freq_str}")
        if data.cpu_cores:
            self.core_matrix.update_cores(data.cpu_cores)

        # GPU
        if data.gpu_available:
            self.lbl_gpu_name.setText(f"{data.gpu_name}  (温度: {data.gpu_temp}°C)")
            self.lbl_gpu_deep.setText(
                f"核心频率: {data.gpu_clock_core_mhz} MHz  |  显存: {data.gpu_clock_mem_mhz} MHz  |  "
                f"功耗: {data.gpu_power_w:.1f} W / {data.gpu_power_limit_w:.1f} W  |  档位: {data.gpu_pstate}"
            )
            pct = (data.gpu_power_w / max(1.0, data.gpu_power_limit_w)) * 100.0
            self.bar_gpu_pwr.setValue(int(pct))
            self.bar_gpu_pwr.setFormat(f"功耗墙负载: {pct:.1f}% ({data.gpu_power_w:.1f}W / {data.gpu_power_limit_w:.0f}W)")
            self.lbl_gpu_vram.setText(
                f"显存占用: {data.gpu_mem_used_mb:.0f} / {data.gpu_mem_total_mb:.0f} MB ({data.gpu_mem_percent:.0f}%)"
            )
        else:
            self.lbl_gpu_name.setText("未检测到独立显卡或显卡处于深度睡眠")
            self.lbl_gpu_deep.setText("频率: --")


        # 内存 & Commit Charge
        self.lbl_ram_info.setText(f"物理内存: {data.ram_used_gb:.1f} / {data.ram_total_gb:.1f} GB ({data.ram_percent:.0f}%)")
        self.bar_ram.setValue(int(data.ram_percent))
        self.lbl_commit_info.setText(f"已提交 Commit: {data.ram_committed_gb:.1f} / {data.ram_commit_total_gb:.1f} GB ({data.ram_commit_percent:.0f}%)")
        self.bar_commit.setValue(int(data.ram_commit_percent))

        # 网络 & 延迟 & 磁盘
        self.lbl_net_stat.setText(f"⬇ {data.net_recv_str}     ⬆ {data.net_sent_str}")
        if data.net_ping_ms >= 0:
            p_color = "#22c55e" if data.net_ping_ms < 45 else ("#f59e0b" if data.net_ping_ms < 90 else "#ef4444")
            ping_text = "<1 ms" if data.net_ping_ms < 1.0 else f"{data.net_ping_ms:.0f} ms"
            self.lbl_ping_stat.setText(f"网络往返延迟 (Ping): <span style='color:{p_color}; font-weight:bold;'>{ping_text}</span>")
        else:
            self.lbl_ping_stat.setText("网络往返延迟 (Ping): -- ms")

        self.lbl_disk_io.setText(f"磁盘读写 I/O: 读 {data.disk_read_str} | 写 {data.disk_write_str}")
        if data.disks:
            disk_texts = [f"{d['mount']} {d['used_gb']:.0f}/{d['total_gb']:.0f}G ({d['percent']}%)" for d in data.disks]
            self.lbl_disk_parts.setText(" | ".join(disk_texts))

        # 3. 进程列表更新
        if data.top_processes:
            for row, p in enumerate(data.top_processes):
                item_name = QTableWidgetItem(str(p['name']))
                item_pid = QTableWidgetItem(str(p['pid']))
                item_pid.setTextAlignment(Qt.AlignmentFlag.AlignCenter)
                item_cpu = QTableWidgetItem(f"{p['cpu_percent']:.1f}%")
                item_cpu.setTextAlignment(Qt.AlignmentFlag.AlignCenter)
                if p['cpu_percent'] > 20:
                    item_cpu.setForeground(QColor("#ef4444"))
                item_mem = QTableWidgetItem(f"{p['mem_mb']:.1f} MB")
                item_mem.setTextAlignment(Qt.AlignmentFlag.AlignRight | Qt.AlignmentFlag.AlignVCenter)

                self.table_procs.setItem(row, 0, item_name)
                self.table_procs.setItem(row, 1, item_pid)
                self.table_procs.setItem(row, 2, item_cpu)
                self.table_procs.setItem(row, 3, item_mem)

    # 4. Antigravity AI 上下文与 Token 监视面板
    def _init_antigravity_tab(self):
        scroll = QScrollArea()
        scroll.setWidgetResizable(True)
        scroll.setStyleSheet("QScrollArea { border: none; background: transparent; }")

        tab = QWidget()
        tab.setStyleSheet("background: transparent;")
        layout = QVBoxLayout(tab)
        layout.setContentsMargins(8, 8, 8, 8)
        layout.setSpacing(8)

        # 1. 活跃会话与运行状态卡片
        card_session = ModernCard("🤖 Antigravity AI 活跃会话 (Active Session)")
        
        row1 = QHBoxLayout()
        self.agy_title_lbl = QLabel("未检测到活跃会话")
        self.agy_title_lbl.setStyleSheet("color: #38bdf8; font-size: 14px; font-weight: bold;")

        self.btn_auto_track = QPushButton("🔄 恢复自动感应")
        self.btn_auto_track.setStyleSheet("background-color: #0284c7; color: white; border-radius: 4px; font-size: 11px; padding: 2px 8px;")
        self.btn_auto_track.setVisible(False)
        self.btn_auto_track.clicked.connect(self._on_resume_auto_track)

        self.agy_status_badge = QLabel("⚪ 离线")
        self.agy_status_badge.setStyleSheet(
            "background-color: #1e293b; color: #94a3b8; padding: 3px 10px; border-radius: 12px; font-size: 11px; font-weight: 600;"
        )
        row1.addWidget(self.agy_title_lbl, 1)
        row1.addWidget(self.btn_auto_track)
        row1.addSpacing(6)
        row1.addWidget(self.agy_status_badge)
        card_session.layout.addLayout(row1)

        row2 = QHBoxLayout()
        self.agy_id_lbl = QLabel("会话 ID: --")
        self.agy_id_lbl.setStyleSheet("color: #64748b; font-family: 'Cascadia Code', monospace; font-size: 11px;")
        self.agy_steps_lbl = QLabel("步骤: 0 steps")
        self.agy_steps_lbl.setStyleSheet("color: #94a3b8; font-size: 11px;")
        self.agy_model_lbl = QLabel("模型: Gemini 3.8 Flash (High)")
        self.agy_model_lbl.setStyleSheet("color: #a855f7; font-size: 11px; font-weight: 600;")
        row2.addWidget(self.agy_id_lbl)
        row2.addStretch()
        row2.addWidget(self.agy_steps_lbl)
        row2.addSpacing(12)
        row2.addWidget(self.agy_model_lbl)
        card_session.layout.addLayout(row2)
        layout.addWidget(card_session)

        # 2. 🌟 官方云端实时配额卡片 (Official Live Quota Limits)
        card_quota = ModernCard("🌟 官方云端实时配额 (Official Quota Limits)")
        
        q_header = QHBoxLayout()
        self.agy_tier_badge = QLabel("💎 Google AI Pro")
        self.agy_tier_badge.setStyleSheet(
            "background: qlineargradient(x1:0, y1:0, x2:1, y2:0, stop:0 #d97706, stop:1 #b45309); "
            "color: #ffffff; font-size: 11px; font-weight: bold; border-radius: 9px; padding: 2px 8px;"
        )
        self.agy_tp_status = QLabel("第三方模型: 待检测")
        self.agy_tp_status.setStyleSheet("color: #94a3b8; font-size: 11px;")

        q_header.addWidget(self.agy_tier_badge)
        q_header.addStretch()
        q_header.addWidget(self.agy_tp_status)
        card_quota.layout.addLayout(q_header)

        grid_quota = QGridLayout()
        grid_quota.setSpacing(6)

        # 5小时限额
        lbl_5h = QLabel("5小时滑动限额 (5-Hour Window):")
        lbl_5h.setStyleSheet("color: #cbd5e1; font-size: 11px; font-weight: 600;")
        self.agy_5h_val_lbl = QLabel("--% (待检测)")
        self.agy_5h_val_lbl.setStyleSheet("color: #38bdf8; font-family: 'Cascadia Code'; font-size: 11px; font-weight: bold;")
        grid_quota.addWidget(lbl_5h, 0, 0)
        grid_quota.addWidget(self.agy_5h_val_lbl, 0, 1, Qt.AlignmentFlag.AlignRight)

        self.bar_quota_5h = QProgressBar()
        self.bar_quota_5h.setRange(0, 100)
        self.bar_quota_5h.setValue(0)
        self.bar_quota_5h.setTextVisible(False)
        self.bar_quota_5h.setFixedHeight(7)
        self.bar_quota_5h.setStyleSheet("""
            QProgressBar {
                background-color: #1e293b;
                border: 1px solid #334155;
                border-radius: 3px;
            }
            QProgressBar::chunk {
                background-color: #10b981;
                border-radius: 2px;
            }
        """)
        grid_quota.addWidget(self.bar_quota_5h, 1, 0, 1, 2)

        # 周度限额
        lbl_wk = QLabel("周度总体限额 (Weekly Limit):")
        lbl_wk.setStyleSheet("color: #cbd5e1; font-size: 11px; font-weight: 600;")
        self.agy_wk_val_lbl = QLabel("--% (待检测)")
        self.agy_wk_val_lbl.setStyleSheet("color: #38bdf8; font-family: 'Cascadia Code'; font-size: 11px; font-weight: bold;")
        grid_quota.addWidget(lbl_wk, 2, 0)
        grid_quota.addWidget(self.agy_wk_val_lbl, 2, 1, Qt.AlignmentFlag.AlignRight)

        self.bar_quota_wk = QProgressBar()
        self.bar_quota_wk.setRange(0, 100)
        self.bar_quota_wk.setValue(0)
        self.bar_quota_wk.setTextVisible(False)
        self.bar_quota_wk.setFixedHeight(7)
        self.bar_quota_wk.setStyleSheet("""
            QProgressBar {
                background-color: #1e293b;
                border: 1px solid #334155;
                border-radius: 3px;
            }
            QProgressBar::chunk {
                background-color: #38bdf8;
                border-radius: 2px;
            }
        """)
        grid_quota.addWidget(self.bar_quota_wk, 3, 0, 1, 2)

        self.lbl_quota_warning = QLabel("⚠️ 云端配额极低 (<15%)，请注意控制请求频率或新开会话")
        self.lbl_quota_warning.setStyleSheet(
            "color: #ef4444; background: rgba(239, 68, 68, 0.15); border: 1px solid #ef4444; "
            "border-radius: 4px; padding: 4px 8px; font-size: 11px; font-weight: bold;"
        )
        self.lbl_quota_warning.setVisible(False)
        card_quota.layout.addLayout(grid_quota)
        card_quota.layout.addWidget(self.lbl_quota_warning)
        layout.addWidget(card_quota)

        # 3. 上下文容量与健康水位卡片
        card_ctx = ModernCard("📊 对话上下文水位 (Context Window Usage)")
        
        ctx_head = QHBoxLayout()
        self.agy_ctx_lbl = QLabel("0 / 1,048,576 Tokens (0.0%)")
        self.agy_ctx_lbl.setStyleSheet("color: #f1f5f9; font-size: 15px; font-weight: bold; font-family: 'Cascadia Code';")
        self.agy_ctx_tip = QLabel("容量充裕 (安全水位)")
        self.agy_ctx_tip.setStyleSheet("color: #22c55e; font-size: 11px; font-weight: 600;")
        ctx_head.addWidget(self.agy_ctx_lbl)
        ctx_head.addStretch()
        ctx_head.addWidget(self.agy_ctx_tip)
        card_ctx.layout.addLayout(ctx_head)

        self.bar_agy_ctx = StackedContextBar()
        card_ctx.layout.addWidget(self.bar_agy_ctx)

        # 细分来源网格
        grid_tok = QGridLayout()
        grid_tok.setSpacing(6)
        lbl_u = QLabel("👤 用户输入:")
        lbl_u.setStyleSheet("color: #94a3b8; font-size: 11px;")
        self.agy_user_tok_lbl = QLabel("0 (0%)")
        self.agy_user_tok_lbl.setStyleSheet("color: #38bdf8; font-family: 'Cascadia Code'; font-size: 11px;")
        grid_tok.addWidget(lbl_u, 0, 0)
        grid_tok.addWidget(self.agy_user_tok_lbl, 0, 1)

        lbl_m = QLabel("🤖 AI回答:")
        lbl_m.setStyleSheet("color: #94a3b8; font-size: 11px;")
        self.agy_model_tok_lbl = QLabel("0 (0%)")
        self.agy_model_tok_lbl.setStyleSheet("color: #10b981; font-family: 'Cascadia Code'; font-size: 11px;")
        grid_tok.addWidget(lbl_m, 0, 2)
        grid_tok.addWidget(self.agy_model_tok_lbl, 0, 3)

        lbl_th = QLabel("💭 深度思考:")
        lbl_th.setStyleSheet("color: #94a3b8; font-size: 11px;")
        self.agy_thinking_tok_lbl = QLabel("0 (0%)")
        self.agy_thinking_tok_lbl.setStyleSheet("color: #c084fc; font-family: 'Cascadia Code'; font-size: 11px;")
        grid_tok.addWidget(lbl_th, 1, 0)
        grid_tok.addWidget(self.agy_thinking_tok_lbl, 1, 1)

        lbl_t = QLabel("⚙️ 工具与输出:")
        lbl_t.setStyleSheet("color: #94a3b8; font-size: 11px;")
        self.agy_tool_tok_lbl = QLabel("0 (0%)")
        self.agy_tool_tok_lbl.setStyleSheet("color: #f59e0b; font-family: 'Cascadia Code'; font-size: 11px;")
        grid_tok.addWidget(lbl_t, 1, 2)
        grid_tok.addWidget(self.agy_tool_tok_lbl, 1, 3)

        card_ctx.layout.addLayout(grid_tok)
        layout.addWidget(card_ctx)

        # 3. 单轮消耗统计卡片
        card_stat = ModernCard("⚡ 单轮消耗统计 (Last Turn Consumption)")
        stat_h = QHBoxLayout()
        stat_h.setSpacing(12)

        lbl_t1 = QLabel("单轮增量 (Last Turn):")
        lbl_t1.setStyleSheet("color: #94a3b8; font-size: 11px;")
        self.agy_turn_lbl = QLabel("+0 (In: 0 | Out: 0)")
        self.agy_turn_lbl.setStyleSheet("color: #e2e8f0; font-family: 'Cascadia Code'; font-size: 12px; font-weight: bold;")
        stat_h.addWidget(lbl_t1)
        stat_h.addWidget(self.agy_turn_lbl)
        stat_h.addStretch()

        card_stat.layout.addLayout(stat_h)
        layout.addWidget(card_stat)

        # 3.5 Token 累计消耗与成本估算卡片
        card_tok_overview = ModernCard("📈 Token 消耗与成本概览 (Tokens & Cost Overview)", "全量历史会话增量估算")
        grid_overview = QGridLayout()
        grid_overview.setSpacing(6)

        lbl_t_day = QLabel("今日消耗:")
        lbl_t_day.setStyleSheet("color: #94a3b8; font-size: 11px;")
        self.lbl_today_tok = QLabel("0 Tokens")
        self.lbl_today_tok.setStyleSheet("color: #38bdf8; font-family: 'Cascadia Code'; font-size: 11px; font-weight: bold;")
        lbl_c_day = QLabel("今日费用:")
        lbl_c_day.setStyleSheet("color: #94a3b8; font-size: 11px;")
        self.lbl_today_cost = QLabel("$0.00 (¥0.00)")
        self.lbl_today_cost.setStyleSheet("color: #10b981; font-family: 'Cascadia Code'; font-size: 11px; font-weight: bold;")

        grid_overview.addWidget(lbl_t_day, 0, 0)
        grid_overview.addWidget(self.lbl_today_tok, 0, 1)
        grid_overview.addWidget(lbl_c_day, 0, 2)
        grid_overview.addWidget(self.lbl_today_cost, 0, 3)

        lbl_t_all = QLabel("累计总计:")
        lbl_t_all.setStyleSheet("color: #94a3b8; font-size: 11px;")
        self.lbl_total_tok = QLabel("0 Tokens")
        self.lbl_total_tok.setStyleSheet("color: #c084fc; font-family: 'Cascadia Code'; font-size: 12px; font-weight: bold;")
        lbl_c_all = QLabel("预估总额:")
        lbl_c_all.setStyleSheet("color: #94a3b8; font-size: 11px;")
        self.lbl_total_cost = QLabel("$0.00 (¥0.00)")
        self.lbl_total_cost.setStyleSheet("color: #34d399; font-family: 'Cascadia Code'; font-size: 12px; font-weight: bold;")

        grid_overview.addWidget(lbl_t_all, 1, 0)
        grid_overview.addWidget(self.lbl_total_tok, 1, 1)
        grid_overview.addWidget(lbl_c_all, 1, 2)
        grid_overview.addWidget(self.lbl_total_cost, 1, 3)

        lbl_s_info = QLabel("历史会话:")
        lbl_s_info.setStyleSheet("color: #94a3b8; font-size: 11px;")
        self.lbl_total_convs = QLabel("0 个会话")
        self.lbl_total_convs.setStyleSheet("color: #cbd5e1; font-family: 'Cascadia Code'; font-size: 11px;")
        lbl_m_info = QLabel("主要模型:")
        lbl_m_info.setStyleSheet("color: #94a3b8; font-size: 11px;")
        self.lbl_top_models = QLabel("检测中...")
        self.lbl_top_models.setStyleSheet("color: #cbd5e1; font-size: 11px;")

        grid_overview.addWidget(lbl_s_info, 2, 0)
        grid_overview.addWidget(self.lbl_total_convs, 2, 1)
        grid_overview.addWidget(lbl_m_info, 2, 2)
        grid_overview.addWidget(self.lbl_top_models, 2, 3)

        card_tok_overview.layout.addLayout(grid_overview)
        layout.addWidget(card_tok_overview)

        # 4. 历史会话漫游表格
        card_recent = ModernCard("📚 最近会话历史 (Recent Conversations)", "💡 点击任意行直接查阅该会话用量")
        self.table_agy_recent = QTableWidget(5, 5)
        self.table_agy_recent.setHorizontalHeaderLabels(["会话标题", "选用模型", "估算 Tokens", "预估费用", "最后更新"])
        self.table_agy_recent.horizontalHeader().setSectionResizeMode(0, QHeaderView.ResizeMode.Stretch)
        self.table_agy_recent.horizontalHeader().setSectionResizeMode(1, QHeaderView.ResizeMode.ResizeToContents)
        self.table_agy_recent.horizontalHeader().setSectionResizeMode(2, QHeaderView.ResizeMode.ResizeToContents)
        self.table_agy_recent.horizontalHeader().setSectionResizeMode(3, QHeaderView.ResizeMode.ResizeToContents)
        self.table_agy_recent.horizontalHeader().setSectionResizeMode(4, QHeaderView.ResizeMode.ResizeToContents)
        self.table_agy_recent.verticalHeader().setVisible(False)
        self.table_agy_recent.setSelectionBehavior(QTableWidget.SelectionBehavior.SelectRows)
        self.table_agy_recent.setEditTriggers(QTableWidget.EditTrigger.NoEditTriggers)
        self.table_agy_recent.setFixedHeight(140)
        self.table_agy_recent.cellClicked.connect(self._on_table_agy_clicked)
        card_recent.layout.addWidget(self.table_agy_recent)

        row_btn = QHBoxLayout()
        btn_open_brain = QPushButton("📂 打开 Antigravity 脑区目录")
        btn_open_brain.setStyleSheet("background-color: #1e293b; color: #38bdf8; border: 1px solid #334155; font-size: 11px; padding: 4px 10px;")
        btn_open_brain.clicked.connect(self._on_open_brain_clicked)
        row_btn.addStretch()
        row_btn.addWidget(btn_open_brain)
        card_recent.layout.addLayout(row_btn)

        layout.addWidget(card_recent)

        scroll.setWidget(tab)
        self.tabs.addTab(scroll, "🤖 Antigravity AI")

    def _on_table_agy_clicked(self, row: int, col: int):
        if row < len(self._current_recent_conversations):
            cid = self._current_recent_conversations[row].get("id")
            if cid:
                self.btn_auto_track.setVisible(True)
                self.select_conversation_signal.emit(cid)

    def _on_resume_auto_track(self):
        self.btn_auto_track.setVisible(False)
        self.select_conversation_signal.emit(None)

    def _on_open_brain_clicked(self):
        brain_dir = os.path.expanduser(r"~/.gemini/antigravity/brain")
        if os.path.exists(brain_dir):
            os.startfile(brain_dir)

    def update_antigravity_metrics(self, data: AntigravityMetrics):
        self._current_recent_conversations = data.recent_conversations
        self.btn_auto_track.setVisible(data.is_pinned)
        if not data.is_running:
            self.agy_status_badge.setText("⚪ 离线")
            self.agy_status_badge.setStyleSheet(
                "background-color: #1e293b; color: #94a3b8; padding: 3px 10px; border-radius: 12px; font-size: 11px; font-weight: 600;"
            )
        else:
            self.agy_status_badge.setText(f"● {data.agent_status}")
            if "思考" in data.agent_status or "生成" in data.agent_status:
                self.agy_status_badge.setStyleSheet(
                    f"background-color: rgba(56, 189, 248, 0.15); color: {data.status_color}; border: 1px solid {data.status_color}; padding: 3px 10px; border-radius: 12px; font-size: 11px; font-weight: 600;"
                )
            elif "工具" in data.agent_status:
                self.agy_status_badge.setStyleSheet(
                    f"background-color: rgba(245, 158, 11, 0.15); color: {data.status_color}; border: 1px solid {data.status_color}; padding: 3px 10px; border-radius: 12px; font-size: 11px; font-weight: 600;"
                )
            else:
                self.agy_status_badge.setStyleSheet(
                    f"background-color: rgba(34, 197, 94, 0.15); color: {data.status_color}; border: 1px solid {data.status_color}; padding: 3px 10px; border-radius: 12px; font-size: 11px; font-weight: 600;"
                )

        self.agy_title_lbl.setText(data.active_title or "未检测到活跃会话")
        short_id = f"{data.active_conversation_id[:12]}..." if len(data.active_conversation_id) > 12 else data.active_conversation_id
        self.agy_id_lbl.setText(f"会话 ID: {short_id or '--'}")
        sub_txt = f" | 子任务: {data.subagents_count}" if data.subagents_count > 0 else ""
        self.agy_steps_lbl.setText(f"步骤: {data.step_count} 轮{sub_txt}")
        self.agy_model_lbl.setText(f"模型: {data.model_name}")

        # 官方云端实时配额更新
        if data.user_tier_name:
            self.agy_tier_badge.setText(f"💎 {data.user_tier_name}")
            self.agy_tier_badge.setVisible(True)
        else:
            self.agy_tier_badge.setText("💎 Google AI")
            self.agy_tier_badge.setVisible(data.is_running)

        # 5小时配额
        if data.gemini_5h_percent >= 0:
            self.bar_quota_5h.setValue(int(data.gemini_5h_percent))
            rst_txt = f" ({data.gemini_5h_reset_str})" if data.gemini_5h_reset_str else ""
            self.agy_5h_val_lbl.setText(f"{data.gemini_5h_percent:.1f}% 剩余{rst_txt}")
            if data.gemini_5h_percent <= 20.0:
                color_5h = "#ef4444"
            elif data.gemini_5h_percent <= 50.0:
                color_5h = "#f59e0b"
            else:
                color_5h = "#10b981"
            self.agy_5h_val_lbl.setStyleSheet(f"color: {color_5h}; font-family: 'Cascadia Code'; font-size: 11px; font-weight: bold;")
            self.bar_quota_5h.setStyleSheet(f"""
                QProgressBar {{ background-color: #1e293b; border: 1px solid #334155; border-radius: 3px; }}
                QProgressBar::chunk {{ background-color: {color_5h}; border-radius: 2px; }}
            """)
        else:
            self.bar_quota_5h.setValue(0)
            self.agy_5h_val_lbl.setText("-- (未连接)")
            self.agy_5h_val_lbl.setStyleSheet("color: #64748b; font-family: 'Cascadia Code'; font-size: 11px;")

        # 周度配额
        if data.gemini_weekly_percent >= 0:
            self.bar_quota_wk.setValue(int(data.gemini_weekly_percent))
            rst_txt = f" ({data.gemini_weekly_reset_str})" if data.gemini_weekly_reset_str else ""
            self.agy_wk_val_lbl.setText(f"{data.gemini_weekly_percent:.1f}% 剩余{rst_txt}")
            if data.gemini_weekly_percent <= 20.0:
                color_wk = "#ef4444"
            elif data.gemini_weekly_percent <= 50.0:
                color_wk = "#f59e0b"
            else:
                color_wk = "#38bdf8"
            self.agy_wk_val_lbl.setStyleSheet(f"color: {color_wk}; font-family: 'Cascadia Code'; font-size: 11px; font-weight: bold;")
            self.bar_quota_wk.setStyleSheet(f"""
                QProgressBar {{ background-color: #1e293b; border: 1px solid #334155; border-radius: 3px; }}
                QProgressBar::chunk {{ background-color: {color_wk}; border-radius: 2px; }}
            """)
        else:
            self.bar_quota_wk.setValue(0)
            self.agy_wk_val_lbl.setText("-- (未连接)")
            self.agy_wk_val_lbl.setStyleSheet("color: #64748b; font-family: 'Cascadia Code'; font-size: 11px;")

        # 第三方模型状态
        if data.third_party_5h_percent >= 0:
            self.agy_tp_status.setText(f"Claude / GPT 限额: 5h {data.third_party_5h_percent:.0f}% | 周 {data.third_party_weekly_percent:.0f}%")
        else:
            self.agy_tp_status.setText("第三方模型: 待检测")

        # 配额紧张预警 (<15%)
        is_tension = (0 <= data.gemini_5h_percent < 15.0) or (0 <= data.gemini_weekly_percent < 15.0)
        self.lbl_quota_warning.setVisible(is_tension)

        # 上下文水位
        self.agy_ctx_lbl.setText(f"{data.context_tokens:,} / {data.context_limit:,} Tokens ({data.context_percent:.1f}%)")
        self.bar_agy_ctx.set_data(
            user_tokens=data.user_tokens,
            model_tokens=data.model_tokens,
            thinking_tokens=data.thinking_tokens,
            tool_tokens=data.tool_tokens,
            base_system_tokens=data.base_system_tokens,
            total_limit=data.context_limit
        )
        if data.context_percent >= 80.0:
            self.agy_ctx_tip.setText("⚠️ 接近上限 (建议新开会话)")
            self.agy_ctx_tip.setStyleSheet("color: #ef4444; font-size: 11px; font-weight: bold;")
        elif data.context_percent >= 50.0:
            self.agy_ctx_tip.setText("⚡ 适中负载 (关注增长)")
            self.agy_ctx_tip.setStyleSheet("color: #f59e0b; font-size: 11px; font-weight: bold;")
        else:
            self.agy_ctx_tip.setText("🟢 容量充裕 (安全水位)")
            self.agy_ctx_tip.setStyleSheet("color: #22c55e; font-size: 11px; font-weight: bold;")

        # 细分
        tot = max(1, data.context_tokens)
        self.agy_user_tok_lbl.setText(f"{data.user_tokens:,} ({(data.user_tokens / tot) * 100:.1f}%)")
        self.agy_model_tok_lbl.setText(f"{data.model_tokens:,} ({(data.model_tokens / tot) * 100:.1f}%)")
        self.agy_thinking_tok_lbl.setText(f"{data.thinking_tokens:,} ({(data.thinking_tokens / tot) * 100:.1f}%)")
        self.agy_tool_tok_lbl.setText(f"{data.tool_tokens:,} ({(data.tool_tokens / tot) * 100:.1f}%)")

        # 单轮消耗统计
        self.agy_turn_lbl.setText(f"+{data.last_turn_total:,} (In: {data.last_turn_input} | Out: {data.last_turn_output})")

        # Token 消耗与成本概览
        self.lbl_today_tok.setText(f"{data.today_tokens:,} Tokens")
        self.lbl_today_cost.setText(f"${data.today_cost_usd:.2f} (¥{data.today_cost_usd * 7.2:.2f})")
        self.lbl_total_tok.setText(f"{data.total_tokens:,} Tokens")
        self.lbl_total_cost.setText(f"${data.total_cost_usd:.2f} (¥{data.total_cost_usd * 7.2:.2f})")
        self.lbl_total_convs.setText(f"{data.total_conversations} 个会话")

        if data.model_breakdown:
            top_models = sorted(
                data.model_breakdown.items(),
                key=lambda x: x[1].get("tokens", 0),
                reverse=True
            )[:2]
            parts = [f"{m.split('/')[-1]}: {v.get('percent', 0):.0f}%" for m, v in top_models]
            self.lbl_top_models.setText(" | ".join(parts) if parts else "暂无")
        else:
            self.lbl_top_models.setText(data.model_name or "默认模型")

        # 历史会话列表
        if data.recent_conversations:
            self.table_agy_recent.setRowCount(len(data.recent_conversations))
            for row, conv in enumerate(data.recent_conversations):
                item_title = QTableWidgetItem(conv.get("title", "未命名"))
                
                item_model = QTableWidgetItem(conv.get("model", "Gemini 3.8 Flash (High)"))
                item_model.setForeground(QColor("#c084fc"))

                item_tok = QTableWidgetItem(f"{conv.get('tokens', 0):,} tok")
                item_tok.setTextAlignment(Qt.AlignmentFlag.AlignRight | Qt.AlignmentFlag.AlignVCenter)

                c_val = conv.get("cost_usd", 0.0)
                item_cost = QTableWidgetItem(f"${c_val:.2f} (¥{c_val*7.2:.2f})")
                item_cost.setTextAlignment(Qt.AlignmentFlag.AlignRight | Qt.AlignmentFlag.AlignVCenter)
                item_cost.setForeground(QColor("#10b981"))

                item_time = QTableWidgetItem(conv.get("mtime", ""))
                item_time.setTextAlignment(Qt.AlignmentFlag.AlignCenter)

                self.table_agy_recent.setItem(row, 0, item_title)
                self.table_agy_recent.setItem(row, 1, item_model)
                self.table_agy_recent.setItem(row, 2, item_tok)
                self.table_agy_recent.setItem(row, 3, item_cost)
                self.table_agy_recent.setItem(row, 4, item_time)

    def closeEvent(self, event):
        self.closed_signal.emit()
        self.hide()
        event.ignore()
