import os
import shutil
from typing import Any, List, Optional
from app.actions.base import BaseAction
from app.core.action_registry import action_registry
from app.core.execution_context import AutomationContext
from app.models.action_result import ActionResult
from app.windows.processes import ProcessManager


class LaunchProcessAction(BaseAction):
    """Launch an application executable or Windows shortcut."""

    PARAM_SCHEMA = {
        "application": {"type": "string", "label": "Application Name / Path / URI", "required": True},
        "arguments": {"type": "list", "label": "Arguments", "required": False},
        "working_dir": {"type": "string", "label": "Working Directory", "required": False},
    }

    def execute(self, context: AutomationContext) -> ActionResult:
        application = self.params.get("application") or self.params.get("executable_path")
        arguments = self.params.get("arguments", [])
        working_dir = self.params.get("working_dir")

        if not application:
            return ActionResult(success=False, message="No application path specified", error="Missing parameter 'application'")

        # If application is a protocol URI (e.g. steam://run/730 or discord://)
        if "://" in application:
            try:
                os.startfile(application)
                return ActionResult(success=True, message=f"Launched URI protocol '{application}'")
            except Exception as e:
                return ActionResult(success=False, message=f"Failed to launch URI '{application}'", error=str(e))

        app_path = application

        # 1. Check user settings configured paths first
        settings = context.get_service("settings")
        if settings and hasattr(settings, "app_paths") and application.lower() in settings.app_paths:
            cfg_path = settings.app_paths[application.lower()]
            if cfg_path and os.path.exists(cfg_path):
                app_path = cfg_path

        # 2. If not found directly, check auto-discovery, shutil.which
        if not os.path.exists(app_path):
            which_path = shutil.which(application)
            if which_path:
                app_path = which_path
            else:
                discovered = ProcessManager.auto_discover_app_path(application)
                if discovered:
                    app_path = discovered

        # Handle Windows shortcut (.lnk) files
        if app_path and app_path.lower().endswith(".lnk") and os.path.exists(app_path):
            try:
                os.startfile(app_path)
                return ActionResult(
                    success=True,
                    message=f"Launched shortcut '{os.path.basename(app_path)}'",
                    data={"path": app_path},
                )
            except Exception as e:
                return ActionResult(success=False, message=f"Failed to launch shortcut '{os.path.basename(app_path)}'", error=str(e))

        # Check if Discord Update.exe requires processStart
        if os.path.basename(app_path).lower() == "update.exe" and "discord" in application.lower():
            if not arguments:
                arguments = ["--processStart", "Discord.exe"]

        if not os.path.exists(app_path) and not shutil.which(app_path):
            # Protocol fallback attempt (e.g. steam://, discord://, spotify://, vscode://)
            app_lower = application.lower()
            protocols = {
                "steam": "steam://",
                "discord": "discord://",
                "spotify": "spotify://",
                "vscode": "vscode://",
                "code": "vscode://",
            }
            if app_lower in protocols:
                try:
                    os.startfile(protocols[app_lower])
                    return ActionResult(success=True, message=f"Launched {application} via system protocol handler ({protocols[app_lower]}).")
                except Exception as e:
                    logger.warning(f"Protocol fallback failed for {application}: {e}")

            return ActionResult(
                success=False,
                message=f"Executable or shortcut for '{application}' not found on system. Please set path in Settings.",
                error=f"Path '{app_path}' does not exist.",
            )

        try:
            proc = ProcessManager.launch_process(app_path, arguments, working_dir)
            pid = proc.pid if proc else None
            pid_str = f" (PID={pid})" if pid else ""
            return ActionResult(
                success=True,
                message=f"Launched '{os.path.basename(app_path)}'{pid_str}",
                data={"pid": pid, "path": app_path},
            )
        except Exception as e:
            return ActionResult(success=False, message=f"Failed to launch '{application}'", error=str(e))



class CloseProcessAction(BaseAction):
    """Close or terminate a running process."""

    PARAM_SCHEMA = {
        "process_name": {"type": "string", "label": "Process Name (e.g. Steam.exe, Discord.exe)", "required": True},
        "force": {"type": "boolean", "label": "Force Kill", "required": False, "default": False},
    }

    def execute(self, context: AutomationContext) -> ActionResult:
        process_name = self.params.get("process_name")
        force = self.params.get("force", False)

        if not process_name:
            return ActionResult(success=False, message="Process name required", error="Missing 'process_name'")

        if not ProcessManager.is_process_running(process_name):
            return ActionResult(success=True, message=f"Process '{process_name}' is not currently running.")

        success = ProcessManager.terminate_process(process_name, force=force)
        if success:
            return ActionResult(success=True, message=f"Terminated process '{process_name}'")
        return ActionResult(success=False, message=f"Failed to terminate process '{process_name}'", error="Access denied or timeout")


class RestartProcessAction(BaseAction):
    """Restart an application process."""

    PARAM_SCHEMA = {
        "process_name": {"type": "string", "label": "Process Name", "required": True},
        "application_path": {"type": "string", "label": "Application Path", "required": True},
    }

    def execute(self, context: AutomationContext) -> ActionResult:
        proc_name = self.params.get("process_name")
        app_path = self.params.get("application_path")

        if ProcessManager.is_process_running(proc_name):
            ProcessManager.terminate_process(proc_name)

        launch_act = LaunchProcessAction(application=app_path)
        return launch_act.execute(context)


class WaitForProcessAction(BaseAction):
    """Wait for a process to start and become active."""

    PARAM_SCHEMA = {
        "application": {"type": "string", "label": "Process Name / App Key", "required": True},
        "timeout": {"type": "number", "label": "Timeout (seconds)", "default": 30},
    }

    def execute(self, context: AutomationContext) -> ActionResult:
        app_name = self.params.get("application") or self.params.get("process_name")
        timeout = float(self.params.get("timeout", 30))

        if not app_name:
            return ActionResult(success=False, message="Application name required", error="Missing application")

        found = ProcessManager.wait_for_process(app_name, timeout=timeout)
        if found:
            return ActionResult(success=True, message=f"Process '{app_name}' is active.")
        return ActionResult(success=False, message=f"Timed out waiting for process '{app_name}' ({timeout}s)", error="Timeout")


class CheckProcessRunningAction(BaseAction):
    """Check whether a process is running."""

    PARAM_SCHEMA = {
        "process_name": {"type": "string", "label": "Process Name", "required": True}
    }

    def execute(self, context: AutomationContext) -> ActionResult:
        proc_name = self.params.get("process_name")
        is_running = ProcessManager.is_process_running(proc_name)
        return ActionResult(
            success=is_running,
            message=f"Process '{proc_name}' is {'running' if is_running else 'not running'}.",
            data={"is_running": is_running},
        )


# Register process actions
action_registry.register("process.launch", LaunchProcessAction, category="Process", display_name="Launch Application")
action_registry.register("process.close", CloseProcessAction, category="Process", display_name="Close Application")
action_registry.register("process.restart", RestartProcessAction, category="Process", display_name="Restart Application")
action_registry.register("process.wait_for", WaitForProcessAction, category="Process", display_name="Wait for Process")
action_registry.register("process.check", CheckProcessRunningAction, category="Process", display_name="Check Process Running")
