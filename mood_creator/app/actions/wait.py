import os
import time
from app.actions.base import BaseAction
from app.core.action_registry import action_registry
from app.core.execution_context import AutomationContext
from app.models.action_result import ActionResult
from app.windows.processes import ProcessManager
from app.windows.windows import WindowManager


class WaitDurationAction(BaseAction):
    """Wait for a specified duration in seconds with responsive cancellation polling."""

    PARAM_SCHEMA = {
        "seconds": {"type": "number", "label": "Duration (seconds)", "required": True, "default": 1.0}
    }

    def execute(self, context: AutomationContext) -> ActionResult:
        seconds = float(self.params.get("seconds") or self.params.get("duration", 1.0))
        start = time.time()
        
        while time.time() - start < seconds:
            if context.is_cancelled():
                return ActionResult(success=False, message="Wait interrupted by user cancellation")
            time.sleep(0.1)

        return ActionResult(success=True, message=f"Waited {seconds} seconds.")


class WaitForWindowAction(BaseAction):
    """Wait until a window matching title_substring appears."""

    PARAM_SCHEMA = {
        "title": {"type": "string", "label": "Window Title Substring", "required": True},
        "timeout": {"type": "number", "label": "Timeout (seconds)", "default": 30.0},
    }

    def execute(self, context: AutomationContext) -> ActionResult:
        title = self.params.get("title")
        timeout = float(self.params.get("timeout", 30.0))

        if not title:
            return ActionResult(success=False, message="Window title required", error="Missing title")

        start = time.time()
        while time.time() - start < timeout:
            if context.is_cancelled():
                return ActionResult(success=False, message="Cancelled while waiting for window")
            
            hwnd = WindowManager.find_window(title)
            if hwnd:
                return ActionResult(success=True, message=f"Window matching '{title}' appeared (HWND={hwnd}).")
            time.sleep(0.5)

        return ActionResult(success=False, message=f"Timed out waiting for window '{title}' ({timeout}s)", error="Timeout")


class WaitForFileAction(BaseAction):
    """Wait until a file path exists."""

    PARAM_SCHEMA = {
        "file_path": {"type": "string", "label": "File Path", "required": True},
        "timeout": {"type": "number", "label": "Timeout (seconds)", "default": 30.0},
    }

    def execute(self, context: AutomationContext) -> ActionResult:
        raw_path = self.params.get("file_path")
        timeout = float(self.params.get("timeout", 30.0))

        if not raw_path:
            return ActionResult(success=False, message="File path required", error="Missing parameter")

        target_path = os.path.expandvars(raw_path)
        start = time.time()
        
        while time.time() - start < timeout:
            if context.is_cancelled():
                return ActionResult(success=False, message="Cancelled while waiting for file")
            if os.path.exists(target_path):
                return ActionResult(success=True, message=f"File '{target_path}' is available.")
            time.sleep(0.5)

        return ActionResult(success=False, message=f"Timed out waiting for file '{target_path}'", error="Timeout")


# Register wait actions
action_registry.register("wait.duration", WaitDurationAction, category="Wait", display_name="Wait Duration")
action_registry.register("wait.for_window", WaitForWindowAction, category="Wait", display_name="Wait for Window")
action_registry.register("wait.for_file", WaitForFileAction, category="Wait", display_name="Wait for File")
