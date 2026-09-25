import ctypes
from ctypes import wintypes
import logging
import time
from typing import Callable, Dict, Optional, Set, Tuple
from PySide6.QtCore import QAbstractNativeEventFilter, QObject, QThread, Signal
from PySide6.QtWidgets import QApplication
import win32con

logger = logging.getLogger(__name__)

# Virtual key map for common hotkey strings
VK_MAP = {
    # Alphabet A-Z
    **{chr(c): c for c in range(ord('A'), ord('Z') + 1)},
    # Digits 0-9
    **{str(n): ord(str(n)) for n in range(10)},
    # Function keys F1-F24
    **{f"F{i}": getattr(win32con, f"VK_F{i}") for i in range(1, 25)},
    # Common navigation & editing
    "SPACE": win32con.VK_SPACE,
    "ENTER": win32con.VK_RETURN,
    "RETURN": win32con.VK_RETURN,
    "TAB": win32con.VK_TAB,
    "ESC": win32con.VK_ESCAPE,
    "ESCAPE": win32con.VK_ESCAPE,
    "BACKSPACE": win32con.VK_BACK,
    "BKSP": win32con.VK_BACK,
    "DELETE": win32con.VK_DELETE,
    "DEL": win32con.VK_DELETE,
    "INSERT": win32con.VK_INSERT,
    "INS": win32con.VK_INSERT,
    "HOME": win32con.VK_HOME,
    "END": win32con.VK_END,
    "PAGEUP": win32con.VK_PRIOR,
    "PGUP": win32con.VK_PRIOR,
    "PAGEDOWN": win32con.VK_NEXT,
    "PGDN": win32con.VK_NEXT,
    "UP": win32con.VK_UP,
    "DOWN": win32con.VK_DOWN,
    "LEFT": win32con.VK_LEFT,
    "RIGHT": win32con.VK_RIGHT,
    "PRINTSCREEN": win32con.VK_SNAPSHOT,
    "PAUSE": win32con.VK_PAUSE,
    "CAPSLOCK": win32con.VK_CAPITAL,
    "NUMLOCK": win32con.VK_NUMLOCK,
    "SCROLLLOCK": win32con.VK_SCROLL,
    "GRAVE": 0xC0,
    "TILDE": 0xC0,
    "`": 0xC0,
    "-": 0xBD,
    "MINUS": 0xBD,
    "=": 0xBB,
    "EQUAL": 0xBB,
    "[": 0xDB,
    "]": 0xDD,
    "\\": 0xDC,
    ";": 0xBA,
    "'": 0xDE,
    ",": 0xBC,
    ".": 0xBE,
    "/": 0xBF,
}

MOD_NOREPEAT = 0x4000  # Suppress repeat notifications when key is held (Windows 7+)
MOD_MAP = {
    "ALT": win32con.MOD_ALT,
    "CTRL": win32con.MOD_CONTROL,
    "CONTROL": win32con.MOD_CONTROL,
    "SHIFT": win32con.MOD_SHIFT,
    "WIN": win32con.MOD_WIN,
    "WINDOWS": win32con.MOD_WIN,
    "SUPER": win32con.MOD_WIN,
}


def parse_hotkey_string(hotkey_str: str) -> Tuple[int, int]:
    """Parse hotkey string (e.g. 'CTRL+ALT+G') into (modifiers, vk_code)."""
    parts = [p.strip().upper() for p in hotkey_str.split("+")]
    modifiers = 0
    vk = 0

    for part in parts:
        if part in MOD_MAP:
            modifiers |= MOD_MAP[part]
        elif part in VK_MAP:
            vk = VK_MAP[part]
        elif len(part) == 1 and ord(part) in range(65, 91):
            vk = ord(part)
        elif len(part) == 1 and part.isdigit():
            vk = ord(part)
        else:
            raise ValueError(f"Unrecognized hotkey component: '{part}' in '{hotkey_str}'")

    if vk == 0:
        raise ValueError(f"No key code found in hotkey '{hotkey_str}'")

    return modifiers, vk


class HotkeySignalHelper(QObject):
    """Signal proxy for cross-thread hotkey dispatch to Qt main UI thread."""
    hotkey_pressed = Signal(str)


class POINT(ctypes.Structure):
    _fields_ = [("x", ctypes.c_long), ("y", ctypes.c_long)]


class MSG(ctypes.Structure):
    _fields_ = [
        ("hwnd", ctypes.c_void_p),
        ("message", ctypes.c_uint),
        ("wParam", ctypes.c_size_t),
        ("lParam", ctypes.c_size_t),
        ("time", ctypes.c_ulong),
        ("pt", POINT),
        ("lPrivate", ctypes.c_ulong),
    ]


class KBDLLHOOKSTRUCT(ctypes.Structure):
    _fields_ = [
        ("vkCode", wintypes.DWORD),
        ("scanCode", wintypes.DWORD),
        ("flags", wintypes.DWORD),
        ("time", wintypes.DWORD),
        ("dwExtraInfo", ctypes.c_size_t),
    ]


