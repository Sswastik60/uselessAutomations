from typing import Optional
from app.integrations.base import ApplicationAdapter
from app.models.action_result import ActionResult
from app.windows.processes import ProcessManager
from app.windows.windows import WindowManager


class DiscordAdapter(ApplicationAdapter):
    """Adapter for Discord Desktop Client."""

    @property
    def app_key(self) -> str:
        return "discord"

    @property
    def display_name(self) -> str:
        return "Discord"

    def is_installed(self) -> bool:
        return ProcessManager.auto_discover_app_path("discord") is not None

    def is_running(self) -> bool:
        return ProcessManager.is_process_running("Discord.exe")

    def launch(self, extra_args: Optional[list] = None) -> ActionResult:
        path = ProcessManager.auto_discover_app_path("discord")
        if not path:
            return ActionResult(success=False, message="Discord executable not found.", error="NotFound")
        ProcessManager.launch_process(path, arguments=extra_args)
        return ActionResult(success=True, message="Launched Discord.")

    def focus(self) -> ActionResult:
        hwnd = WindowManager.find_window("Discord")
        if hwnd:
            WindowManager.focus_window(hwnd)
            return ActionResult(success=True, message="Focused Discord window")
        return ActionResult(success=False, message="Discord window not found")

    def close(self, force: bool = False) -> ActionResult:
        ok = ProcessManager.terminate_process("Discord.exe", force=force)
        return ActionResult(success=ok, message="Closed Discord")
