import time
import win32api
import win32con
from app.actions.base import BaseAction
from app.core.action_registry import action_registry
from app.core.execution_context import AutomationContext
from app.models.action_result import ActionResult


class MouseClickAction(BaseAction):
    """Click mouse button at current or specified coordinate."""

    PARAM_SCHEMA = {
        "x": {"type": "number", "label": "X Coordinate (optional)", "required": False},
        "y": {"type": "number", "label": "Y Coordinate (optional)", "required": False},
        "button": {"type": "string", "label": "Button (left/right/middle)", "default": "left"},
        "clicks": {"type": "number", "label": "Number of Clicks", "default": 1},
    }

    def execute(self, context: AutomationContext) -> ActionResult:
        x = self.params.get("x")
        y = self.params.get("y")
        button = str(self.params.get("button", "left")).lower()
        clicks = int(self.params.get("clicks", 1))

        try:
            if x is not None and y is not None:
                win32api.SetCursorPos((int(x), int(y)))
                time.sleep(0.05)

            down_evt = win32con.MOUSEEVENTF_LEFTDOWN
            up_evt = win32con.MOUSEEVENTF_LEFTUP
            if button == "right":
                down_evt = win32con.MOUSEEVENTF_RIGHTDOWN
                up_evt = win32con.MOUSEEVENTF_RIGHTUP
            elif button == "middle":
                down_evt = win32con.MOUSEEVENTF_MIDDLEDOWN
                up_evt = win32con.MOUSEEVENTF_MIDDLEUP

            for _ in range(clicks):
                win32api.mouse_event(down_evt, 0, 0, 0, 0)
                time.sleep(0.02)
                win32api.mouse_event(up_evt, 0, 0, 0, 0)
                time.sleep(0.05)

            curr_pos = win32api.GetCursorPos()
            return ActionResult(success=True, message=f"Clicked mouse ({button}) at {curr_pos}")
        except Exception as e:
            return ActionResult(success=False, message="Failed mouse click", error=str(e))


class MoveCursorAction(BaseAction):
    """Move cursor position to (x, y)."""

    PARAM_SCHEMA = {
        "x": {"type": "number", "label": "X Coordinate", "required": True},
        "y": {"type": "number", "label": "Y Coordinate", "required": True},
    }

    def execute(self, context: AutomationContext) -> ActionResult:
        x = int(self.params.get("x", 0))
        y = int(self.params.get("y", 0))
        try:
            win32api.SetCursorPos((x, y))
            return ActionResult(success=True, message=f"Moved cursor to ({x}, {y})")
        except Exception as e:
            return ActionResult(success=False, message=f"Failed to move cursor", error=str(e))


class ScrollMouseAction(BaseAction):
    """Scroll mouse wheel."""

    PARAM_SCHEMA = {
        "amount": {"type": "number", "label": "Scroll Amount (positive = up, negative = down)", "default": 120}
    }

    def execute(self, context: AutomationContext) -> ActionResult:
        amount = int(self.params.get("amount", 120))
        try:
            win32api.mouse_event(win32con.MOUSEEVENTF_WHEEL, 0, 0, amount, 0)
            return ActionResult(success=True, message=f"Scrolled mouse wheel ({amount})")
        except Exception as e:
            return ActionResult(success=False, message="Failed to scroll mouse", error=str(e))


# Register mouse actions
action_registry.register("mouse.click", MouseClickAction, category="Mouse", display_name="Mouse Click")
action_registry.register("mouse.move", MoveCursorAction, category="Mouse", display_name="Move Cursor")
action_registry.register("mouse.scroll", ScrollMouseAction, category="Mouse", display_name="Scroll Mouse Wheel")
