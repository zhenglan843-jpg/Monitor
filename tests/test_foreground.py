import ctypes
import ctypes.wintypes
import psutil

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

if __name__ == "__main__":
    h, title, p, name = get_foreground_info()
    print(f"Foreground: '{title}' | PID: {p} | Name: {name}")
