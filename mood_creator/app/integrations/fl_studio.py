import os
from typing import Optional
from app.integrations.base import ApplicationAdapter
from app.models.action_result import ActionResult
from app.windows.processes import ProcessManager
from app.windows.windows import WindowManager


class FLStudioAdapter(ApplicationAdapter):
    """Adapter for Image-Line FL Studio digital audio workstation."""

    @property
    def app_key(self) -> str:
        return "fl_studio"

    @property
    def display_name(self) -> str:
        return "FL Studio"

    def get_executable_path(self) -> Optional[str]:
        return ProcessManager.auto_discover_app_path("fl_studio")

    def is_installed(self) -> bool:
        path = self.get_executable_path()
        return path is not None and os.path.exists(path)

    def is_running(self) -> bool:
        return ProcessManager.is_process_running("FL64.exe") or ProcessManager.is_process_running("FL.exe")

    def launch(self, extra_args: Optional[list] = None) -> ActionResult:
        exec_path = self.get_executable_path()
        if not exec_path:
            return ActionResult(
                success=False,
                message="FL Studio executable was not found.",
                error="PathNotConfigured",
            )

        try:
            ProcessManager.launch_process(exec_path, arguments=extra_args)
            return ActionResult(success=True, message="FL Studio launched successfully.")
        except Exception as e:
            return ActionResult(success=False, message="Failed to launch FL Studio", error=str(e))

    def open_project(self, project_path: str) -> ActionResult:
        """Launch FL Studio opening a specified project/template file."""
        exec_path = self.get_executable_path()
        resolved_proj = os.path.expandvars(project_path)

        if not os.path.exists(resolved_proj):
            return ActionResult(
                success=False,
                message=f"FL Studio project file '{resolved_proj}' not found.",
                error="ProjectNotFound",
            )

        if exec_path and os.path.exists(exec_path):
            ProcessManager.launch_process(exec_path, arguments=[resolved_proj])
            return ActionResult(success=True, message=f"Opening FL Studio project '{os.path.basename(resolved_proj)}'")
        else:
            # Fallback to startfile
            os.startfile(resolved_proj)
            return ActionResult(success=True, message=f"Opening project '{os.path.basename(resolved_proj)}' with default handler")

    def wait_until_ready(self, timeout: float = 30.0) -> bool:
        """Wait until FL Studio main window or process is ready."""
        start = ProcessManager.wait_for_process("FL64.exe", timeout=timeout)
        if start:
            WindowManager.wait_for_window("FL Studio", timeout=10.0)
            return True
        return False

    def focus(self) -> ActionResult:
        hwnd = WindowManager.find_window("FL Studio")
        if hwnd:
            WindowManager.focus_window(hwnd)
            return ActionResult(success=True, message="Focused FL Studio window")
        return ActionResult(success=False, message="FL Studio window not found")

    def close(self, force: bool = False) -> ActionResult:
        ok = ProcessManager.terminate_process("FL64.exe", force=force)
        return ActionResult(success=ok, message="Closed FL Studio" if ok else "FL Studio was not running")
