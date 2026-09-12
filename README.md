# Monitor (专业级 Windows 硬件与 AI 性能监控中枢)

<div align="center">

[![Python](https://img.shields.io/badge/Python-3.11%20%7C%203.12-blue.svg?logo=python&logoColor=white)](https://www.python.org/)
[![Platform](https://img.shields.io/badge/Platform-Windows%2010%20%7C%2011-0078D6.svg?logo=windows&logoColor=white)](https://www.microsoft.com/windows)
[![GUI](https://img.shields.io/badge/GUI-PyQt6-41CD52.svg?logo=qt&logoColor=white)](https://www.riverbankcomputing.com/software/pyqt/)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](LICENSE)
[![CI](https://img.shields.io/badge/CI-Passing-brightgreen.svg?logo=githubactions&logoColor=white)](https://github.com/ck554/Monitor/actions)

**融合 MSI Afterburner (微星小飞机) 与 NVIDIA App (GeForce Experience Overlay) 精髓，原生支持 Google Antigravity AI Agent 深度遥测的高性能、低开销 Windows 监控软件。**

[🌟 核心特性](#-核心特性) • [🖼️ 界面预览](#️-界面预览) • [🚀 快速开始](#-快速开始) • [🎮 交互指南](#-交互指南) • [🛠️ 故障排查与反馈](#️-故障排查与反馈) • [📄 开源协议](#-开源协议)

</div>

---

## 🖼️ 界面预览

### 1. 三种游戏级 HUD 悬浮形态 (实时 FPS · 1% Low · 动态波形 · AI 上下文)

| 横向流线型胶囊栏 (Horizontal Pill) | 垂直游戏侧边栏 (Vertical Sidebar) | 极简微型徽章 (Mini Badge) |
| :---: | :---: | :---: |
| ![横向胶囊栏](assets/screenshots/hud_horizontal.png) | ![垂直侧边栏](assets/screenshots/hud_vertical.png) | ![极简微型徽章](assets/screenshots/hud_mini.png) |

### 2. 专业性能中枢仪表盘 (Pro Hub 2.0)

| 📈 60 秒平滑波形走势图 (Curves) | 💻 CPU 核心拓扑与 GPU 功耗墙 (Hardware) |
| :---: | :---: |
| ![性能曲线走势](assets/screenshots/dashboard_curves.png) | ![硬件全景与核心矩阵](assets/screenshots/dashboard_hardware.png) |

| 🤖 Google Antigravity AI Agent 深度遥测中枢 | ⚡ 进程占用与系统工具 (Processes) |
| :---: | :---: |
| ![Antigravity AI 遥测面板](assets/screenshots/dashboard_antigravity.png) | ![进程列表与内存优化](assets/screenshots/dashboard_processes.png) |

---

## 🌟 核心特性

### 1. 媲美 MSI Afterburner & NVIDIA App 的深度硬件遥测
* **GPU (NVIDIA NVML 驱动级直接遥测)**：
  * **动态核心频率与显存频率 (MHz)**：毫秒级掌握显卡加速睿频；
  * **实时功耗与功耗墙 (Power Draw W / TDP Limit W)**：动态监测显卡是否触及功耗墙上限；
  * **核心利用率与显存容量占用**；
  * **GPU 核心温度** 与 **P-State 性能档位** (P0 满血 3D ~ P8 节能待机)。
* **CPU (处理器全景与核心矩阵)**：
  * 自动读取完整官方型号（如 `Intel(R) Core(TM) Ultra 5 125H`）；
  * **18 线程独立热力图矩阵**：直观分辨大核 (P-Core) 与小核 (E-Core) 负载差异，一目了然定位游戏单核瓶颈；
  * 动态运行主频与核心占用。
* **RAM 物理内存 & 虚拟内存 (Commit Charge)**：
  * 引入 MSI Afterburner 经典已提交内存监控，提前防范游戏爆虚拟内存崩溃。
* **3D 游戏渲染帧率与 1% Low 掉帧遥测 (RTSS 微秒级直读通道)**：
  * **零开销微秒级直读 (< 0.01ms)**：非侵入式对接 RivaTuner Statistics Server (RTSS / MSI Afterburner 核心) 共享内存，无需管理员权限（避开 PresentMon 内核跟踪需要管理员权限的限制），全面兼容 DirectX 9/11/12、Vulkan、OpenGL 等所有 3D 游戏引擎；
  * **标准 1% Low / 0.1% Low 掉帧算法**：严格依照 Digital Foundry / CapFrameX 基准标准，直接从 1024 槽环形微秒缓冲区提取计算长尾卡顿点（1000.0 / t_p99），即使平均帧率很高也能精准揪出瞬间微卡顿和掉帧；
  * **无感待机与自愈**：未运行 3D 游戏或未开启 RTSS 时优雅显示 `--`，零额外 CPU 开销。
* **游戏网络往返延迟 (Ping) 与实时上下行**：
  * 极轻量 Socket 握手延迟探测（绿/黄/红三色毫秒指标），媲美 NVIDIA Overlay 的 Network Latency。
* **磁盘读写 I/O 速率**：
  * 实时读取/写入吞吐 (MB/s)，快速排查磁盘加载瓶颈。

---

### 2. 界面显示设计：游戏级 HUD 与专业中枢
* **3 种 HUD 悬浮形态，一键快捷切换**：
  1. **垂直侧边 HUD (Vertical Sidebar)**：经典游戏侧边栏风格，紧凑贴靠屏幕边缘，顶部优先呈现游戏帧率与 1% Low；
  2. **横向流线型胶囊栏 (Horizontal Pill)**：全景旗舰形态，紧凑排布 `124·88L` 实时帧率与 1% Low 标识，内置 CPU 实时微型动态波形折线 (Sparkline)；
  3. **极简微型徽章 (Mini Badge)**：极简极客模式，紧凑呈现即时高优先级 FPS，桌面占用极小。
* **🖱️ 鼠标穿透模式 (Click-Through)**：
  * 专为游戏玩家定制！开启后，鼠标点击完全穿透悬浮条直接操作背景游戏/软件，HUD 常驻屏幕但绝不干扰射击与点击操作！
* **📈 60 秒实时波形走势图 (Performance Curves)**：
  * 原生 `QPainter` 平滑绘制 60 秒 CPU/GPU 利用率、显卡功耗、游戏渲染帧率 (FPS) 与网络流量走势，实时标注 Min / Avg / Max 极值。
* **🧹 内存一键优化整理**：
  * 调用 Windows API 释放冗余进程工作集缓存。
* **零抖动、零毛边抗锯齿**：
  * Cascadia Code 等宽数字、定宽右对齐布局，彻底解决百分号跳动与 Windows 半透明文字毛边。

---

### 3. 🤖 Google Antigravity AI Agent 深度遥测中枢
* **对话上下文容量与健康水位 (Context Usage & Health)**：
  * 实时监控当前活跃会话持有的实际上下文 Tokens 总量（如 `64.6k / 1,048,576 Tokens`）；
  * 渐变彩色主进度条根据利用率自动变色（安全天青蓝 / 预警琥珀黄 / 告警珊瑚红），提前防范上下文过载导致的模型性能劣化。
* **Token 细分构成精确拆解**：
  * 直观呈现：👤 用户输入、🤖 AI代码与回答、💭 深度思考推理 (Thinking)、⚙️ 工具命令与执行返回 (Tool Results) 以及底层系统基底各自的消耗量与占比。
* **实时单轮增量与历史累计用量**：
  * 实时捕捉上一轮请求的输入与输出增量（`In: +61 | Out: +127`）；
  * 汇总统计今日全天消耗 Token 与全量历史会话消耗总量；
  * 根据 Gemini 模型费率实时估算折算成本（美元/人民币）。
* **HUD 悬浮条与托盘深度集成**：
  * **AI 上下文容量**：横向胶囊栏与微型徽章显示当前活跃会话持有的上下文 Tokens（如 `AI 185.5k` / `17.5%`）；
  * **Token 消耗统计 (当日/总计)**：横向胶囊栏与微型徽章新增 `TOK: 今日/总和` 紧凑微组件（如 `TOK 774k/1.88M`）；
  * **悬停浮窗 (Tooltip)**：浮现今日与总和的折算成本估算（$ / ¥）、历史会话总数与单轮增量详细指标。
* **历史会话漫游浏览器**：
  * 仪表盘中表格列出最近对话列表、估算消耗与最后活跃时间，支持一键定位会话日志。

---

## 🚀 快速开始

### 运行环境要求
* **操作系统**：Windows 10 / Windows 11 (64 位)
* **Python**：Python 3.11 或 3.12
* **显卡支持**：全功能支持 NVIDIA 独立显卡（非 NVIDIA 显卡将自动隐藏显存/功耗指标，CPU与系统指标仍全功能正常工作）
* **游戏帧率监控（可选）**：推荐后台运行 [RivaTuner Statistics Server (RTSS)](https://www.guru3d.com/download/rtss-rivatuner-statistics-server-download/) 或 MSI Afterburner

### 1. 克隆本仓库
```bash
git clone https://github.com/ck554/Monitor.git
cd Monitor
```

### 2. 安装运行依赖（任选一种）

#### 选项 A: 使用 uv (极速推荐 ⚡)
```powershell
# 自动创建虚拟环境并同步安装所有依赖
uv sync
```

#### 选项 B: 使用标准 Python + pip
```powershell
# 创建虚拟环境
python -m venv .venv

# 激活虚拟环境并安装依赖
.\.venv\Scripts\pip.exe install -r requirements.txt
```

### 3. 启动运行

* **便捷双击启动**：
  * 正常静默运行：直接双击根目录下的 **`启动Monitor.bat`**（后台静默运行，免黑色终端窗口）。
  * 调试运行：双击 **`调试启动.bat`**（保留控制台日志，方便查看硬件初始化输出）。
* **命令行启动**：
  ```powershell
  # 方式一：使用 uv
  uv run monitor

  # 方式二：直接通过虚拟环境 Python 运行
  .\.venv\Scripts\python.exe run.py
  ```

---

## 🎮 交互指南

| 操作 | 响应动作 |
| :--- | :--- |
| **鼠标左键拖动** | 自由拖曳悬浮窗，靠近屏幕四周 15px 自动磁吸贴边 |
| **鼠标双击悬浮窗** | 快速展开 / 收起专业性能中枢仪表盘 |
| **右键悬浮窗 / 托盘图标** | 切换 3 种 HUD 布局、切换鼠标穿透、锁定位置、调节透明度、退出 |
| **仪表盘选项卡切换** | 在「📈 性能曲线」、「💻 硬件全景」、「⚡ 进程与设置」、「🤖 Antigravity AI」间无缝切换 |
| **整理内存按钮** | 一键调用 Windows 底层工作集释放 API 优化内存 |

---

## 🧪 自动化测试

项目内置完整的单元测试套件（覆盖 RTSS 微秒级 1% Low 掉帧算法、NVML 驱动遥测、Antigravity Token 估算与模型计价等）：

* **一键运行测试**：双击根目录下的 **`运行测试.bat`**
* **命令行执行**：
  ```powershell
  .\.venv\Scripts\python.exe -m unittest discover -v -s tests -p "test_*.py"
  ```

---

## 🛠️ 故障排查与反馈

如果您在使用过程中遇到任何问题（例如显卡数据未识别、帧率未显示等）：

1. 双击运行 **`调试启动.bat`**，查看控制台输出的详细初始化日志；
2. 欢迎在 GitHub 提交 [Issues](https://github.com/ck554/Monitor/issues)，并附上控制台报错截图；
3. 如果您有新的功能需求或优化建议，欢迎发起 Pull Request 或在 Discussions 中畅所欲言！

---

## 📄 开源协议

本项目采用 [MIT License](LICENSE) 开源许可证。
Copyright (c) 2026 ck554
