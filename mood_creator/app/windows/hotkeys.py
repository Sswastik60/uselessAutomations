import ctypes
import logging
from typing import Callable, Dict, Optional, Tuple
from PySide6.QtCore import QObject, QThread, Signal
import win32con

logger = logging.getLogger(__name__)

# Virtual key map for common hotkey strings
VK_MAP = {
    "A": 0x41, "B": 0x42, "C": 0x43, "D": 0x44, "E": 0x45, "F": 0x46, "G": 0x47,
    "H": 0x48, "I": 0x49, "J": 0x4A, "K": 0x4B, "L": 0x4C, "M": 0x4D, "N": 0x4E,
    "O": 0x4F, "P": 0x50, "Q": 0x51, "R": 0x52, "S": 0x53, "T": 0x54, "U": 0x55,
    "V": 0x56, "W": 0x57, "X": 0x58, "Y": 0x59, "Z": 0x5A,
    "0": 0x30, "1": 0x31, "2": 0x32, "3": 0x33, "4": 0x34,
    "5": 0x35, "6": 0x36, "7": 0x37, "8": 0x38, "9": 0x39,
    "F1": win32con.VK_F1, "F2": win32con.VK_F2, "F3": win32con.VK_F3,
    "F4": win32con.VK_F4, "F5": win32con.VK_F5, "F6": win32con.VK_F6,
    "F7": win32con.VK_F7, "F8": win32con.VK_F8, "F9": win32con.VK_F9,
    "F10": win32con.VK_F10, "F11": win32con.VK_F11, "F12": win32con.VK_F12,
    "SPACE": win32con.VK_SPACE, "ENTER": win32con.VK_RETURN, "TAB": win32con.VK_TAB,
    "ESC": win32con.VK_ESCAPE, "ESCAPE": win32con.VK_ESCAPE,
}

MOD_MAP = {
    "ALT": win32con.MOD_ALT,
    "CTRL": win32con.MOD_CONTROL,
    "CONTROL": win32con.MOD_CONTROL,
    "SHIFT": win32con.MOD_SHIFT,
    "WIN": win32con.MOD_WIN,
    "WINDOWS": win32con.MOD_WIN,
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


class HotkeyThread(QThread):
    """Background Windows message loop thread for listening to system RegisterHotKey events."""

    def __init__(self, parent: Optional[QObject] = None):
        super().__init__(parent)
        self.signal_helper = HotkeySignalHelper()
        self._hotkeys: Dict[int, Tuple[str, int, int]] = {}  # id -> (hotkey_str, mod, vk)
        self._next_id = 1
        self._running = False
        self._thread_id: Optional[int] = None

    def register_hotkey(self, hotkey_str: str) -> int:
        """Register a hotkey combination."""
        mod, vk = parse_hotkey_string(hotkey_str)
        
        # Check if already registered
        for hk_id, (existing_str, existing_mod, existing_vk) in self._hotkeys.items():
            if existing_mod == mod and existing_vk == vk:
                return hk_id

        hk_id = self._next_id
        self._next_id += 1
        self._hotkeys[hk_id] = (hotkey_str, mod, vk)

        # If thread is running, register directly via Win32 API
        if self._running:
            res = ctypes.windll.user32.RegisterHotKey(None, hk_id, mod, vk)
            if not res:
                del self._hotkeys[hk_id]
                err = ctypes.GetLastError()
                logger.warning(f"Could not register hotkey '{hotkey_str}' (reserved by Windows or another app, error: {err})")
                return -1

        logger.info(f"Registered hotkey '{hotkey_str}' (ID={hk_id})")
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
            if self._running:
                ctypes.windll.user32.UnregisterHotKey(None, target_id)
            del self._hotkeys[target_id]
            logger.info(f"Unregistered hotkey ID={target_id}")
            return True
        return False

    def run(self) -> None:
        """Message loop for receiving WM_HOTKEY messages."""
        self._running = True
        self._thread_id = ctypes.windll.kernel32.GetCurrentThreadId()
        user32 = ctypes.windll.user32
        
        # Register all pending hotkeys
        failed_ids = []
        for hk_id, (hk_str, mod, vk) in list(self._hotkeys.items()):
            res = user32.RegisterHotKey(None, hk_id, mod, vk)
            if not res:
                failed_ids.append(hk_id)
                logger.warning(f"Could not register hotkey '{hk_str}' (may be reserved by Windows or another app).")

        for fid in failed_ids:
            self._hotkeys.pop(fid, None)

        msg = MSG()
        while self._running:
            b_ret = user32.GetMessageW(ctypes.byref(msg), None, 0, 0)
            if b_ret == 0 or b_ret == -1:
                break
            
            # WM_HOTKEY message ID = 0x0312
            if msg.message == win32con.WM_HOTKEY:
                hk_id = msg.wParam
                if hk_id in self._hotkeys:
                    hk_str = self._hotkeys[hk_id][0]
                    logger.debug(f"Global hotkey triggered: '{hk_str}'")
                    self.signal_helper.hotkey_pressed.emit(hk_str)

            user32.TranslateMessage(ctypes.byref(msg))
            user32.DispatchMessageW(ctypes.byref(msg))

        # Cleanup on stop
        for hk_id in list(self._hotkeys.keys()):
            user32.UnregisterHotKey(None, hk_id)
        self._running = False

    def stop(self) -> None:
        """Stop background message thread."""
        self._running = False
        tid = getattr(self, "_thread_id", None)
        if tid:
            ctypes.windll.user32.PostThreadMessageW(tid, win32con.WM_QUIT, 0, 0)
        else:
            self.quit()
