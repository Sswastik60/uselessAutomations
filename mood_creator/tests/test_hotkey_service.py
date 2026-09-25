import pytest
import win32con
from PySide6.QtWidgets import QApplication, QMainWindow
from PySide6.QtCore import QTimer

from app.windows.hotkeys import parse_hotkey_string, HotkeyThread
from app.services.hotkey_service import HotkeyService
from app.ui.toast import ToastManager


@pytest.fixture(scope="module")
def qapp():
    app = QApplication.instance()
    if app is None:
        app = QApplication([])
    app.setQuitOnLastWindowClosed(False)
    yield app


def test_parse_hotkey_string():
    # Test valid key combinations
    mod, vk = parse_hotkey_string("CTRL+ALT+G")
    assert mod == (win32con.MOD_CONTROL | win32con.MOD_ALT)
    assert vk == ord("G")

    mod, vk = parse_hotkey_string("SHIFT+F5")
    assert mod == win32con.MOD_SHIFT
    assert vk == win32con.VK_F5

    mod, vk = parse_hotkey_string("WIN+ALT+1")
    assert mod == (win32con.MOD_WIN | win32con.MOD_ALT)
    assert vk == ord("1")

    # Test error cases
    with pytest.raises(ValueError):
        parse_hotkey_string("INVALID_KEY_COMBO")

    with pytest.raises(ValueError):
        parse_hotkey_string("CTRL+ALT")


def test_hotkey_service_registration_and_trigger(qapp):
    triggered_modes = []

    def on_mode_triggered(mode_id: str):
        triggered_modes.append(mode_id)

    service = HotkeyService(mode_trigger_callback=on_mode_triggered)

    # Register hotkey
    res = service.register_mode_hotkey("coding_mode", "CTRL+ALT+C")
    assert res is True
    assert service._mode_hotkeys.get("coding_mode") == "CTRL+ALT+C"
    assert service._hotkey_modes.get("CTRL+ALT+C") == "coding_mode"

    # Simulate triggering hotkey directly via service handler
    service._on_hotkey_pressed("CTRL+ALT+C")
    assert "coding_mode" in triggered_modes

    # Unregister hotkey
    service.unregister_mode_hotkey("coding_mode")
    assert "coding_mode" not in service._mode_hotkeys
    assert "CTRL+ALT+C" not in service._hotkey_modes

    service.stop()


def test_hotkey_detection_while_window_hidden_in_tray(qapp):
    """Verify hotkey dispatch is received and processed while the main window is hidden."""
    triggered_modes = []

    def on_mode_triggered(mode_id: str):
        triggered_modes.append(mode_id)

    service = HotkeyService(mode_trigger_callback=on_mode_triggered)
    service.register_mode_hotkey("guitar_mode", "CTRL+ALT+G")

    # Simulate main window being closed/hidden to system tray
    window = QMainWindow()
    window.show()
    qapp.processEvents()

    window.hide()
    qapp.processEvents()
    assert window.isVisible() is False

    # Simulate the hotkey signal dispatch
    service.hotkey_thread.signal_helper.hotkey_pressed.emit("CTRL+ALT+G")
    qapp.processEvents()

    assert "guitar_mode" in triggered_modes

    service.stop()
    window.close()


def test_toast_manager_with_hidden_parent(qapp):
    """Ensure toast notifications position correctly even if parent window is hidden."""
    win = QMainWindow()
    win.hide()

    toast = ToastManager.show_toast(win, "Mode executed in background", level="success")
    assert toast is not None
    assert toast.msg_lbl.text() == "Mode executed in background"
    assert toast.parent() is None  # Attached to screen, not hidden parent
    toast.close()
