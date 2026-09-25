from app.actions.base import BaseAction
from app.core.action_registry import action_registry
from app.core.execution_context import AutomationContext
from app.models.action_result import ActionResult
from app.windows.windows import WindowManager


class FocusWindowAction(BaseAction):
    """Bring a matching application window to front and set focus."""

    PARAM_SCHEMA = {
        "title": {
            "type": "string",
            "label": "Window Title or App Name",
            "required": False,
            "default": "",
            "placeholder": "e.g. VLC, Notepad, Chrome (leave blank for last launched app)",
        },
        "timeout": {
            "type": "number",
            "label": "Wait Timeout (seconds)",
            "required": False,
            "default": 5,
        },
    }

    def execute(self, context: AutomationContext) -> ActionResult:
        title = self.params.get("title") or self.params.get("window_title")
        timeout = float(self.params.get("timeout", 5.0))

        ok = WindowManager.focus_window(title, timeout=timeout, context=context)
        target_name = f"'{title}'" if title else "active / last launched application"
        if ok:
            return ActionResult(success=True, message=f"Focused window for {target_name}")
        return ActionResult(
            success=False,
            message=f"Could not find or focus window for {target_name} (waited {timeout}s).",
            error="WindowNotFound",
        )


class MinimizeWindowAction(BaseAction):
    """Minimize a matching window."""

    PARAM_SCHEMA = {
        "title": {
            "type": "string",
            "label": "Window Title or App Name",
            "required": False,
            "default": "",
            "placeholder": "e.g. VLC, Notepad, Chrome (leave blank for last launched app)",
        },
        "timeout": {
            "type": "number",
            "label": "Wait Timeout (seconds)",
            "required": False,
            "default": 5,
        },
    }

    def execute(self, context: AutomationContext) -> ActionResult:
        title = self.params.get("title") or self.params.get("window_title")
        timeout = float(self.params.get("timeout", 5.0))

        ok = WindowManager.minimize_window(title, timeout=timeout, context=context)
        target_name = f"'{title}'" if title else "active / last launched application"
        if ok:
            return ActionResult(success=True, message=f"Minimized window for {target_name}")
        return ActionResult(
            success=False,
            message=f"Window for {target_name} not found or could not minimize (waited {timeout}s).",
            error="WindowNotFound",
        )


class MaximizeWindowAction(BaseAction):
    """Maximize a matching window."""

    PARAM_SCHEMA = {
        "title": {
            "type": "string",
            "label": "Window Title or App Name",
            "required": False,
            "default": "",
            "placeholder": "e.g. VLC, Notepad, Chrome (leave blank for last launched app)",
        },
        "timeout": {
            "type": "number",
            "label": "Wait Timeout (seconds)",
            "required": False,
            "default": 5,
        },
    }

    def execute(self, context: AutomationContext) -> ActionResult:
        title = self.params.get("title") or self.params.get("window_title")
        timeout = float(self.params.get("timeout", 5.0))

        ok = WindowManager.maximize_window(title, timeout=timeout, context=context)
        target_name = f"'{title}'" if title else "active / last launched application"
        if ok:
            return ActionResult(success=True, message=f"Maximized window for {target_name}")
        return ActionResult(
            success=False,
            message=f"Window for {target_name} not found or could not maximize (waited {timeout}s).",
            error="WindowNotFound",
        )


class MoveResizeWindowAction(BaseAction):
    """Reposition and resize a window."""

    PARAM_SCHEMA = {
        "title": {
            "type": "string",
            "label": "Window Title or App Name",
            "required": False,
            "default": "",
            "placeholder": "e.g. VLC, Notepad, Chrome (leave blank for last launched app)",
        },
        "timeout": {
            "type": "number",
            "label": "Wait Timeout (seconds)",
            "required": False,
            "default": 5,
        },
        "x": {"type": "number", "label": "X Position", "default": 0},
        "y": {"type": "number", "label": "Y Position", "default": 0},
        "width": {"type": "number", "label": "Width", "default": 1280},
        "height": {"type": "number", "label": "Height", "default": 720},
    }

    def execute(self, context: AutomationContext) -> ActionResult:
        title = self.params.get("title") or self.params.get("window_title")
        timeout = float(self.params.get("timeout", 5.0))
        x = int(self.params.get("x", 0))
        y = int(self.params.get("y", 0))
        w = int(self.params.get("width", 1280))
        h = int(self.params.get("height", 720))

        ok = WindowManager.move_resize_window(title, x, y, w, h, timeout=timeout, context=context)
        target_name = f"'{title}'" if title else "active / last launched application"
        if ok:
            return ActionResult(success=True, message=f"Resized window for {target_name} to {w}x{h} at ({x},{y})")
        return ActionResult(
            success=False,
            message=f"Window for {target_name} not found or could not resize (waited {timeout}s).",
            error="WindowNotFound",
        )


