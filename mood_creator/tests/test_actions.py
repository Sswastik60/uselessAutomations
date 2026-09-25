import os
import pytest
from app.actions.filesystem import CreateDirectoryAction, CheckFileExistsAction
from app.actions.wait import WaitDurationAction
from app.actions.conditional import EnvVarExistsConditionAction
from app.core.execution_context import AutomationContext


def test_wait_duration_action():
    ctx = AutomationContext("test", "Test Mode")
    act = WaitDurationAction(seconds=0.1)
    res = act.execute(ctx)
    assert res.success is True


def test_filesystem_actions(tmp_path):
    ctx = AutomationContext("test", "Test Mode")
    target_dir = str(tmp_path / "new_folder")

    # Create dir
    act_create = CreateDirectoryAction(directory_path=target_dir)
    res_create = act_create.execute(ctx)
    assert res_create.success is True
    assert os.path.exists(target_dir)

    # Check exists
    act_chk = CheckFileExistsAction(path=target_dir)
    res_chk = act_chk.execute(ctx)
    assert res_chk.success is True


def test_env_var_condition_action():
    ctx = AutomationContext("test", "Test Mode")
    act = EnvVarExistsConditionAction(variable_name="PATH")
    res = act.execute(ctx)
    assert res.success is True
    assert res.data["condition_met"] is True


def test_process_manager_shortcut_resolution():
    from app.windows.processes import ProcessManager
    # Test resolving existing shortcut if available
    dedicated_lnk = "DEDICATED_MODES/Game_mode/Steam.lnk"
    if os.path.exists(dedicated_lnk):
        target = ProcessManager.resolve_shortcut(dedicated_lnk)
        assert target is not None
        assert "Steam.exe" in target or os.path.exists(target)


def test_auto_discover_app_path():
    from app.windows.processes import ProcessManager
    # Test that auto_discover_app_path runs without NameError or unhandled exception
    res_steam = ProcessManager.auto_discover_app_path("steam")
    res_discord = ProcessManager.auto_discover_app_path("discord")
    res_code = ProcessManager.auto_discover_app_path("code")
    # At least one should be found on the dev machine
    assert res_steam is not None or res_discord is not None or res_code is not None


def test_launch_process_context_and_arguments():
    from app.actions.process import LaunchProcessAction
    from unittest.mock import patch, MagicMock

    ctx = AutomationContext("test_launch", "Test Launch")
    mock_proc = MagicMock()
    mock_proc.pid = 12345

    with patch("app.windows.processes.ProcessManager.launch_process", return_value=mock_proc) as mock_launch:
        with patch("os.path.exists", return_value=True):
            act = LaunchProcessAction(application="notepad.exe", arguments="--test arg2")
            res = act.execute(ctx)
            assert res.success is True
            assert ctx.get_variable("last_launched_pid") == 12345
            assert ctx.get_variable("last_launched_name") == "notepad.exe"
            # Verify string arguments were split correctly
            mock_launch.assert_called_once_with("notepad.exe", ["--test", "arg2"], None)


def test_window_manager_find_and_maximize(monkeypatch):
    from app.windows.windows import WindowManager
    from app.actions.windows import MaximizeWindowAction

    ctx = AutomationContext("test_win", "Test Window")
    ctx.set_variable("last_launched_name", "notepad.exe")
    ctx.set_variable("last_launched_pid", 9999)

    # Mock visible windows
    fake_windows = [
        (1001, "Chrome - Google", "chrome.exe"),
        (2002, "Untitled - Notepad", "Notepad.exe"),
    ]
    monkeypatch.setattr(WindowManager, "get_all_visible_windows", lambda: fake_windows)

    # 1. Match by process name without .exe
    hwnd1 = WindowManager.find_window("notepad")
    assert hwnd1 == 2002

    # 2. Match by window title
    hwnd2 = WindowManager.find_window("Untitled")
    assert hwnd2 == 2002

    # 3. Match by context variable when title is blank
    hwnd3 = WindowManager.find_window("", context=ctx)
    assert hwnd3 == 2002

    # 4. Test MaximizeWindowAction with mocked Win32 calls
    monkeypatch.setattr("win32gui.IsWindow", lambda h: True)
    monkeypatch.setattr("win32gui.IsIconic", lambda h: False)
    monkeypatch.setattr("win32gui.ShowWindow", lambda h, cmd: None)
    monkeypatch.setattr("win32gui.SetForegroundWindow", lambda h: None)
    monkeypatch.setattr("ctypes.windll.user32.ShowWindowAsync", lambda h, cmd: 1)

    max_act = MaximizeWindowAction(title="")
    res = max_act.execute(ctx)
    assert res.success is True
    assert "Maximized" in res.message


