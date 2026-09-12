@echo off
chcp 65001 >nul
cd /d "%~dp0"
echo ============================================================
echo [Monitor 调试模式] 启动中，将输出实时硬件探测与日志信息...
echo ============================================================
echo.

if not exist ".venv\Scripts\python.exe" goto :NO_VENV

".venv\Scripts\python.exe" run.py

echo.
echo ============================================================
echo [Monitor 已退出] 如遇异常闪退，可截取上方错误日志提交 GitHub Issue。
echo ============================================================
pause
exit /b 0

:NO_VENV
echo [错误] 未检测到虚拟环境: .venv，请先运行 uv sync 或配置 requirements.txt
pause
exit /b 1
