import ctypes
import logging
import time
from typing import List, Optional, Tuple, TYPE_CHECKING

import psutil
import win32con
import win32gui
import win32process

if TYPE_CHECKING:
    from app.core.execution_context import AutomationContext

logger = logging.getLogger(__name__)


def ensure_desktop() -> None:
    """Ensure current thread is attached to the active user desktop window station."""
    try:
        hdesk = ctypes.windll.user32.OpenInputDesktop(0, False, 0x01FF)
        if hdesk:
            ctypes.windll.user32.SetThreadDesktop(hdesk)
    except Exception:
        pass


def win32api_get_current_thread_id() -> int:
    return ctypes.windll.kernel32.GetCurrentThreadId()


class WindowManager:
    """Windows OS top-level window finder, inspector, and control manager."""

    @staticmethod
    def get_all_visible_windows() -> List[Tuple[int, str, str]]:
        """
        Return list of (hwnd, window_title, process_name) for visible top-level windows.
        """
        ensure_desktop()
        hwnds: List[int] = []
        # 1. Try EnumDesktopWindows on input desktop first
        try:
            hdesk = ctypes.windll.user32.OpenInputDesktop(0, False, 0x01FF)
            if hdesk:
                from ctypes import wintypes
                WNDENUMPROC = ctypes.WINFUNCTYPE(wintypes.BOOL, wintypes.HWND, wintypes.LPARAM)

                def cb(h, _):
                    try:
                        if win32gui.IsWindowVisible(h):
                            hwnds.append(h)
                    except Exception:
                        pass
                    return True

                proc = WNDENUMPROC(cb)
                ctypes.windll.user32.EnumDesktopWindows(hdesk, proc, 0)
                ctypes.windll.user32.CloseDesktop(hdesk)
        except Exception as e:
            logger.debug(f"EnumDesktopWindows notice: {e}")

        # 2. Fallback to EnumWindows if empty
        if not hwnds:
            def enum_win_proc(hwnd, _):
                try:
                    if win32gui.IsWindowVisible(hwnd):
                        hwnds.append(hwnd)
                except Exception:
                    pass
                return True

            ctypes.windll.kernel32.SetLastError(0)
            try:
                win32gui.EnumWindows(enum_win_proc, None)
            except Exception as e:
                logger.debug(f"EnumWindows notice: {e}")

        results: List[Tuple[int, str, str]] = []
        for hwnd in hwnds:
            try:
                title = win32gui.GetWindowText(hwnd).strip()
                pname = ""
                try:
                    _, pid = win32process.GetWindowThreadProcessId(hwnd)
                    if pid:
                        pname = psutil.Process(pid).name()
                except Exception:
                    pass

                if title or (pname and win32gui.IsWindow(hwnd)):
                    results.append((hwnd, title, pname))
            except Exception:
                continue

        return results

    @staticmethod
    def find_window(
        title_or_app: Optional[str] = None,
        timeout: float = 0.0,
        pid: Optional[int] = None,
        context: Optional["AutomationContext"] = None,
    ) -> Optional[int]:
        """
        Search for a top-level window matching title substring, application/process name,
        or context last-launched application. Polls up to `timeout` seconds.
        """
        ensure_desktop()
        start = time.time()
        poll_interval = 0.15

        # Check if context provides a last-launched application or PID
        ctx_pid = pid
        ctx_name = None
        if context:
            if ctx_pid is None:
                ctx_pid = context.get_variable("last_launched_pid")
            ctx_name = context.get_variable("last_launched_name")

        # Determine search target
        target_str = (title_or_app or "").strip()
        is_generic_or_empty = not target_str or target_str.lower() in ("active", "current", "last_launched", "last")

        while True:
            # 1. If target is explicitly asking for active or left blank without context,
            # check current foreground window
            if is_generic_or_empty and not ctx_pid and not ctx_name:
                fore_hwnd = win32gui.GetForegroundWindow()
                if fore_hwnd and win32gui.IsWindow(fore_hwnd) and win32gui.IsWindowVisible(fore_hwnd):
                    return fore_hwnd

            windows = WindowManager.get_all_visible_windows()

            # 2. Check PID match first if target PID is known
            if ctx_pid:
                for hwnd, title, pname in windows:
                    try:
                        _, w_pid = win32process.GetWindowThreadProcessId(hwnd)
                        if w_pid == ctx_pid and (title or win32gui.IsWindowVisible(hwnd)):
                            return hwnd
                    except Exception:
                        pass

            # 3. Check target string or context last launched app name
            clean_targets = []
            if not is_generic_or_empty:
                clean_targets.append(target_str.lower().removesuffix(".exe"))
            if ctx_name:
                clean_targets.append(str(ctx_name).lower().removesuffix(".exe"))

            for target in clean_targets:
                if not target:
                    continue

                # Pass A: exact matches on title or process name
                for hwnd, title, pname in windows:
                    t_lower = title.lower()
                    p_lower = pname.lower().removesuffix(".exe")
                    if target == t_lower or target == p_lower:
                        return hwnd

                # Pass B: substring matches
                for hwnd, title, pname in windows:
                    t_lower = title.lower()
                    p_lower = pname.lower().removesuffix(".exe")
                    if target in t_lower or (p_lower and target in p_lower):
                        return hwnd

            # Check timeout
            if time.time() - start >= timeout:
                break
            time.sleep(poll_interval)

        # Fallback for generic/empty if no window was found yet
        if is_generic_or_empty:
            fore_hwnd = win32gui.GetForegroundWindow()
            if fore_hwnd and win32gui.IsWindow(fore_hwnd):
                return fore_hwnd

        return None

    @staticmethod
    def focus_window(
        hwnd_or_title: int | str | None,
        timeout: float = 5.0,
        context: Optional["AutomationContext"] = None,
    ) -> bool:
        """Bring window to foreground and set focus."""
        hwnd = WindowManager._resolve_hwnd(hwnd_or_title, timeout=timeout, context=context)
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
                fore_thread = win32process.GetWindowThreadProcessId(fore_hwnd)[0] if fore_hwnd else 0
                app_thread = win32api_get_current_thread_id()

                if fore_thread and fore_thread != app_thread:
                    ctypes.windll.user32.AttachThreadInput(fore_thread, app_thread, True)
                    win32gui.SetForegroundWindow(hwnd)
                    ctypes.windll.user32.AttachThreadInput(fore_thread, app_thread, False)
                else:
                    win32gui.SetForegroundWindow(hwnd)
            return True
        except Exception as e:
            logger.debug(f"Direct foreground attach notice for window {hwnd_or_title}: {e}")
            try:
                ctypes.windll.user32.SetForegroundWindow(hwnd)
                return True
            except Exception:
                return False

    @staticmethod
    def minimize_window(
        hwnd_or_title: int | str | None,
        timeout: float = 5.0,
        context: Optional["AutomationContext"] = None,
    ) -> bool:
        """Minimize window."""
        hwnd = WindowManager._resolve_hwnd(hwnd_or_title, timeout=timeout, context=context)
        if not hwnd or not win32gui.IsWindow(hwnd):
            logger.warning(f"Cannot minimize invalid window handle: {hwnd_or_title}")
            return False

        try:
            ctypes.windll.user32.ShowWindowAsync(hwnd, win32con.SW_MINIMIZE)
            win32gui.ShowWindow(hwnd, win32con.SW_MINIMIZE)
            return True
        except Exception as e:
            logger.error(f"Error minimizing window {hwnd}: {e}")
            return False

    @staticmethod
    def maximize_window(
        hwnd_or_title: int | str | None,
        timeout: float = 5.0,
        context: Optional["AutomationContext"] = None,
    ) -> bool:
        """Maximize window reliably using Win32 ShowWindow / ShowWindowAsync."""
        hwnd = WindowManager._resolve_hwnd(hwnd_or_title, timeout=timeout, context=context)
        if not hwnd or not win32gui.IsWindow(hwnd):
            logger.warning(f"Cannot maximize invalid window handle: {hwnd_or_title}")
            return False

        try:
            # 1. Restore if minimized
            if win32gui.IsIconic(hwnd):
                win32gui.ShowWindow(hwnd, win32con.SW_RESTORE)
                time.sleep(0.05)

            # 2. Async maximize to prevent UI hang across thread/process boundaries
            ctypes.windll.user32.ShowWindowAsync(hwnd, win32con.SW_MAXIMIZE)
            # 3. Synchronous show maximize
            win32gui.ShowWindow(hwnd, win32con.SW_MAXIMIZE)

            # 4. Bring to foreground
            WindowManager.focus_window(hwnd, timeout=0.0)

            return True
        except Exception as e:
            logger.error(f"Error maximizing window {hwnd}: {e}")
            return False

    @staticmethod
    def move_resize_window(
        hwnd_or_title: int | str | None,
        x: int,
        y: int,
        width: int,
        height: int,
        timeout: float = 5.0,
        context: Optional["AutomationContext"] = None,
    ) -> bool:
        """Reposition and resize window."""
        hwnd = WindowManager._resolve_hwnd(hwnd_or_title, timeout=timeout, context=context)
        if not hwnd or not win32gui.IsWindow(hwnd):
            logger.warning(f"Cannot move/resize invalid window handle: {hwnd_or_title}")
            return False

        try:
            # If window is maximized or minimized, restore to normal first so MoveWindow takes effect
            placement = win32gui.GetWindowPlacement(hwnd)
            if placement[1] in (win32con.SW_SHOWMAXIMIZED, win32con.SW_SHOWMINIMIZED):
                win32gui.ShowWindow(hwnd, win32con.SW_RESTORE)
                time.sleep(0.05)

            win32gui.MoveWindow(hwnd, int(x), int(y), int(width), int(height), True)
            return True
        except Exception as e:
            logger.error(f"Error moving/resizing window {hwnd}: {e}")
            return False

    @staticmethod
    def wait_for_window(
        title_or_app: str,
        timeout: float = 30.0,
        poll_interval: float = 0.5,
        context: Optional["AutomationContext"] = None,
    ) -> Optional[int]:
        """Poll until a matching window title or application appears."""
        return WindowManager.find_window(title_or_app, timeout=timeout, context=context)

    @staticmethod
    def _resolve_hwnd(
        hwnd_or_title: int | str | None,
        timeout: float = 5.0,
        context: Optional["AutomationContext"] = None,
    ) -> Optional[int]:
        """Resolve HWND from integer, title/app string, or active/context application."""
        if isinstance(hwnd_or_title, int):
            if win32gui.IsWindow(hwnd_or_title):
                return hwnd_or_title
            return None
        return WindowManager.find_window(hwnd_or_title, timeout=timeout, context=context)
