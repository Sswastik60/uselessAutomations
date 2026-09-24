import os
from typing import Any, List
from app.actions.base import BaseAction
from app.core.action_registry import action_registry
from app.core.execution_context import AutomationContext
from app.models.action import ActionConfig
from app.models.action_result import ActionResult
from app.windows.devices import DeviceManager
from app.windows.processes import ProcessManager


class DeviceExistsConditionAction(BaseAction):
    """Conditional branch: check if hardware device is connected."""

    PARAM_SCHEMA = {
        "device": {"type": "string", "label": "Device Name Substring", "required": True},
        "then_actions": {"type": "list", "label": "Actions if True", "required": False},
        "else_actions": {"type": "list", "label": "Actions if False", "required": False},
    }

    def execute(self, context: AutomationContext) -> ActionResult:
        device_name = self.params.get("device")
        dev_mgr = context.get_service("device_manager") or DeviceManager()
        exists = dev_mgr.check_device_exists(device_name)

        target_actions = self.params.get("then_actions" if exists else "else_actions", [])
        self._execute_sub_actions(target_actions, context)

        return ActionResult(
            success=True,
            message=f"Condition 'device_exists({device_name})' evaluated to {exists}",
            data={"condition_met": exists},
        )

    def _execute_sub_actions(self, action_dicts: List[dict], context: AutomationContext) -> None:
        for act_dict in action_dicts:
            if context.is_cancelled():
                break
            try:
                cfg = ActionConfig.model_validate(act_dict)
                action_obj = action_registry.create_action(cfg.type, cfg.params)
                action_obj.execute(context)
            except Exception as e:
                context.logger.error(f"Error in conditional sub-action: {e}")


class ProcessRunningConditionAction(BaseAction):
    """Conditional branch: check if process is running."""

    PARAM_SCHEMA = {
        "process_name": {"type": "string", "label": "Process Name", "required": True}
    }

    def execute(self, context: AutomationContext) -> ActionResult:
        proc_name = self.params.get("process_name")
        running = ProcessManager.is_process_running(proc_name)
        return ActionResult(
            success=running,
            message=f"Condition 'process_running({proc_name})' evaluated to {running}",
            data={"condition_met": running},
        )


class FileExistsConditionAction(BaseAction):
    """Conditional branch: check if file or path exists."""

    PARAM_SCHEMA = {
        "file_path": {"type": "string", "label": "File Path", "required": True}
    }

    def execute(self, context: AutomationContext) -> ActionResult:
        target = os.path.expandvars(self.params.get("file_path", ""))
        exists = os.path.exists(target)
        return ActionResult(
            success=exists,
            message=f"Condition 'file_exists({target})' evaluated to {exists}",
            data={"condition_met": exists},
        )


class EnvVarExistsConditionAction(BaseAction):
    """Conditional branch: check if environment variable exists."""

    PARAM_SCHEMA = {
        "variable_name": {"type": "string", "label": "Environment Variable Name", "required": True}
    }

    def execute(self, context: AutomationContext) -> ActionResult:
        var_name = self.params.get("variable_name", "")
        exists = var_name in os.environ
        val = os.environ.get(var_name)
        return ActionResult(
            success=exists,
            message=f"Environment variable '{var_name}' {'exists' if exists else 'missing'}.",
            data={"condition_met": exists, "value": val},
        )


# Register conditional actions
action_registry.register("condition.device_exists", DeviceExistsConditionAction, category="Condition", display_name="IF Device Exists")
action_registry.register("condition.process_running", ProcessRunningConditionAction, category="Condition", display_name="IF Process Running")
action_registry.register("condition.file_exists", FileExistsConditionAction, category="Condition", display_name="IF File Exists")
action_registry.register("condition.env_exists", EnvVarExistsConditionAction, category="Condition", display_name="IF Environment Variable Exists")
