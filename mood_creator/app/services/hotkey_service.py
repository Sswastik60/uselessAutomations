import logging
from typing import Callable, Dict, Optional
from app.core.exceptions import HotkeyConflictError
from app.windows.hotkeys import HotkeyThread

logger = logging.getLogger(__name__)


class HotkeyService:
    """Service for binding global system hotkeys to mode execution triggers."""

    def __init__(self, mode_trigger_callback: Callable[[str], None]):
        self.trigger_callback = mode_trigger_callback
        self.hotkey_thread = HotkeyThread()
        self._mode_hotkeys: Dict[str, str] = {}  # mode_id -> hotkey_str
        self._hotkey_modes: Dict[str, str] = {}  # HOTKEY_STR -> mode_id

        # Connect thread signal to handler
        self.hotkey_thread.signal_helper.hotkey_pressed.connect(self._on_hotkey_pressed)
        self.hotkey_thread.start()

    def register_mode_hotkey(self, mode_id: str, hotkey_str: str) -> bool:
        """Bind a mode to a hotkey combination."""
        if not hotkey_str or not hotkey_str.strip():
            return False

        normalized_hk = hotkey_str.strip().upper()

        # Check if already bound to another mode
        if normalized_hk in self._hotkey_modes:
            existing_mode = self._hotkey_modes[normalized_hk]
            if existing_mode != mode_id:
                logger.warning(f"Hotkey '{hotkey_str}' is already bound to mode '{existing_mode}'. Skipping for '{mode_id}'.")
                return False

        # Unregister previous hotkey for this mode if any
        self.unregister_mode_hotkey(mode_id)

        try:
            self.hotkey_thread.register_hotkey(normalized_hk)
            self._mode_hotkeys[mode_id] = normalized_hk
            self._hotkey_modes[normalized_hk] = mode_id
            logger.info(f"Bound mode '{mode_id}' to hotkey '{normalized_hk}'")
            return True
        except Exception as e:
            logger.error(f"Failed to register hotkey '{hotkey_str}' for mode '{mode_id}': {e}")
            return False

    def unregister_mode_hotkey(self, mode_id: str) -> None:
        """Unbind a hotkey for a mode."""
        if mode_id in self._mode_hotkeys:
            hk = self._mode_hotkeys[mode_id]
            self.hotkey_thread.unregister_hotkey(hk)
            del self._mode_hotkeys[mode_id]
            if hk in self._hotkey_modes:
                del self._hotkey_modes[hk]

    def _on_hotkey_pressed(self, hotkey_str: str) -> None:
        """Handler called when global hotkey is detected."""
        normalized = hotkey_str.upper()
        if normalized in self._hotkey_modes:
            mode_id = self._hotkey_modes[normalized]
            logger.info(f"Hotkey '{hotkey_str}' triggered mode '{mode_id}'")
            self.trigger_callback(mode_id)

    def stop(self) -> None:
        """Stop hotkey listener thread."""
        self.hotkey_thread.stop()
        self.hotkey_thread.wait(2000)