class ToggleFullscreenAction(BaseAction):
    """Toggle fullscreen mode (F11 / Alt+Enter) for a window."""

    PARAM_SCHEMA = {
        "title": {
            "type": "string",
            "label": "Window Title or App Name",
            "required": False,
            "default": "",
            "placeholder": "e.g. Brave, Chrome, VLC (or leave blank for active/last launched)",
        },
        "key": {
            "type": "string",
            "label": "Fullscreen Key",
            "default": "F11",
            "placeholder": "F11 (browsers) or ALT+ENTER (games/media)",
        },
        "delay_before": {
            "type": "number",
            "label": "Delay Before Keypress (sec)",
            "default": 0.5,
        },
        "timeout": {
            "type": "number",
            "label": "Wait Timeout (seconds)",
            "default": 5,
        },
    }

    def execute(self, context: AutomationContext) -> ActionResult:
        import time
        import win32api
        import win32con
        from app.windows.hotkeys import VK_MAP

        title = self.params.get("title") or self.params.get("window_title")
        key_str = str(self.params.get("key", "F11")).upper().strip()
        delay_before = float(self.params.get("delay_before", 0.5))
        timeout = float(self.params.get("timeout", 5.0))

        # Focus target window first
        ok = WindowManager.focus_window(title, timeout=timeout, context=context)
        target_name = f"'{title}'" if title else "active / last launched application"
        if not ok:
            return ActionResult(
                success=False,
                message=f"Window for {target_name} not found or could not focus (waited {timeout}s).",
                error="WindowNotFound",
            )

        if delay_before > 0:
            start_wait = time.time()
            while time.time() - start_wait < delay_before:
                if context.is_cancelled():
                    return ActionResult(success=False, message="Fullscreen action cancelled")
                time.sleep(0.05)

        parts = [p.strip() for p in key_str.split("+")]
        mod_vks = []
        key_vk = None

        for part in parts:
            if part in ["ALT", "MENU"]:
                mod_vks.append(win32con.VK_MENU)
            elif part in ["CTRL", "CONTROL"]:
                mod_vks.append(win32con.VK_CONTROL)
            elif part in ["SHIFT"]:
                mod_vks.append(win32con.VK_SHIFT)
            elif part in VK_MAP:
                key_vk = VK_MAP[part]
            elif len(part) == 1:
                key_vk = ord(part)

        if not key_vk:
            key_vk = getattr(win32con, "VK_F11", 0x7A)

        try:
            for mod in mod_vks:
                m_scan = win32api.MapVirtualKey(mod, 0)
                win32api.keybd_event(mod, m_scan, 0, 0)

            k_scan = win32api.MapVirtualKey(key_vk, 0)
            win32api.keybd_event(key_vk, k_scan, 0, 0)
            time.sleep(0.08)
            win32api.keybd_event(key_vk, k_scan, win32con.KEYEVENTF_KEYUP, 0)

            for mod in reversed(mod_vks):
                m_scan = win32api.MapVirtualKey(mod, 0)
                win32api.keybd_event(mod, m_scan, win32con.KEYEVENTF_KEYUP, 0)

            return ActionResult(success=True, message=f"Toggled fullscreen ({key_str}) for {target_name}")
        except Exception as e:
            return ActionResult(success=False, message=f"Failed to toggle fullscreen: {e}", error=str(e))


class SetWallpaperAction(BaseAction):
    """Set the Windows desktop background wallpaper."""

    PARAM_SCHEMA = {
        "image_path": {
            "type": "string",
            "label": "Wallpaper Image Path",
            "required": True,
            "placeholder": "e.g. C:/Wallpapers/wallpaper.jpg",
        },
    }

    def execute(self, context: AutomationContext) -> ActionResult:
        import ctypes
        import os
        from pathlib import Path
        img = self.params.get("image_path", "")
        p = Path(img)
        if not p.is_file():
            user_bg_dir = Path(os.environ.get("APPDATA", ".")) / "AutomationHub" / "backgrounds"
            up = user_bg_dir / img
            if up.is_file():
                p = up
            else:
                return ActionResult(success=False, message=f"Wallpaper image not found: {img}", error="FileNotFound")

        try:
            SPI_SETDESKWALLPAPER = 20
            SPIF_UPDATEINIFILE = 1
            SPIF_SENDCHANGE = 2
            res = ctypes.windll.user32.SystemParametersInfoW(
                SPI_SETDESKWALLPAPER, 0, str(p.resolve()), SPIF_UPDATEINIFILE | SPIF_SENDCHANGE
            )
            if res:
                return ActionResult(success=True, message=f"Desktop wallpaper updated to: {p.name}")
            return ActionResult(success=False, message="SystemParametersInfoW failed to set wallpaper.", error="Win32Error")
        except Exception as e:
            return ActionResult(success=False, message=f"Error setting wallpaper: {e}", error=str(e))


# Register window actions
action_registry.register("window.focus", FocusWindowAction, category="Window", display_name="Focus Window")
action_registry.register("window.minimize", MinimizeWindowAction, category="Window", display_name="Minimize Window")
action_registry.register("window.maximize", MaximizeWindowAction, category="Window", display_name="Maximize Window")
action_registry.register("window.fullscreen", ToggleFullscreenAction, category="Window", display_name="Toggle Fullscreen (F11)")
action_registry.register("window.move", MoveResizeWindowAction, category="Window", display_name="Move / Resize Window")
action_registry.register("windows.set_wallpaper", SetWallpaperAction, category="Window", display_name="Set Desktop Wallpaper")


