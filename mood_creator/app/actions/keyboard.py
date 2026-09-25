import time
import win32api
import win32con
from app.actions.base import BaseAction
from app.core.action_registry import action_registry
from app.core.execution_context import AutomationContext
from app.models.action_result import ActionResult
from app.windows.hotkeys import VK_MAP
from app.windows.windows import WindowManager

EXTENDED_KEYS = {
    win32con.VK_UP,
    win32con.VK_DOWN,
    win32con.VK_LEFT,
    win32con.VK_RIGHT,
    win32con.VK_INSERT,
    win32con.VK_DELETE,
    win32con.VK_HOME,
    win32con.VK_END,
    win32con.VK_PRIOR,
    win32con.VK_NEXT,
    win32con.VK_LWIN,
    win32con.VK_RWIN,
}


def _get_key_flags(vk: int) -> int:
    return win32con.KEYEVENTF_EXTENDEDKEY if vk in EXTENDED_KEYS else 0


class PressKeyAction(BaseAction):
    """Simulate single key press with hardware scan code and optional window target."""

    PARAM_SCHEMA = {
        "key": {
            "type": "string",
            "label": "Key Name (e.g. F11, ENTER, SPACE)",
            "required": True,
            "placeholder": "e.g. F11, ENTER, ESC, TAB",
        },
        "window": {
            "type": "string",
            "label": "Target Window / App (optional)",
            "required": False,
            "default": "",
            "placeholder": "e.g. Brave, Chrome, VLC (or leave blank for active/last launched)",
        },
        "delay_before": {
            "type": "number",
            "label": "Delay Before Press (sec)",
            "required": False,
            "default": 0.2,
        },
    }

    def execute(self, context: AutomationContext) -> ActionResult:
        key_name = str(self.params.get("key", "")).upper().strip()
        window_target = self.params.get("window") or self.params.get("title")
        delay_before = float(self.params.get("delay_before", 0.2))

        vk = VK_MAP.get(key_name)
        if not vk and len(key_name) == 1:
            vk = ord(key_name)

        if not vk:
            return ActionResult(success=False, message=f"Unknown key code for '{key_name}'", error="InvalidKey")

        # 1. Bring target window to front if specified or if an app was recently launched
        if window_target or context.get_variable("last_launched_name") or context.get_variable("last_launched_pid"):
            WindowManager.focus_window(window_target, timeout=5.0, context=context)

        # 2. Settle delay
        if delay_before > 0:
            start_wait = time.time()
            while time.time() - start_wait < delay_before:
                if context.is_cancelled():
                    return ActionResult(success=False, message="Key press cancelled")
                time.sleep(0.05)

        try:
            scan = win32api.MapVirtualKey(vk, 0)
            flags = _get_key_flags(vk)

            # Key down with hardware scan code
            win32api.keybd_event(vk, scan, flags, 0)
            time.sleep(0.08)
            # Key up
            win32api.keybd_event(vk, scan, flags | win32con.KEYEVENTF_KEYUP, 0)

            target_str = f" on '{window_target}'" if window_target else ""
            return ActionResult(success=True, message=f"Pressed key '{key_name}'{target_str}")
        except Exception as e:
            return ActionResult(success=False, message=f"Failed to press key '{key_name}'", error=str(e))


class TypeTextAction(BaseAction):
    """Type a string of characters into the active or targeted window."""

    PARAM_SCHEMA = {
        "text": {"type": "string", "label": "Text to Type", "required": True},
        "window": {
            "type": "string",
            "label": "Target Window / App (optional)",
            "required": False,
            "default": "",
            "placeholder": "e.g. Brave, Notepad (or leave blank for active)",
        },
        "delay": {"type": "number", "label": "Inter-key delay (sec)", "default": 0.02},
        "delay_before": {
            "type": "number",
            "label": "Delay Before Typing (sec)",
            "required": False,
            "default": 0.2,
        },
    }

    def execute(self, context: AutomationContext) -> ActionResult:
        text = self.params.get("text", "")
        window_target = self.params.get("window") or self.params.get("title")
        delay = float(self.params.get("delay", 0.02))
        delay_before = float(self.params.get("delay_before", 0.2))

        # Focus window if specified
        if window_target or context.get_variable("last_launched_name") or context.get_variable("last_launched_pid"):
            WindowManager.focus_window(window_target, timeout=5.0, context=context)

        if delay_before > 0:
            time.sleep(delay_before)

        try:
            for char in text:
                if context.is_cancelled():
                    return ActionResult(success=False, message="Typing cancelled")

                is_upper = char.isupper()
                if is_upper:
                    win32api.keybd_event(win32con.VK_SHIFT, 0, 0, 0)

                vk = win32api.VkKeyScan(char) & 0xFF
                if vk != 0xFF:
                    scan = win32api.MapVirtualKey(vk, 0)
                    win32api.keybd_event(vk, scan, 0, 0)
                    time.sleep(delay)
                    win32api.keybd_event(vk, scan, win32con.KEYEVENTF_KEYUP, 0)

                if is_upper:
                    win32api.keybd_event(win32con.VK_SHIFT, 0, win32con.KEYEVENTF_KEYUP, 0)

            return ActionResult(success=True, message=f"Typed text ({len(text)} chars)")
        except Exception as e:
            return ActionResult(success=False, message="Failed to type text", error=str(e))


