from app.actions.base import BaseAction
from app.core.action_registry import action_registry
from app.core.execution_context import AutomationContext
from app.models.action_result import ActionResult
from app.windows.windows import WindowManager


class FocusWindowAction(BaseAction):
    """Bring a matching application window to front and set focus."""

    PARAM_SCHEMA = {
        "title": {"type": "string", "label": "Window Title Substring", "required": True}
    }

    def execute(self, context: AutomationContext) -> ActionResult:
        title = self.params.get("title")
        if not title:
            return ActionResult(success=False, message="Window title required", error="Missing title")

        hwnd = WindowManager.find_window(title)
        if not hwnd:
            return ActionResult(success=False, message=f"Window with title matching '{title}' not found.")

        ok = WindowManager.focus_window(hwnd)
        if ok:
            return ActionResult(success=True, message=f"Focused window matching '{title}'")
        return ActionResult(success=False, message=f"Could not focus window '{title}'", error="Win32 call failed")


class MinimizeWindowAction(BaseAction):
    """Minimize a matching window."""

    PARAM_SCHEMA = {
        "title": {"type": "string", "label": "Window Title Substring", "required": True}
    }

    def execute(self, context: AutomationContext) -> ActionResult:
        title = self.params.get("title")
        ok = WindowManager.minimize_window(title)
        if ok:
            return ActionResult(success=True, message=f"Minimized window '{title}'")
        return ActionResult(success=False, message=f"Window '{title}' not found or could not minimize.")


class MaximizeWindowAction(BaseAction):
    """Maximize a matching window."""

    PARAM_SCHEMA = {
        "title": {"type": "string", "label": "Window Title Substring", "required": True}
    }

    def execute(self, context: AutomationContext) -> ActionResult:
        title = self.params.get("title")
        ok = WindowManager.maximize_window(title)
        if ok:
            return ActionResult(success=True, message=f"Maximized window '{title}'")
        return ActionResult(success=False, message=f"Window '{title}' not found or could not maximize.")


class MoveResizeWindowAction(BaseAction):
    """Reposition and resize a window."""

    PARAM_SCHEMA = {
        "title": {"type": "string", "label": "Window Title Substring", "required": True},
        "x": {"type": "number", "label": "X Position", "default": 0},
        "y": {"type": "number", "label": "Y Position", "default": 0},
        "width": {"type": "number", "label": "Width", "default": 1280},
        "height": {"type": "number", "label": "Height", "default": 720},
    }

    def execute(self, context: AutomationContext) -> ActionResult:
        title = self.params.get("title")
        x = int(self.params.get("x", 0))
        y = int(self.params.get("y", 0))
        w = int(self.params.get("width", 1280))
        h = int(self.params.get("height", 720))

        ok = WindowManager.move_resize_window(title, x, y, w, h)
        if ok:
            return ActionResult(success=True, message=f"Resized window '{title}' to {w}x{h} at ({x},{y})")
        return ActionResult(success=False, message=f"Window '{title}' not found.")


# Register window actions
action_registry.register("window.focus", FocusWindowAction, category="Window", display_name="Focus Window")
action_registry.register("window.minimize", MinimizeWindowAction, category="Window", display_name="Minimize Window")
action_registry.register("window.maximize", MaximizeWindowAction, category="Window", display_name="Maximize Window")
action_registry.register("window.move", MoveResizeWindowAction, category="Window", display_name="Move / Resize Window")
