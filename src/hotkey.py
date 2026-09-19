import sys
import ctypes
from ctypes import wintypes
from typing import Dict, Tuple, Optional
from PyQt6.QtCore import QObject, pyqtSignal, QAbstractNativeEventFilter
from PyQt6.QtWidgets import QWidget, QApplication


MOD_ALT = 0x0001
MOD_CONTROL = 0x0002
MOD_SHIFT = 0x0004
MOD_WIN = 0x0008
MOD_NOREPEAT = 0x4000
WM_HOTKEY = 0x0312

# 快捷键 ID
HOTKEY_ID_CLICK_THROUGH = 1001
HOTKEY_ID_TOGGLE_HUD = 1002
HOTKEY_ID_TOGGLE_DASHBOARD = 1003


def parse_hotkey_string(key_str: str) -> Tuple[int, int]:
    """
    解析快捷键字符串 (如 'Ctrl+Shift+P' 或 'Alt+F11')
    返回 (modifiers, vk_code)
    """
    parts = [p.strip().upper() for p in key_str.split("+") if p.strip()]
    modifiers = MOD_NOREPEAT
    vk = 0

    for p in parts:
        if p in ("CTRL", "CONTROL"):
            modifiers |= MOD_CONTROL
        elif p == "SHIFT":
            modifiers |= MOD_SHIFT
        elif p == "ALT":
            modifiers |= MOD_ALT
        elif p in ("WIN", "WINDOWS", "SUPER"):
            modifiers |= MOD_WIN
        elif len(p) == 1 and ("A" <= p <= "Z" or "0" <= p <= "9"):
            vk = ord(p)
        elif p.startswith("F") and p[1:].isdigit():
            fn = int(p[1:])
            if 1 <= fn <= 24:
                vk = 0x70 + (fn - 1)
        elif p == "SPACE":
            vk = 0x20
        elif p == "TAB":
            vk = 0x09
        elif p == "ESC" or p == "ESCAPE":
            vk = 0x1B

    return modifiers, vk


class _NativeHotkeyFilter(QAbstractNativeEventFilter):
    """底层 Windows 消息过滤器，捕获 WM_HOTKEY 消息"""
    def __init__(self, dispatcher):
        super().__init__()
        self._dispatcher = dispatcher

    def nativeEventFilter(self, eventType, message):
        try:
            msg = wintypes.MSG.from_address(message.__int__())
            if msg.message == WM_HOTKEY:
                self._dispatcher._handle_hotkey(msg.wParam)
                return True, 0
        except Exception:
            pass
        return False, 0


class GlobalHotkeyManager(QObject):
    """
    Windows 原生全局快捷键管理器
    - 基于 Win32 API RegisterHotKey / UnregisterHotKey
    - 纯原生免第三方重型依赖，极低开销，毫秒级响应
    """
    hotkey_click_through = pyqtSignal()
    hotkey_toggle_hud = pyqtSignal()
    hotkey_toggle_dashboard = pyqtSignal()

    def __init__(self, app: QApplication, parent=None):
        super().__init__(parent)
        self.app = app
        self._registered_ids: Dict[int, Tuple[int, int]] = {}
        self._filter = _NativeHotkeyFilter(self)
        self._helper_widget = QWidget()
        self._helper_widget.setWindowFlags(self._helper_widget.windowFlags() | 0x00000001)  # Popup/Tool
        self._hwnd = int(self._helper_widget.winId())

        self.app.installNativeEventFilter(self._filter)

    def register_hotkeys(
        self,
        key_click_through: str = "Ctrl+Shift+P",
        key_toggle_hud: str = "Ctrl+Shift+H",
        key_toggle_dash: str = "Ctrl+Shift+D"
    ):
        """批量注册全局快捷键"""
        self.unregister_all()

        configs = [
            (HOTKEY_ID_CLICK_THROUGH, key_click_through),
            (HOTKEY_ID_TOGGLE_HUD, key_toggle_hud),
            (HOTKEY_ID_TOGGLE_DASHBOARD, key_toggle_dash)
        ]

        for hid, key_str in configs:
            mods, vk = parse_hotkey_string(key_str)
            if vk != 0:
                res = ctypes.windll.user32.RegisterHotKey(self._hwnd, hid, mods, vk)
                if res:
                    self._registered_ids[hid] = (mods, vk)

    def _handle_hotkey(self, hotkey_id: int):
        if hotkey_id == HOTKEY_ID_CLICK_THROUGH:
            self.hotkey_click_through.emit()
        elif hotkey_id == HOTKEY_ID_TOGGLE_HUD:
            self.hotkey_toggle_hud.emit()
        elif hotkey_id == HOTKEY_ID_TOGGLE_DASHBOARD:
            self.hotkey_toggle_dashboard.emit()

    def unregister_all(self):
        """释放所有注册的全局热键"""
        for hid in list(self._registered_ids.keys()):
            try:
                ctypes.windll.user32.UnregisterHotKey(self._hwnd, hid)
            except Exception:
                pass
        self._registered_ids.clear()

    def cleanup(self):
        self.unregister_all()
        try:
            self.app.removeNativeEventFilter(self._filter)
        except Exception:
            pass
        self._helper_widget.deleteLater()
