import sys
import os
import unittest
import ctypes
import ctypes.wintypes
import psutil

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

if sys.stdout and hasattr(sys.stdout, "reconfigure"):
    try:
        sys.stdout.reconfigure(encoding="utf-8")
    except Exception:
        pass


def get_foreground_info():
    user32 = ctypes.windll.user32
    hwnd = user32.GetForegroundWindow()
    pid = ctypes.wintypes.DWORD()
    user32.GetWindowThreadProcessId(hwnd, ctypes.byref(pid))
    length = user32.GetWindowTextLengthW(hwnd)
    buff = ctypes.create_unicode_buffer(length + 1)
    user32.GetWindowTextW(hwnd, buff, length + 1)
    p_name = ""
    try:
        p_name = psutil.Process(pid.value).name()
    except Exception:
        pass
    return hwnd, buff.value, pid.value, p_name


class TestForeground(unittest.TestCase):
    def test_get_foreground_info(self):
        hwnd, title, pid, name = get_foreground_info()
        self.assertIsInstance(hwnd, int)
        self.assertIsInstance(title, str)
        self.assertIsInstance(pid, int)
        self.assertIsInstance(name, str)


if __name__ == "__main__":
    unittest.main()
