@echo off
chcp 65001 >nul
cd /d "%~dp0"

if not exist ".venv\Scripts\pythonw.exe" (
    echo ============================================================
    echo [提示] 未检测到 Monitor Python 虚拟环境 (.venv)！
    echo ============================================================
    echo 首次运行请先完成依赖安装，任选以下一种方式：
    echo.
    echo 1. 使用 uv 快速初始化 (推荐):
    echo    uv sync
    echo.
    echo 2. 使用传统 pip 初始化:
    echo    python -m venv .venv
    echo    .venv\Scripts\pip.exe install -r requirements.txt
    echo ============================================================
    echo.
    pause
    exit /b 1
)

start "" ".venv\Scripts\pythonw.exe" run.py
exit
