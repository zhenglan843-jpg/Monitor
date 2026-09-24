import os
import sys
import json
import winreg
from dataclasses import dataclass, asdict, field
from typing import Optional, Dict, Any


CONFIG_DIR = os.path.join(os.environ.get("APPDATA", os.path.expanduser("~")), "Monitor")
CONFIG_FILE = os.path.join(CONFIG_DIR, "config.json")
RUN_REG_KEY = r"Software\Microsoft\Windows\CurrentVersion\Run"
APP_REG_NAME = "Monitor"


@dataclass
class AppConfig:
    hud_mode: str = "VERTICAL"          # VERTICAL, HORIZONTAL, MINI
    pos_x: Optional[int] = None
    pos_y: Optional[int] = None
    opacity: float = 0.92
    is_pinned: bool = True
    locked_position: bool = False
    click_through: bool = False
    sample_interval: float = 1.0        # 0.5, 1.0, 2.0
    auto_start: bool = False
    currency: str = "CNY"               # CNY / USD
    hud_scale: float = 1.0              # 0.8, 1.0, 1.2, 1.4
    auto_game_mode: bool = False        # 全屏应用/游戏自动穿透
    hotkeys_enabled: bool = True
    hotkey_click_through: str = "Ctrl+Shift+P"
    hotkey_toggle_hud: str = "Ctrl+Shift+H"
    hotkey_toggle_dashboard: str = "Ctrl+Shift+D"


class ConfigManager:
    """配置管理与注册表开机自启控制"""

    @staticmethod
    def get_config_path() -> str:
        return CONFIG_FILE

    @classmethod
    def load(cls) -> AppConfig:
        if not os.path.exists(CONFIG_FILE):
            cfg = AppConfig()
            cfg.auto_start = cls.is_auto_start_registered()
            return cfg

        try:
            with open(CONFIG_FILE, "r", encoding="utf-8") as f:
                data = json.load(f)
            cfg = AppConfig(
                hud_mode=data.get("hud_mode", "VERTICAL"),
                pos_x=data.get("pos_x"),
                pos_y=data.get("pos_y"),
                opacity=float(data.get("opacity", 0.92)),
                is_pinned=bool(data.get("is_pinned", True)),
                locked_position=bool(data.get("locked_position", False)),
                click_through=bool(data.get("click_through", False)),
                sample_interval=float(data.get("sample_interval", 1.0)),
                auto_start=bool(data.get("auto_start", False)),
                currency=data.get("currency", "CNY"),
                hud_scale=float(data.get("hud_scale", 1.0)),
                auto_game_mode=bool(data.get("auto_game_mode", False)),
                hotkeys_enabled=bool(data.get("hotkeys_enabled", True)),
                hotkey_click_through=data.get("hotkey_click_through", "Ctrl+Shift+P"),
                hotkey_toggle_hud=data.get("hotkey_toggle_hud", "Ctrl+Shift+H"),
                hotkey_toggle_dashboard=data.get("hotkey_toggle_dashboard", "Ctrl+Shift+D"),
            )
            # 校验并同步系统注册表自启状态
            reg_status = cls.is_auto_start_registered()
            cfg.auto_start = reg_status
            return cfg
        except Exception:
            return AppConfig()

    @classmethod
    def save(cls, cfg: AppConfig):
        try:
            os.makedirs(CONFIG_DIR, exist_ok=True)
            with open(CONFIG_FILE, "w", encoding="utf-8") as f:
                json.dump(asdict(cfg), f, indent=2, ensure_ascii=False)
        except Exception:
            pass

    @classmethod
    def is_auto_start_registered(cls) -> bool:
        """检查注册表中是否已写入 Monitor 开机自启项"""
        try:
            with winreg.OpenKey(winreg.HKEY_CURRENT_USER, RUN_REG_KEY, 0, winreg.KEY_READ) as key:
                val, _ = winreg.QueryValueEx(key, APP_REG_NAME)
                return bool(val)
        except (FileNotFoundError, OSError):
            return False

    @classmethod
    def set_auto_start(cls, enable: bool) -> bool:
        """开启或关闭 Windows 开机自启"""
        try:
            with winreg.OpenKey(winreg.HKEY_CURRENT_USER, RUN_REG_KEY, 0, winreg.KEY_SET_VALUE) as key:
                if enable:
                    # 获取当前可执行环境路径与启动脚本
                    proj_root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
                    run_py = os.path.join(proj_root, "run.py")

                    # 优先使用 .venv 中的 pythonw.exe 免控制台黑框运行
                    venv_pythonw = os.path.join(proj_root, ".venv", "Scripts", "pythonw.exe")
                    if os.path.exists(venv_pythonw):
                        cmd = f'"{venv_pythonw}" "{run_py}"'
                    else:
                        py_dir = os.path.dirname(sys.executable)
                        pythonw = os.path.join(py_dir, "pythonw.exe")
                        if os.path.exists(pythonw):
                            cmd = f'"{pythonw}" "{run_py}"'
                        else:
                            cmd = f'"{sys.executable}" "{run_py}"'

                    winreg.SetValueEx(key, APP_REG_NAME, 0, winreg.REG_SZ, cmd)
                    return True
                else:
                    try:
                        winreg.DeleteValue(key, APP_REG_NAME)
                    except FileNotFoundError:
                        pass
                    return True
        except Exception:
            return False
