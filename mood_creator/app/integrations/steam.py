import os
from typing import Optional
from app.integrations.base import ApplicationAdapter
from app.models.action_result import ActionResult
from app.windows.processes import ProcessManager
from app.windows.windows import WindowManager


class SteamAdapter(ApplicationAdapter):
    """Adapter for Valve Steam client."""

    @property
    def app_key(self) -> str:
        return "steam"

    @property
    def display_name(self) -> str:
        return "Steam"

    def is_installed(self) -> bool:
        return ProcessManager.auto_discover_app_path("steam") is not None

    def is_running(self) -> bool:
        return ProcessManager.is_process_running("steam.exe")

    def launch(self, extra_args: Optional[list] = None) -> ActionResult:
        path = ProcessManager.auto_discover_app_path("steam")
        if not path:
            return ActionResult(success=False, message="Steam executable not found.", error="NotFound")
        ProcessManager.launch_process(path, arguments=extra_args)
        return ActionResult(success=True, message="Launched Steam client.")

    def launch_game(self, game_app_id: str) -> ActionResult:
        """Launch game by Steam AppID (e.g. 730 for CS:GO)."""
        uri = f"steam://run/{game_app_id}"
        os.startfile(uri)
        return ActionResult(success=True, message=f"Launched Steam Game (AppID={game_app_id})")

    def focus(self) -> ActionResult:
        hwnd = WindowManager.find_window("Steam")
        if hwnd:
            WindowManager.focus_window(hwnd)
            return ActionResult(success=True, message="Focused Steam window")
        return ActionResult(success=False, message="Steam window not found")

    def close(self, force: bool = False) -> ActionResult:
        ok = ProcessManager.terminate_process("steam.exe", force=force)
        return ActionResult(success=ok, message="Closed Steam")
