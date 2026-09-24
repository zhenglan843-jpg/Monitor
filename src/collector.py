import sys
import time
import os
import socket
import threading
import collections
import ctypes
from ctypes import wintypes
import struct
from dataclasses import dataclass, field
from typing import List, Dict, Any
from PyQt6.QtCore import QThread, pyqtSignal

import psutil
import warnings

if sys.stdout and hasattr(sys.stdout, "reconfigure"):
    try:
        sys.stdout.reconfigure(encoding="utf-8")
    except Exception:
        pass
if sys.stderr and hasattr(sys.stderr, "reconfigure"):
    try:
        sys.stderr.reconfigure(encoding="utf-8")
    except Exception:
        pass

try:
    with warnings.catch_warnings():
        warnings.simplefilter("ignore")
        import pynvml
    _HAS_NVML = True
except ImportError:
    _HAS_NVML = False


class MEMORYSTATUSEX(ctypes.Structure):
    _fields_ = [
        ('dwLength', ctypes.c_ulong),
        ('dwMemoryLoad', ctypes.c_ulong),
        ('ullTotalPhys', ctypes.c_ulonglong),
        ('ullAvailPhys', ctypes.c_ulonglong),
        ('ullTotalPageFile', ctypes.c_ulonglong),
        ('ullAvailPageFile', ctypes.c_ulonglong),
        ('ullTotalVirtual', ctypes.c_ulonglong),
        ('ullAvailVirtual', ctypes.c_ulonglong),
        ('sullAvailExtendedVirtual', ctypes.c_ulonglong),
    ]


class IP_OPTION_INFORMATION(ctypes.Structure):
    _fields_ = [
        ('Ttl', ctypes.c_ubyte),
        ('Tos', ctypes.c_ubyte),
        ('Flags', ctypes.c_ubyte),
        ('OptionsSize', ctypes.c_ubyte),
        ('OptionsData', ctypes.c_void_p),
    ]


class ICMP_ECHO_REPLY(ctypes.Structure):
    _fields_ = [
        ('Address', wintypes.ULONG),
        ('Status', wintypes.ULONG),
        ('RoundTripTime', wintypes.ULONG),
        ('DataSize', wintypes.USHORT),
        ('Reserved', wintypes.USHORT),
        ('Data', ctypes.c_void_p),
        ('Options', IP_OPTION_INFORMATION),
    ]


try:
    _iphlpapi = ctypes.windll.iphlpapi
    _iphlpapi.IcmpCreateFile.restype = wintypes.HANDLE
    _iphlpapi.IcmpCloseHandle.argtypes = [wintypes.HANDLE]
    _iphlpapi.IcmpCloseHandle.restype = wintypes.BOOL
    _iphlpapi.IcmpSendEcho.argtypes = [
        wintypes.HANDLE,
        wintypes.ULONG,
        wintypes.LPVOID,
        wintypes.WORD,
        ctypes.c_void_p,
        wintypes.LPVOID,
        wintypes.DWORD,
        wintypes.DWORD,
    ]
    _iphlpapi.IcmpSendEcho.restype = wintypes.DWORD
    _HAS_ICMP_API = True
except Exception:
    _HAS_ICMP_API = False


class PDH_FMT_COUNTERVALUE_ITEM_W(ctypes.Structure):
    _fields_ = [
        ('szName', wintypes.LPWSTR),
        ('CStatus', wintypes.DWORD),
        ('dummy', wintypes.DWORD),
        ('doubleValue', ctypes.c_double)
    ]