class TriggerHotkeyAction(BaseAction):
    """Trigger a hotkey combination (e.g. CTRL+S, F11, ALT+ENTER) with hardware scan codes."""

    PARAM_SCHEMA = {
        "hotkey": {
            "type": "string",
            "label": "Hotkey String (e.g. F11, CTRL+S, ALT+ENTER)",
            "required": True,
            "placeholder": "e.g. F11, CTRL+ALT+T, ALT+ENTER",
        },
        "window": {
            "type": "string",
            "label": "Target Window / App (optional)",
            "required": False,
            "default": "",
            "placeholder": "e.g. Brave, Chrome, VLC (or leave blank for active/last launched)",
        },
        "delay_before": {
            "type": "number",
            "label": "Delay Before Press (sec)",
            "required": False,
            "default": 0.2,
        },
    }

    def execute(self, context: AutomationContext) -> ActionResult:
        hotkey_str = self.params.get("hotkey", "").upper().strip()
        window_target = self.params.get("window") or self.params.get("title")
        delay_before = float(self.params.get("delay_before", 0.2))

        parts = [p.strip() for p in hotkey_str.split("+")]

        mod_vks = []
        key_vk = None

        for part in parts:
            if part in ["CTRL", "CONTROL"]:
                mod_vks.append(win32con.VK_CONTROL)
            elif part == "ALT":
                mod_vks.append(win32con.VK_MENU)
            elif part == "SHIFT":
                mod_vks.append(win32con.VK_SHIFT)
            elif part in ["WIN", "WINDOWS", "SUPER", "META"]:
                mod_vks.append(win32con.VK_LWIN)
            elif part in VK_MAP:
                key_vk = VK_MAP[part]
            elif len(part) == 1:
                key_vk = ord(part)

        if not key_vk and not mod_vks:
            return ActionResult(success=False, message=f"Invalid hotkey '{hotkey_str}'", error="ParseError")

        # Focus window if specified
        if window_target or context.get_variable("last_launched_name") or context.get_variable("last_launched_pid"):
            WindowManager.focus_window(window_target, timeout=5.0, context=context)

        if delay_before > 0:
            start_wait = time.time()
            while time.time() - start_wait < delay_before:
                if context.is_cancelled():
                    return ActionResult(success=False, message="Hotkey cancelled")
                time.sleep(0.05)

        try:
            # Press modifiers down
            for mod in mod_vks:
                m_scan = win32api.MapVirtualKey(mod, 0)
                win32api.keybd_event(mod, m_scan, _get_key_flags(mod), 0)

            # Press main key
            if key_vk:
                k_scan = win32api.MapVirtualKey(key_vk, 0)
                flags = _get_key_flags(key_vk)
                win32api.keybd_event(key_vk, k_scan, flags, 0)
                time.sleep(0.08)
                win32api.keybd_event(key_vk, k_scan, flags | win32con.KEYEVENTF_KEYUP, 0)

            # Release modifiers up
            for mod in reversed(mod_vks):
                m_scan = win32api.MapVirtualKey(mod, 0)
                win32api.keybd_event(mod, m_scan, _get_key_flags(mod) | win32con.KEYEVENTF_KEYUP, 0)

            target_str = f" on '{window_target}'" if window_target else ""
            return ActionResult(success=True, message=f"Triggered hotkey '{hotkey_str}'{target_str}")
        except Exception as e:
            return ActionResult(success=False, message=f"Failed to trigger hotkey '{hotkey_str}'", error=str(e))


# Register keyboard actions
action_registry.register("keyboard.press_key", PressKeyAction, category="Keyboard", display_name="Press Key")
action_registry.register("keyboard.type_text", TypeTextAction, category="Keyboard", display_name="Type Text")
action_registry.register("keyboard.hotkey", TriggerHotkeyAction, category="Keyboard", display_name="Trigger Hotkey")

