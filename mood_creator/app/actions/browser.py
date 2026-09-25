import logging
import os
import shutil
import time
import webbrowser
from typing import Optional

from app.actions.base import BaseAction
from app.core.action_registry import action_registry
from app.core.execution_context import AutomationContext
from app.models.action_result import ActionResult
from app.windows.processes import ProcessManager
from app.windows.windows import WindowManager

logger = logging.getLogger(__name__)


class OpenUrlAction(BaseAction):
    """Open a website/URL in a browser with optional automatic full screen."""

    PARAM_SCHEMA = {
        "url": {
            "type": "string",
            "label": "Website URL",
            "required": True,
            "placeholder": "e.g. https://www.youtube.com, https://netflix.com, https://twitch.tv",
        },
        "browser": {
            "type": "string",
            "label": "Browser (optional)",
            "required": False,
            "default": "",
            "placeholder": "e.g. brave, chrome, edge, or leave blank for system default",
        },
        "fullscreen": {
            "type": "boolean",
            "label": "Full Screen (F11)",
            "required": False,
            "default": False,
        },
        "delay_before_fullscreen": {
            "type": "number",
            "label": "Delay Before Fullscreen (sec)",
            "required": False,
            "default": 1.5,
        },
    }

    def execute(self, context: AutomationContext) -> ActionResult:
        raw_url = str(self.params.get("url", "")).strip()
        browser_choice = str(self.params.get("browser", "")).strip()
        fullscreen = bool(self.params.get("fullscreen", False))
        delay_before_fullscreen = float(self.params.get("delay_before_fullscreen", 1.5))

        if not raw_url:
            return ActionResult(success=False, message="Website URL is required", error="MissingUrl")

        # Ensure scheme
        url = raw_url
        if not (url.startswith("http://") or url.startswith("https://") or url.startswith("file://")):
            url = f"https://{url}"

        browser_name = browser_choice.lower().removesuffix(".exe") if browser_choice else ""
        browser_exe: Optional[str] = None

        if browser_name:
            # 1. User configured settings
            settings = context.get_service("settings")
            if settings and hasattr(settings, "app_paths") and browser_name in settings.app_paths:
                browser_exe = settings.app_paths[browser_name]

            # 2. Auto-discovery
            if not browser_exe or not os.path.exists(browser_exe):
                browser_exe = ProcessManager.auto_discover_app_path(browser_name)

            # 3. PATH lookup
            if not browser_exe or not os.path.exists(browser_exe):
                browser_exe = shutil.which(browser_name) or shutil.which(f"{browser_name}.exe")

        try:
            if browser_exe and os.path.exists(browser_exe):
                proc = ProcessManager.launch_process(browser_exe, [url])
                pid = proc.pid if proc else None
                context.set_variable("last_launched_pid", pid)
                context.set_variable("last_launched_name", os.path.basename(browser_exe))
                context.set_variable("last_launched_path", browser_exe)
                context.set_variable("last_launched_app", browser_name)
            else:
                webbrowser.open(url)
                context.set_variable("last_launched_name", browser_name or "browser")
                context.set_variable("last_launched_app", browser_name or "browser")

            # Handle automatic fullscreen if requested
            if fullscreen:
                target_search = browser_name or None
                time.sleep(delay_before_fullscreen)
                hwnd = WindowManager.find_window(target_search, timeout=5.0, context=context)
                if hwnd:
                    WindowManager.focus_window(hwnd, timeout=2.0)
                    time.sleep(0.3)
                    import win32api
                    import win32con
                    vk = getattr(win32con, "VK_F11", 0x7A)
                    scan = win32api.MapVirtualKey(vk, 0)
                    win32api.keybd_event(vk, scan, 0, 0)
                    time.sleep(0.08)
                    win32api.keybd_event(vk, scan, win32con.KEYEVENTF_KEYUP, 0)

            fs_msg = " in Full Screen (F11)" if fullscreen else ""
            b_msg = f" in {browser_name.title()}" if browser_name else ""
            return ActionResult(success=True, message=f"Opened website '{raw_url}'{b_msg}{fs_msg}")
        except Exception as e:
            logger.error(f"Failed to open URL '{url}': {e}")
            return ActionResult(success=False, message=f"Failed to open website '{raw_url}'", error=str(e))


# Register browser action
action_registry.register("browser.open_url", OpenUrlAction, category="Process", display_name="Open Website / URL")