# Win32 Function Signatures for 64-bit safety
user32 = ctypes.windll.user32
kernel32 = ctypes.windll.kernel32

HOOKPROC = ctypes.WINFUNCTYPE(ctypes.c_longlong, ctypes.c_int, wintypes.WPARAM, wintypes.LPARAM)
user32.SetWindowsHookExW.argtypes = [ctypes.c_int, HOOKPROC, wintypes.HINSTANCE, wintypes.DWORD]
user32.SetWindowsHookExW.restype = wintypes.HHOOK
user32.CallNextHookEx.argtypes = [wintypes.HHOOK, ctypes.c_int, wintypes.WPARAM, wintypes.LPARAM]
user32.CallNextHookEx.restype = ctypes.c_longlong
user32.UnhookWindowsHookEx.argtypes = [wintypes.HHOOK]


class GlobalHotkeyNativeFilter(QAbstractNativeEventFilter):
    """Native event filter for intercepting WM_HOTKEY in Qt's main message loop."""

    def __init__(self, dispatch_fn: Callable[[int], None]):
        super().__init__()
        self.dispatch_fn = dispatch_fn

    def nativeEventFilter(self, eventType, message) -> Tuple[bool, int]:
        if eventType in (b"windows_generic_MSG", "windows_generic_MSG"):
            try:
                msg = wintypes.MSG.from_address(message.__int__())
                if msg.message == win32con.WM_HOTKEY:
                    hk_id = int(msg.wParam)
                    self.dispatch_fn(hk_id)
                    return True, 0
            except Exception as e:
                logger.debug(f"Error in nativeEventFilter: {e}")
        return False, 0


