import os
from typing import Optional
from app.integrations.base import ApplicationAdapter
from app.models.action_result import ActionResult
from app.windows.processes import ProcessManager
from app.windows.windows import WindowManager


class SpotifyAdapter(ApplicationAdapter):
    """Adapter for Spotify Desktop Client."""

    @property
    def app_key(self) -> str:
        return "spotify"

    @property
    def display_name(self) -> str:
        return "Spotify"

    def is_installed(self) -> bool:
        return ProcessManager.auto_discover_app_path("spotify") is not None

    def is_running(self) -> bool:
        return ProcessManager.is_process_running("Spotify.exe")

    def launch(self, extra_args: Optional[list] = None) -> ActionResult:
        path = ProcessManager.auto_discover_app_path("spotify")
        if not path:
            return ActionResult(success=False, message="Spotify executable not found.", error="NotFound")
        ProcessManager.launch_process(path, arguments=extra_args)
        return ActionResult(success=True, message="Launched Spotify.")

    def focus(self) -> ActionResult:
        hwnd = WindowManager.find_window("Spotify")
        if hwnd:
            WindowManager.focus_window(hwnd)
            return ActionResult(success=True, message="Focused Spotify window")
        return ActionResult(success=False, message="Spotify window not found")

    def close(self, force: bool = False) -> ActionResult:
        ok = ProcessManager.terminate_process("Spotify.exe", force=force)
        return ActionResult(success=ok, message="Closed Spotify")