def test_trigger_hotkey_action_modifiers(monkeypatch):
    from app.actions.keyboard import TriggerHotkeyAction
    import win32con

    ctx = AutomationContext("test_hotkey", "Test Hotkey")
    events = []

    def mock_keybd(vk, scan, flags, extra):
        events.append((vk, flags))

    monkeypatch.setattr("win32api.keybd_event", mock_keybd)
    monkeypatch.setattr("time.sleep", lambda s: None)

    act = TriggerHotkeyAction(hotkey="WIN+D")
    res = act.execute(ctx)
    assert res.success is True
    # Verify VK_LWIN was pressed
    pressed_vks = [e[0] for e in events]
    assert win32con.VK_LWIN in pressed_vks


def test_press_key_f11_with_window_and_scan_code(monkeypatch):
    from app.actions.keyboard import PressKeyAction
    from app.windows.windows import WindowManager
    import win32con

    ctx = AutomationContext("test_f11", "Test F11")
    focused = []
    events = []

    monkeypatch.setattr(WindowManager, "focus_window", lambda win, timeout=5.0, context=None: focused.append(win) or True)
    monkeypatch.setattr("win32api.keybd_event", lambda vk, scan, flags, extra: events.append((vk, scan, flags)))
    monkeypatch.setattr("time.sleep", lambda s: None)

    act = PressKeyAction(key="F11", window="Brave", delay_before=0.0)
    res = act.execute(ctx)
    assert res.success is True
    assert "Pressed key 'F11'" in res.message
    assert "Brave" in focused
    # Check that events were generated with scan code
    assert len(events) == 2
    assert events[0][0] == win32con.VK_F11
    assert events[0][1] != 0  # hardware scan code must not be 0


def test_toggle_fullscreen_action(monkeypatch):
    from app.actions.windows import ToggleFullscreenAction
    from app.windows.windows import WindowManager
    import win32con

    ctx = AutomationContext("test_fs", "Test Fullscreen")
    events = []

    monkeypatch.setattr(WindowManager, "focus_window", lambda win, timeout=5.0, context=None: True)
    monkeypatch.setattr("win32api.keybd_event", lambda vk, scan, flags, extra: events.append((vk, scan, flags)))
    monkeypatch.setattr("time.sleep", lambda s: None)

    act = ToggleFullscreenAction(title="Brave", key="F11", delay_before=0.0)
    res = act.execute(ctx)
    assert res.success is True
    assert "Toggled fullscreen" in res.message
    assert any(e[0] == win32con.VK_F11 for e in events)


def test_open_url_action(monkeypatch):
    from app.actions.browser import OpenUrlAction
    from app.windows.processes import ProcessManager
    from unittest.mock import patch, MagicMock

    ctx = AutomationContext("test_url", "Test URL")
    mock_proc = MagicMock()
    mock_proc.pid = 9876

    with patch("app.windows.processes.ProcessManager.launch_process", return_value=mock_proc) as mock_launch:
        with patch("app.windows.processes.ProcessManager.auto_discover_app_path", return_value=r"C:\Program Files\BraveSoftware\Brave-Browser\Application\brave.exe"):
            with patch("os.path.exists", return_value=True):
                act = OpenUrlAction(url="https://youtube.com", browser="brave", fullscreen=False)
                res = act.execute(ctx)
                assert res.success is True
                assert "Opened website" in res.message
                assert ctx.get_variable("last_launched_pid") == 9876
                mock_launch.assert_called_once()