class HotkeyThread(QThread):
    """Global system-wide hotkey listener supporting both Win32 RegisterHotKey and low-level keyboard hook fallback.
    
    Guarantees hotkey detection whether the application is active, full screen, minimized, or hidden in the system tray.
    """

    def __init__(self, parent: Optional[QObject] = None):
        super().__init__(parent)
        self.signal_helper = HotkeySignalHelper()
        self._hotkeys: Dict[int, Tuple[str, int, int]] = {}  # id -> (hotkey_str, mod, vk)
        self._combo_map: Dict[Tuple[int, int], str] = {}  # (mod, vk) -> hotkey_str
        self._win32_registered_ids: Set[int] = set()
        self._next_id = 1
        self._running = False
        self._thread_id: Optional[int] = None
        self._native_filter: Optional[GlobalHotkeyNativeFilter] = None
        self._hook_handle: Optional[int] = None
        self._hook_proc_ref = None
        self._last_trigger_time: Dict[str, float] = {}

    def register_hotkey(self, hotkey_str: str) -> int:
        """Register a global hotkey combination."""
        mod, vk = parse_hotkey_string(hotkey_str)

        # Check if already registered
        for hk_id, (existing_str, existing_mod, existing_vk) in self._hotkeys.items():
            if existing_mod == mod and existing_vk == vk:
                return hk_id

        hk_id = self._next_id
        self._next_id += 1
        self._hotkeys[hk_id] = (hotkey_str, mod, vk)
        self._combo_map[(mod, vk)] = hotkey_str

        # Register with Win32 API
        res = user32.RegisterHotKey(None, hk_id, mod | MOD_NOREPEAT, vk)
        if res:
            self._win32_registered_ids.add(hk_id)
            logger.info(f"Registered global Win32 hotkey '{hotkey_str}' (ID={hk_id})")
        else:
            err = ctypes.GetLastError()
            logger.warning(
                f"RegisterHotKey returned {res} (code {err}) for '{hotkey_str}'. "
                "Low-level keyboard hook fallback will intercept this hotkey."
            )

        return hk_id

    def unregister_hotkey(self, hotkey_id_or_str: int | str) -> bool:
        """Unregister a hotkey by ID or hotkey string."""
        target_id = None
        if isinstance(hotkey_id_or_str, int):
            target_id = hotkey_id_or_str
        else:
            for hk_id, (str_val, _, _) in list(self._hotkeys.items()):
                if str_val.upper() == hotkey_id_or_str.upper():
                    target_id = hk_id
                    break

        if target_id and target_id in self._hotkeys:
            hk_str, mod, vk = self._hotkeys[target_id]
            if target_id in self._win32_registered_ids:
                user32.UnregisterHotKey(None, target_id)
                self._win32_registered_ids.discard(target_id)
            self._hotkeys.pop(target_id, None)
            self._combo_map.pop((mod, vk), None)
            logger.info(f"Unregistered global hotkey ID={target_id} ('{hk_str}')")
            return True
        return False

    def _dispatch_trigger(self, hotkey_str: str) -> None:
        """Debounced dispatch of hotkey event to signal helper."""
        now = time.monotonic()
        last = self._last_trigger_time.get(hotkey_str, 0.0)
        if now - last < 0.25:
            # Debounce repeated triggers within 250ms
            return
        self._last_trigger_time[hotkey_str] = now
        logger.info(f"Global hotkey triggered: '{hotkey_str}'")
        self.signal_helper.hotkey_pressed.emit(hotkey_str)

    def _on_win32_hotkey(self, hk_id: int) -> None:
        """Callback from native event filter when WM_HOTKEY arrives."""
        if hk_id in self._hotkeys:
            hk_str = self._hotkeys[hk_id][0]
            self._dispatch_trigger(hk_str)

    def _ll_hook_callback(self, nCode: int, wParam: int, lParam: int) -> int:
        """Low-level keyboard hook procedure for fallback and tray hotkey listening."""
        if nCode >= 0 and wParam in (win32con.WM_KEYDOWN, win32con.WM_SYSKEYDOWN):
            try:
                kb = KBDLLHOOKSTRUCT.from_address(lParam)
                vk = kb.vkCode

                # Read active modifier states
                mod = 0
                if (user32.GetAsyncKeyState(win32con.VK_CONTROL) & 0x8000) != 0:
                    mod |= win32con.MOD_CONTROL
                if (user32.GetAsyncKeyState(win32con.VK_MENU) & 0x8000) != 0:
                    mod |= win32con.MOD_ALT
                if (user32.GetAsyncKeyState(win32con.VK_SHIFT) & 0x8000) != 0:
                    mod |= win32con.MOD_SHIFT
                if (
                    (user32.GetAsyncKeyState(win32con.VK_LWIN) & 0x8000) != 0
                    or (user32.GetAsyncKeyState(win32con.VK_RWIN) & 0x8000) != 0
                ):
                    mod |= win32con.MOD_WIN

                combo = (mod, vk)
                if combo in self._combo_map:
                    hk_str = self._combo_map[combo]
                    self._dispatch_trigger(hk_str)
            except Exception as e:
                logger.debug(f"Error in hook callback: {e}")

        return user32.CallNextHookEx(self._hook_handle, nCode, wParam, lParam)

    def start(self, priority: QThread.Priority = QThread.Priority.InheritPriority) -> None:
        """Start listening for global hotkeys."""
        self._running = True

        app = QApplication.instance()
        if app is not None:
            # Install native event filter in Qt's main event dispatcher
            if self._native_filter is None:
                self._native_filter = GlobalHotkeyNativeFilter(self._on_win32_hotkey)
                app.installNativeEventFilter(self._native_filter)
                logger.info("Installed GlobalHotkeyNativeFilter on QApplication.")

            # Install low-level hook as resilient fallback for conflicts & tray modes
            if self._hook_handle is None:
                self._hook_proc_ref = HOOKPROC(self._ll_hook_callback)
                self._hook_handle = user32.SetWindowsHookExW(
                    win32con.WH_KEYBOARD_LL, self._hook_proc_ref, None, 0
                )
                if self._hook_handle:
                    logger.info("Installed WH_KEYBOARD_LL hook listener for background hotkeys.")
                else:
                    logger.warning(f"Could not install WH_KEYBOARD_LL hook: error {ctypes.GetLastError()}")
        else:
            # If no QApplication instance, run worker thread message loop
            super().start(priority)

    def run(self) -> None:
        """Message loop for receiving WM_HOTKEY messages when running outside a Qt GUI application."""
        self._thread_id = kernel32.GetCurrentThreadId()
        
        # Register hotkeys on this thread
        for hk_id, (hk_str, mod, vk) in list(self._hotkeys.items()):
            res = user32.RegisterHotKey(None, hk_id, mod | MOD_NOREPEAT, vk)
            if res:
                self._win32_registered_ids.add(hk_id)

        msg = MSG()
        while self._running:
            b_ret = user32.GetMessageW(ctypes.byref(msg), None, 0, 0)
            if b_ret == 0 or b_ret == -1:
                break

            if msg.message == win32con.WM_HOTKEY:
                self._on_win32_hotkey(msg.wParam)

            user32.TranslateMessage(ctypes.byref(msg))
            user32.DispatchMessageW(ctypes.byref(msg))

    def stop(self) -> None:
        """Stop hotkey listening and clean up all resources."""
        self._running = False

        # Unhook low-level keyboard hook
        if self._hook_handle:
            try:
                user32.UnhookWindowsHookEx(self._hook_handle)
            except Exception as e:
                logger.debug(f"Error unhooking keyboard hook: {e}")
            self._hook_handle = None
            self._hook_proc_ref = None

        # Remove native event filter
        app = QApplication.instance()
        if app is not None and self._native_filter is not None:
            try:
                app.removeNativeEventFilter(self._native_filter)
            except Exception as e:
                logger.debug(f"Error removing native event filter: {e}")
            self._native_filter = None

        # Unregister all Win32 hotkeys
        for hk_id in list(self._win32_registered_ids):
            try:
                user32.UnregisterHotKey(None, hk_id)
            except Exception as e:
                logger.debug(f"Error unregistering hotkey ID={hk_id}: {e}")
        self._win32_registered_ids.clear()

        # Stop thread if running
        tid = getattr(self, "_thread_id", None)
        if tid:
            user32.PostThreadMessageW(tid, win32con.WM_QUIT, 0, 0)
        else:
            self.quit()
