import ctypes
import logging
import time
from typing import List, Optional, Tuple

import win32con
import win32gui
import win32process

logger = logging.getLogger(__name__)


class WindowManager:
    """Windows OS top-level window finder and control manager."""

    @staticmethod
    def get_all_visible_windows() -> List[Tuple[int, str]]:
        """Return list of (hwnd, window_title) for visible top-level windows."""
        results: List[Tuple[int, str]] = []

        def enum_win_proc(hwnd, _):
            if win32gui.IsWindowVisible(hwnd):
                title = win32gui.GetWindowText(hwnd).strip()
                if title:
                    results.append((hwnd, title))
            return True

        win32gui.EnumWindows(enum_win_proc, None)
        return results

    @staticmethod
    def find_window(title_substring: str) -> Optional[int]:
        """Search for a top-level window matching title_substring (case-insensitive)."""
        target = title_substring.lower()
        for hwnd, title in WindowManager.get_all_visible_windows():
            if target in title.lower():
                return hwnd
        return None

    @staticmethod
    def focus_window(hwnd_or_title: int | str) -> bool:
        """Bring window to foreground and set focus."""
        hwnd = WindowManager._resolve_hwnd(hwnd_or_title)
        if not hwnd or not win32gui.IsWindow(hwnd):
            logger.warning(f"Cannot focus invalid window handle: {hwnd_or_title}")
            return False

        try:
            # Restore if minimized
            if win32gui.IsIconic(hwnd):
                win32gui.ShowWindow(hwnd, win32con.SW_RESTORE)

            # Bring to front
            win32gui.ShowWindow(hwnd, win32con.SW_SHOW)
            
            # Attach thread input to bypass Windows SetForegroundWindow restrictions
            fore_hwnd = win32gui.GetForegroundWindow()
            if fore_hwnd != hwnd:
                fore_thread = win32process.GetWindowThreadProcessId(fore_hwnd)[0]
                app_thread = win32api_get_current_thread_id()
                
                if fore_thread != app_thread:
                    ctypes.windll.user32.AttachThreadInput(fore_thread, app_thread, True)
                    win32gui.SetForegroundWindow(hwnd)
                    ctypes.windll.user32.AttachThreadInput(fore_thread, app_thread, False)
                else:
                    win32gui.SetForegroundWindow(hwnd)
            return True
        except Exception as e:
            logger.error(f"Error focusing window {hwnd_or_title}: {e}")
            try:
                win32gui.SetForegroundWindow(hwnd)
                return True
            except Exception:
                return False

    @staticmethod
    def minimize_window(hwnd_or_title: int | str) -> bool:
        """Minimize window."""
        hwnd = WindowManager._resolve_hwnd(hwnd_or_title)
        if hwnd and win32gui.IsWindow(hwnd):
            win32gui.ShowWindow(hwnd, win32con.SW_MINIMIZE)
            return True
        return False

    @staticmethod
    def maximize_window(hwnd_or_title: int | str) -> bool:
        """Maximize window."""
        hwnd = WindowManager._resolve_hwnd(hwnd_or_title)
        if hwnd and win32gui.IsWindow(hwnd):
            win32gui.ShowWindow(hwnd, win32con.SW_MAXIMIZE)
            return True
        return False

    @staticmethod
    def move_resize_window(hwnd_or_title: int | str, x: int, y: int, width: int, height: int) -> bool:
        """Reposition and resize window."""
        hwnd = WindowManager._resolve_hwnd(hwnd_or_title)
        if hwnd and win32gui.IsWindow(hwnd):
            win32gui.MoveWindow(hwnd, x, y, width, height, True)
            return True
        return False

    @staticmethod
    def wait_for_window(title_substring: str, timeout: float = 30.0, poll_interval: float = 0.5) -> Optional[int]:
        """Poll until a matching window title appears."""
        start = time.time()
        while time.time() - start < timeout:
            hwnd = WindowManager.find_window(title_substring)
            if hwnd:
                return hwnd
            time.sleep(poll_interval)
        return None

    @staticmethod
    def _resolve_hwnd(hwnd_or_title: int | str) -> Optional[int]:
        """Resolve HWND from integer or title substring."""
        if isinstance(hwnd_or_title, int):
            return hwnd_or_title
        return WindowManager.find_window(str(hwnd_or_title))


def win32api_get_current_thread_id() -> int:
    return ctypes.windll.kernel32.GetCurrentThreadId()
