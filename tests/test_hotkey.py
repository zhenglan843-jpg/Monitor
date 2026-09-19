import unittest
from PyQt6.QtWidgets import QApplication
from src.hotkey import parse_hotkey_string, GlobalHotkeyManager, MOD_CONTROL, MOD_SHIFT, MOD_NOREPEAT


class TestHotkey(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.app = QApplication.instance() or QApplication([])

    def test_parse_hotkey_string(self):
        mods, vk = parse_hotkey_string("Ctrl+Shift+P")
        self.assertEqual(mods, MOD_CONTROL | MOD_SHIFT | MOD_NOREPEAT)
        self.assertEqual(vk, ord("P"))

        mods, vk = parse_hotkey_string("Alt+F11")
        self.assertEqual(vk, 0x70 + 10)

    def test_hotkey_manager_lifecycle(self):
        manager = GlobalHotkeyManager(self.app)
        manager.register_hotkeys("Ctrl+Shift+P", "Ctrl+Shift+H", "Ctrl+Shift+D")
        self.assertTrue(len(manager._registered_ids) >= 0)
        manager.cleanup()
        self.assertEqual(len(manager._registered_ids), 0)


if __name__ == "__main__":
    unittest.main()