class PdhGpuSampler:
    """Windows 原生性能计数器 GPU 采样器 (跨厂商支持 AMD / Intel Arc / 核显 / 深度睡眠独显)"""
    def __init__(self):
        self.available = False
        self._h_query = wintypes.HANDLE()
        self._h_counter = wintypes.HANDLE()
        try:
            self._pdh = ctypes.windll.pdh
            if self._pdh.PdhOpenQueryW(None, 0, ctypes.byref(self._h_query)) == 0:
                res = self._pdh.PdhAddEnglishCounterW(
                    self._h_query,
                    r'\GPU Engine(*_engtype_3D)\Utilization Percentage',
                    0,
                    ctypes.byref(self._h_counter)
                )
                if res == 0:
                    self._pdh.PdhCollectQueryData(self._h_query)
                    self.available = True
        except Exception:
            self.available = False

    def sample(self) -> float:
        if not self.available:
            return 0.0
        try:
            if self._pdh.PdhCollectQueryData(self._h_query) != 0:
                return 0.0
            buffer_size = wintypes.DWORD(0)
            item_count = wintypes.DWORD(0)
            PDH_FMT_DOUBLE = 0x00000200
            self._pdh.PdhGetFormattedCounterArrayW(
                self._h_counter, PDH_FMT_DOUBLE, ctypes.byref(buffer_size), ctypes.byref(item_count), None
            )
            if buffer_size.value == 0:
                return 0.0
            buf = ctypes.create_string_buffer(buffer_size.value)
            if self._pdh.PdhGetFormattedCounterArrayW(
                self._h_counter, PDH_FMT_DOUBLE, ctypes.byref(buffer_size), ctypes.byref(item_count), ctypes.byref(buf)
            ) == 0:
                items = ctypes.cast(buf, ctypes.POINTER(PDH_FMT_COUNTERVALUE_ITEM_W))
                total = sum(items[i].doubleValue for i in range(item_count.value) if items[i].CStatus == 0)
                return max(0.0, min(100.0, float(total)))
        except Exception:
            pass
        return 0.0

    def close(self):
        if self.available and self._h_query:
            try:
                self._pdh.PdhCloseQuery(self._h_query)
            except Exception:
                pass
            self.available = False


def format_speed(bytes_per_sec: float) -> str:
    """智能格式化速率（B/s、KB/s、MB/s、GB/s）"""
    if bytes_per_sec < 1024:
        return f"{int(bytes_per_sec)} B/s"
    elif bytes_per_sec < 1024 * 1024:
        return f"{bytes_per_sec / 1024:.1f} KB/s"
    elif bytes_per_sec < 1024 * 1024 * 1024:
        return f"{bytes_per_sec / (1024 * 1024):.1f} MB/s"
    else:
        return f"{bytes_per_sec / (1024 * 1024 * 1024):.2f} GB/s"


def format_size(bytes_num: float) -> str:
    """格式化容量"""
    return f"{bytes_num / (1024 ** 3):.1f} GB"


@dataclass
class MetricData:
    # CPU (类似 Afterburner & HWiNFO 深度信息)
    cpu_name: str = "Processor"
    cpu_percent: float = 0.0
    cpu_freq_mhz: float = 0.0
    cpu_physical_cores: int = 0
    cpu_logical_cores: int = 0
    cpu_cores: List[float] = field(default_factory=list)

    # RAM & Commit Charge 虚拟内存 (游戏/应用防爆内存关键指标)
    ram_percent: float = 0.0
    ram_used_gb: float = 0.0
    ram_total_gb: float = 0.0
    ram_committed_gb: float = 0.0
    ram_commit_total_gb: float = 0.0
    ram_commit_percent: float = 0.0

    # GPU (NVIDIA NVML 专业级深度遥测 - 核心/显存频率、功耗瓦数、功耗墙、P-State)
    gpu_available: bool = False
    gpu_name: str = ""
    gpu_percent: float = 0.0
    gpu_clock_core_mhz: int = 0
    gpu_clock_mem_mhz: int = 0
    gpu_power_w: float = 0.0
    gpu_power_limit_w: float = 0.0
    gpu_pstate: str = "--"
    gpu_mem_percent: float = 0.0
    gpu_mem_used_mb: float = 0.0
    gpu_mem_total_mb: float = 0.0
    gpu_temp: int = 0

    # Network (实时上传下载 + 游戏 Ping 往返延迟)
    net_recv_speed: float = 0.0
    net_sent_speed: float = 0.0
    net_recv_str: str = "0 B/s"
    net_sent_str: str = "0 B/s"
    net_ping_ms: float = -1.0

    # Disk I/O (读写吞吐速率与分区使用量)
    disk_read_speed: float = 0.0
    disk_write_speed: float = 0.0
    disk_read_str: str = "0 B/s"
    disk_write_str: str = "0 B/s"
    disks: List[Dict[str, Any]] = field(default_factory=list)

    # Battery
    battery_percent: int = -1
    battery_plugged: bool = True

    # 60 秒平滑历史滚动数据 (供 MSI Afterburner 风格走势图与迷你 Sparkline 使用)
    history_cpu: List[float] = field(default_factory=list)
    history_gpu: List[float] = field(default_factory=list)
    history_ram: List[float] = field(default_factory=list)
    history_power: List[float] = field(default_factory=list)
    history_net_down: List[float] = field(default_factory=list)

    # Top 进程 (按需采样，常态为空避免开销)
    top_processes: List[Dict[str, Any]] = field(default_factory=list)


