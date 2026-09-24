import time
import win32api
import win32con
from app.actions.base import BaseAction
from app.core.action_registry import action_registry
from app.core.execution_context import AutomationContext
from app.models.action_result import ActionResult
from app.windows.hotkeys import VK_MAP


class PressKeyAction(BaseAction):
    """Simulate single key press."""

    PARAM_SCHEMA = {
        "key": {"type": "string", "label": "Key Name (e.g. ENTER, F5, A)", "required": True}
    }

    def execute(self, context: AutomationContext) -> ActionResult:
        key_name = str(self.params.get("key", "")).upper()
        vk = VK_MAP.get(key_name)
        if not vk and len(key_name) == 1:
            vk = ord(key_name)

        if not vk:
            return ActionResult(success=False, message=f"Unknown key code for '{key_name}'", error="InvalidKey")

        try:
            win32api.keybd_event(vk, 0, 0, 0)
            time.sleep(0.05)
            win32api.keybd_event(vk, 0, win32con.KEYEVENTF_KEYUP, 0)
            return ActionResult(success=True, message=f"Pressed key '{key_name}'")
        except Exception as e:
            return ActionResult(success=False, message=f"Failed to press key '{key_name}'", error=str(e))


class TypeTextAction(BaseAction):
    """Type a string of characters."""

    PARAM_SCHEMA = {
        "text": {"type": "string", "label": "Text to Type", "required": True},
        "delay": {"type": "number", "label": "Inter-key delay (sec)", "default": 0.02},
    }

    def execute(self, context: AutomationContext) -> ActionResult:
        text = self.params.get("text", "")
        delay = float(self.params.get("delay", 0.02))

        try:
            for char in text:
                if context.is_cancelled():
                    return ActionResult(success=False, message="Typing cancelled")
                
                # Check uppercase
                is_upper = char.isupper()
                if is_upper:
                    win32api.keybd_event(win32con.VK_SHIFT, 0, 0, 0)

                vk = win32api.VkKeyScan(char) & 0xFF
                if vk != 0xFF:
                    win32api.keybd_event(vk, 0, 0, 0)
                    time.sleep(delay)
                    win32api.keybd_event(vk, 0, win32con.KEYEVENTF_KEYUP, 0)

                if is_upper:
                    win32api.keybd_event(win32con.VK_SHIFT, 0, win32con.KEYEVENTF_KEYUP, 0)

            return ActionResult(success=True, message=f"Typed text ({len(text)} chars)")
        except Exception as e:
            return ActionResult(success=False, message="Failed to type text", error=str(e))


class TriggerHotkeyAction(BaseAction):
    """Trigger a hotkey combination (e.g. CTRL+S)."""

    PARAM_SCHEMA = {
        "hotkey": {"type": "string", "label": "Hotkey String (e.g. CTRL+S)", "required": True}
    }

    def execute(self, context: AutomationContext) -> ActionResult:
        hotkey_str = self.params.get("hotkey", "").upper()
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
            elif part in VK_MAP:
                key_vk = VK_MAP[part]
            elif len(part) == 1:
                key_vk = ord(part)

        if not key_vk:
            return ActionResult(success=False, message=f"Invalid hotkey '{hotkey_str}'", error="ParseError")

        try:
            # Press modifiers down
            for mod in mod_vks:
                win32api.keybd_event(mod, 0, 0, 0)
            
            # Press key
            win32api.keybd_event(key_vk, 0, 0, 0)
            time.sleep(0.05)
            win32api.keybd_event(key_vk, 0, win32con.KEYEVENTF_KEYUP, 0)

            # Release modifiers up
            for mod in reversed(mod_vks):
                win32api.keybd_event(mod, 0, win32con.KEYEVENTF_KEYUP, 0)

            return ActionResult(success=True, message=f"Triggered hotkey '{hotkey_str}'")
        except Exception as e:
            return ActionResult(success=False, message=f"Failed to trigger hotkey '{hotkey_str}'", error=str(e))


# Register keyboard actions
action_registry.register("keyboard.press_key", PressKeyAction, category="Keyboard", display_name="Press Key")
action_registry.register("keyboard.type_text", TypeTextAction, category="Keyboard", display_name="Type Text")
action_registry.register("keyboard.hotkey", TriggerHotkeyAction, category="Keyboard", display_name="Trigger Hotkey")
