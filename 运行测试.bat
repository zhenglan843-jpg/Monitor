@echo off
chcp 65001 >nul
cd /d "%~dp0"
echo ============================================================
echo [Monitor] 正在执行全套单元测试套件...
echo ============================================================
echo.

if not exist ".venv\Scripts\python.exe" (
    echo [错误] 未检测到虚拟环境 (.venv)，请先完成环境配置。
    pause
    exit /b 1
)

".venv\Scripts\python.exe" -m unittest discover -v -s tests -p "test_*.py"

echo.
echo ============================================================
echo [测试执行完毕]
echo ============================================================
pause