class SystemCollector(QThread):
    """
    高性能深度硬件采样引擎
    - 参考 MSI Afterburner、NVIDIA App、HWiNFO64 底层采样架构
    - 原生直调 NVML、GlobalMemoryStatusEx、psutil 底层性能计数器
    - 常态仅需 < 4ms 极速采集，低功耗、低占用
    """
    metrics_updated = pyqtSignal(MetricData)

    def __init__(self, interval: float = 1.0, parent=None):
        super().__init__(parent)
        self.interval = interval
        self.running = True
        self.detailed_mode = False

        # 硬件静态信息缓存
        self._cpu_name = self._detect_cpu_name()
        self._cpu_physical = psutil.cpu_count(logical=False) or 0
        self._cpu_logical = psutil.cpu_count(logical=True) or 0

        # 网络 I/O 状态
        self._last_net_time = time.monotonic()
        initial_net = psutil.net_io_counters()
        self._last_bytes_recv = initial_net.bytes_recv
        self._last_bytes_sent = initial_net.bytes_sent

        # 磁盘 I/O 状态
        self._last_disk_time = time.monotonic()
        try:
            initial_disk = psutil.disk_io_counters()
            self._last_disk_read = initial_disk.read_bytes if initial_disk else 0
            self._last_disk_write = initial_disk.write_bytes if initial_disk else 0
        except Exception:
            self._last_disk_read = 0
            self._last_disk_write = 0

        # 网络 Ping 延迟异步缓存与常驻守护线程
        self._last_ping_ms = -1.0
        self._ping_fail_count = 0
        self._stop_event = threading.Event()

        # 显卡初始化 (NVML + Windows PDH 通用 Fallback)
        self._pdh_gpu = PdhGpuSampler()
        self._nvml_initialized = False
        self._gpu_handle = None
        self._gpu_name = ""
        self._fallback_gpu_name = ""
        self._gpu_power_limit = 0.0
        self._init_gpu()

        # 启动常驻轻量 Ping 守护线程 (杜绝频繁创建/销毁线程开销)
        self._ping_thread = threading.Thread(target=self._ping_worker_loop, daemon=True)
        self._ping_thread.start()

        # 详细模式节流缓存
        self._cached_disks: List[Dict[str, Any]] = []
        self._last_disk_sample_time = 0.0
        self._cached_top_procs: List[Dict[str, Any]] = []
        self._last_proc_sample_time = 0.0

        # 60 秒历史循环队列 (预填充 60 个 0)
        self._hist_cpu = collections.deque([0.0] * 60, maxlen=60)
        self._hist_gpu = collections.deque([0.0] * 60, maxlen=60)
        self._hist_ram = collections.deque([0.0] * 60, maxlen=60)
        self._hist_power = collections.deque([0.0] * 60, maxlen=60)
        self._hist_net = collections.deque([0.0] * 60, maxlen=60)

        # 预热 CPU 采样器
        psutil.cpu_percent(interval=None)

    def _detect_cpu_name(self) -> str:
        """从 Windows 注册表直读 CPU 完整官方型号名"""
        try:
            import winreg
            key = winreg.OpenKey(winreg.HKEY_LOCAL_MACHINE, r'HARDWARE\DESCRIPTION\System\CentralProcessor\0')
            name, _ = winreg.QueryValueEx(key, 'ProcessorNameString')
            return name.strip()
        except Exception:
            import platform
            return platform.processor() or "CPU Processor"

    def _detect_fallback_gpu(self) -> str:
        """从 Windows 注册表探测已安装的显卡型号 (适配 AMD Radeon / Intel Arc / 核显)"""
        try:
            import winreg
            base_key = r'SYSTEM\CurrentControlSet\Control\Class\{4d36e968-e325-11ce-bfc1-08002be10318}'
            with winreg.OpenKey(winreg.HKEY_LOCAL_MACHINE, base_key) as key:
                num_subkeys = winreg.QueryInfoKey(key)[0]
                candidates = []
                for i in range(num_subkeys):
                    subkey_name = winreg.EnumKey(key, i)
                    if subkey_name.isdigit():
                        try:
                            with winreg.OpenKey(key, subkey_name) as subkey:
                                desc, _ = winreg.QueryValueEx(subkey, 'DriverDesc')
                                desc_str = str(desc).strip()
                                if desc_str and not any(k in desc_str.lower() for k in ["remote", "basic", "virtual", "rdp"]):
                                    candidates.append(desc_str)
                        except Exception:
                            pass
                if candidates:
                    for c in candidates:
                        if any(k in c.lower() for k in ["geforce", "rtx", "gtx", "radeon", "arc"]):
                            return c
                    return candidates[0]
        except Exception:
            pass
        return ""

    def _init_gpu(self):
        if _HAS_NVML:
            try:
                pynvml.nvmlInit()
                device_count = pynvml.nvmlDeviceGetCount()
                if device_count > 0:
                    self._gpu_handle = pynvml.nvmlDeviceGetHandleByIndex(0)
                    name = pynvml.nvmlDeviceGetName(self._gpu_handle)
                    if isinstance(name, bytes):
                        name = name.decode("utf-8", errors="ignore")
                    self._gpu_name = name
                    try:
                        self._gpu_power_limit = pynvml.nvmlDeviceGetEnforcedPowerLimit(self._gpu_handle) / 1000.0
                    except Exception:
                        self._gpu_power_limit = 0.0
                    self._nvml_initialized = True
            except Exception:
                self._nvml_initialized = False

        if not self._nvml_initialized:
            self._fallback_gpu_name = self._detect_fallback_gpu()

    def _probe_ping_once(self):
        """执行单次网络往返延迟探测 (Win32 ICMP 优先 + TCP 兜底 + EWMA 平滑滤波)"""
        try:
            # 1. 优先使用 Windows 原生 Win32 ICMP Echo API
            if _HAS_ICMP_API:
                icmp_targets = ['223.5.5.5', '119.29.29.29', '180.76.76.76', '1.1.1.1']
                handle = _iphlpapi.IcmpCreateFile()
                if handle:
                    try:
                        send_data = b'monitor_ping'
                        reply_size = ctypes.sizeof(ICMP_ECHO_REPLY) + len(send_data) + 128
                        reply_buf = ctypes.create_string_buffer(reply_size)

                        for ip_str in icmp_targets:
                            try:
                                ip_ulong = struct.unpack('<I', socket.inet_aton(ip_str))[0]
                                res = _iphlpapi.IcmpSendEcho(
                                    handle,
                                    ip_ulong,
                                    send_data,
                                    len(send_data),
                                    None,
                                    reply_buf,
                                    reply_size,
                                    800  # 800ms 超时
                                )
                                if res > 0:
                                    reply = ICMP_ECHO_REPLY.from_buffer(reply_buf)
                                    if reply.Status == 0:
                                        rtt = float(reply.RoundTripTime)
                                        # 广域网正常物理往返时延保底 1.0ms
                                        valid_rtt = max(1.0, rtt)
                                        if self._last_ping_ms > 0:
                                            self._last_ping_ms = round(0.7 * self._last_ping_ms + 0.3 * valid_rtt, 1)
                                        else:
                                            self._last_ping_ms = round(valid_rtt, 1)
                                        self._ping_fail_count = 0
                                        return
                            except Exception:
                                continue
                    finally:
                        _iphlpapi.IcmpCloseHandle(handle)

            # 2. 兜底策略：TCP 探测
            tcp_targets = [('223.5.5.5', 80), ('119.29.29.29', 80)]
            for host, port in tcp_targets:
                try:
                    t0 = time.perf_counter()
                    s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
                    s.settimeout(0.8)
                    s.connect((host, port))
                    ms = (time.perf_counter() - t0) * 1000.0
                    s.close()
                    if ms >= 2.0:
                        if self._last_ping_ms > 0:
                            self._last_ping_ms = round(0.7 * self._last_ping_ms + 0.3 * ms, 1)
                        else:
                            self._last_ping_ms = round(ms, 1)
                        self._ping_fail_count = 0
                        return
                except Exception:
                    continue

            # 连续 3 次探测全部失败时标记断网
            self._ping_fail_count += 1
            if self._ping_fail_count >= 3:
                self._last_ping_ms = -1.0
        except Exception:
            pass

    def _ping_worker_loop(self):
        """常驻轻量 Ping 守护线程 (零线程创建开销)"""
        while not self._stop_event.is_set():
            self._probe_ping_once()
            self._stop_event.wait(2.0)

    def set_detailed_mode(self, enabled: bool):
        self.detailed_mode = enabled

    def set_interval(self, interval: float):
        self.interval = max(0.2, interval)

    def stop(self):
        self.running = False
        self._stop_event.set()
        if hasattr(self, "_ping_thread") and self._ping_thread.is_alive():
            self._ping_thread.join(timeout=0.8)
        self._pdh_gpu.close()
        self.wait(2000)

    def run(self):
        while self.running:
            start_time = time.monotonic()
            data = MetricData(
                cpu_name=self._cpu_name,
                cpu_physical_cores=self._cpu_physical,
                cpu_logical_cores=self._cpu_logical
            )

            # 1. 采集 CPU (消除多核微秒级采样抖动)
            try:
                freq = psutil.cpu_freq()
                if freq:
                    data.cpu_freq_mhz = freq.current
                if self.detailed_mode:
                    cores = psutil.cpu_percent(interval=None, percpu=True)
                    data.cpu_cores = cores
                    data.cpu_percent = (sum(cores) / len(cores)) if cores else 0.0
                else:
                    data.cpu_percent = psutil.cpu_percent(interval=None)
            except Exception:
                pass

            # 2. 采集 物理内存 (RAM) & 已提交内存 (Commit Charge)
            try:
                vm = psutil.virtual_memory()
                data.ram_percent = vm.percent
                data.ram_used_gb = vm.used / (1024 ** 3)
                data.ram_total_gb = vm.total / (1024 ** 3)

                # Windows API: GlobalMemoryStatusEx (Commit Charge 虚拟内存)
                stat = MEMORYSTATUSEX()
                stat.dwLength = ctypes.sizeof(MEMORYSTATUSEX)
                ctypes.windll.kernel32.GlobalMemoryStatusEx(ctypes.byref(stat))
                data.ram_committed_gb = (stat.ullTotalPageFile - stat.ullAvailPageFile) / (1024 ** 3)
                data.ram_commit_total_gb = stat.ullTotalPageFile / (1024 ** 3)
                if data.ram_commit_total_gb > 0:
                    data.ram_commit_percent = (data.ram_committed_gb / data.ram_commit_total_gb) * 100.0
            except Exception:
                pass

            # 3. 采集 网络实时上下行速率
            now = time.monotonic()
            dt_net = max(0.001, now - self._last_net_time)
            try:
                net = psutil.net_io_counters()
                recv_delta = max(0, net.bytes_recv - self._last_bytes_recv)
                sent_delta = max(0, net.bytes_sent - self._last_bytes_sent)

                data.net_recv_speed = recv_delta / dt_net
                data.net_sent_speed = sent_delta / dt_net
                data.net_recv_str = format_speed(data.net_recv_speed)
                data.net_sent_str = format_speed(data.net_sent_speed)

                self._last_bytes_recv = net.bytes_recv
                self._last_bytes_sent = net.bytes_sent
                self._last_net_time = now
            except Exception:
                pass

            # 同步守护线程探测的 Ping 延迟
            data.net_ping_ms = self._last_ping_ms

            # 4. 采集 磁盘实时读写 I/O 速率
            dt_disk = max(0.001, now - self._last_disk_time)
            try:
                disk_io = psutil.disk_io_counters()
                if disk_io:
                    r_delta = max(0, disk_io.read_bytes - self._last_disk_read)
                    w_delta = max(0, disk_io.write_bytes - self._last_disk_write)
                    data.disk_read_speed = r_delta / dt_disk
                    data.disk_write_speed = w_delta / dt_disk
                    data.disk_read_str = format_speed(data.disk_read_speed)
                    data.disk_write_str = format_speed(data.disk_write_speed)
                    self._last_disk_read = disk_io.read_bytes
                    self._last_disk_write = disk_io.write_bytes
                self._last_disk_time = now
            except Exception:
                pass

            # 5. 采集 GPU (优先 NVIDIA NVML 深度遥测，次级使用 Windows PDH 性能计数器 Fallback)
            if self._nvml_initialized and self._gpu_handle:
                try:
                    data.gpu_available = True
                    data.gpu_name = self._gpu_name
                    data.gpu_power_limit_w = self._gpu_power_limit

                    # 核心利用率
                    util = pynvml.nvmlDeviceGetUtilizationRates(self._gpu_handle)
                    data.gpu_percent = float(util.gpu)

                    # 显卡核心频率与显存频率
                    try:
                        data.gpu_clock_core_mhz = pynvml.nvmlDeviceGetClockInfo(self._gpu_handle, pynvml.NVML_CLOCK_GRAPHICS)
                        data.gpu_clock_mem_mhz = pynvml.nvmlDeviceGetClockInfo(self._gpu_handle, pynvml.NVML_CLOCK_MEM)
                    except Exception:
                        pass

                    # 实时功耗 (Watts)
                    try:
                        data.gpu_power_w = pynvml.nvmlDeviceGetPowerUsage(self._gpu_handle) / 1000.0
                    except Exception:
                        pass

                    # P-State 档位
                    try:
                        pstate = pynvml.nvmlDeviceGetPerformanceState(self._gpu_handle)
                        data.gpu_pstate = f"P{pstate}"
                    except Exception:
                        pass

                    # 显存容量
                    mem = pynvml.nvmlDeviceGetMemoryInfo(self._gpu_handle)
                    data.gpu_mem_used_mb = mem.used / (1024 ** 2)
                    data.gpu_mem_total_mb = mem.total / (1024 ** 2)
                    data.gpu_mem_percent = (mem.used / mem.total) * 100.0 if mem.total > 0 else 0.0

                    # 核心温度
                    data.gpu_temp = int(pynvml.nvmlDeviceGetTemperature(self._gpu_handle, pynvml.NVML_TEMPERATURE_GPU))
                except Exception:
                    # NVML 句柄异常 (驱动重载/显卡进入休眠)，自动优雅降级
                    self._nvml_initialized = False

            if not self._nvml_initialized:
                # 使用 Windows PDH 性能计数器采样 GPU 3D 核心利用率 (兼容 AMD / Intel Arc / 核显)
                pdh_util = self._pdh_gpu.sample()
                data.gpu_percent = pdh_util
                if self._fallback_gpu_name or pdh_util > 0:
                    data.gpu_available = True
                    data.gpu_name = self._fallback_gpu_name or "Windows Generic GPU"

            # 6. 采集 电池状态
            try:
                bat = psutil.sensors_battery()
                if bat:
                    data.battery_percent = int(bat.percent)
                    data.battery_plugged = bool(bat.power_plugged)
            except Exception:
                pass

            # 6. 更新 60 秒历史循环队列
            self._hist_cpu.append(data.cpu_percent)
            self._hist_gpu.append(data.gpu_percent if data.gpu_available else 0.0)
            self._hist_ram.append(data.ram_percent)
            self._hist_power.append(data.gpu_power_w if data.gpu_available else 0.0)
            self._hist_net.append(data.net_recv_speed / 1024.0)  # KB/s

            data.history_cpu = list(self._hist_cpu)
            data.history_gpu = list(self._hist_gpu)
            data.history_ram = list(self._hist_ram)
            data.history_power = list(self._hist_power)
            data.history_net_down = list(self._hist_net)

            # 7. 详细模式扩展：分区容量与高占用进程排行 (智能节流采样，极致压缩开销)
            if self.detailed_mode:
                # 磁盘分区 (每 5 秒节流采样一次)
                if now - self._last_disk_sample_time >= 5.0 or not self._cached_disks:
                    try:
                        disks_info = []
                        for part in psutil.disk_partitions(all=False):
                            if os.name == 'nt' and ('cdrom' in part.opts or part.fstype == ''):
                                continue
                            try:
                                usage = psutil.disk_usage(part.mountpoint)
                                disks_info.append({
                                    'mount': part.mountpoint,
                                    'total_gb': usage.total / (1024 ** 3),
                                    'used_gb': usage.used / (1024 ** 3),
                                    'percent': usage.percent
                                })
                            except (PermissionError, OSError):
                                continue
                        self._cached_disks = disks_info
                        self._last_disk_sample_time = now
                    except Exception:
                        pass
                data.disks = self._cached_disks

                # 进程排行 Top 5 (每 2 秒节流采样一次，节省 80% CPU 占用)
                if now - self._last_proc_sample_time >= 2.0 or not self._cached_top_procs:
                    try:
                        procs = []
                        for p in psutil.process_iter(['pid', 'name', 'cpu_percent', 'memory_info']):
                            try:
                                info = p.info
                                pid = info['pid']
                                name = info['name']
                                if pid == 0 or not name or name == 'System Idle Process':
                                    continue
                                mem_mb = info['memory_info'].rss / (1024 ** 2) if info['memory_info'] else 0.0
                                cpu_p = info['cpu_percent'] or 0.0
                                procs.append({
                                    'pid': pid,
                                    'name': name,
                                    'cpu_percent': cpu_p,
                                    'mem_mb': mem_mb
                                })
                            except (psutil.NoSuchProcess, psutil.AccessDenied):
                                continue
                        procs.sort(key=lambda x: (x['cpu_percent'], x['mem_mb']), reverse=True)
                        self._cached_top_procs = procs[:5]
                        self._last_proc_sample_time = now
                    except Exception:
                        pass
                data.top_processes = self._cached_top_procs

            # 发射统一遥测数据
            self.metrics_updated.emit(data)

            # 动态节流休眠
            elapsed = time.monotonic() - start_time
            sleep_time = max(0.04, self.interval - elapsed)
            time.sleep(sleep_time)

        if self._nvml_initialized:
            try:
                pynvml.nvmlShutdown()
            except Exception:
                pass
