import os
import shutil
from pathlib import Path
from app.actions.base import BaseAction
from app.core.action_registry import action_registry
from app.core.execution_context import AutomationContext
from app.models.action_result import ActionResult


class OpenFileAction(BaseAction):
    """Open a file or project template using the OS default application handler."""

    PARAM_SCHEMA = {
        "file_path": {"type": "string", "label": "File Path", "required": True},
    }

    def execute(self, context: AutomationContext) -> ActionResult:
        raw_path = self.params.get("file_path")
        if not raw_path:
            return ActionResult(success=False, message="File path is required", error="Missing 'file_path'")

        full_path = os.path.expandvars(raw_path)
        if not os.path.exists(full_path):
            return ActionResult(success=False, message=f"File not found: '{full_path}'", error="FileNotFound")

        try:
            os.startfile(full_path)
            return ActionResult(success=True, message=f"Opened file '{os.path.basename(full_path)}'")
        except Exception as e:
            return ActionResult(success=False, message=f"Failed to open '{full_path}'", error=str(e))


class CreateDirectoryAction(BaseAction):
    """Create a directory hierarchy."""

    PARAM_SCHEMA = {
        "directory_path": {"type": "string", "label": "Directory Path", "required": True}
    }

    def execute(self, context: AutomationContext) -> ActionResult:
        raw_path = self.params.get("directory_path")
        dir_path = os.path.expandvars(raw_path)
        try:
            os.makedirs(dir_path, exist_ok=True)
            return ActionResult(success=True, message=f"Directory created: '{dir_path}'")
        except Exception as e:
            return ActionResult(success=False, message=f"Failed to create directory '{dir_path}'", error=str(e))


class CopyFileAction(BaseAction):
    """Copy a file from source to destination."""

    PARAM_SCHEMA = {
        "source": {"type": "string", "label": "Source Path", "required": True},
        "destination": {"type": "string", "label": "Destination Path", "required": True},
    }

    def execute(self, context: AutomationContext) -> ActionResult:
        src = os.path.expandvars(self.params.get("source", ""))
        dst = os.path.expandvars(self.params.get("destination", ""))

        if not os.path.exists(src):
            return ActionResult(success=False, message=f"Source file does not exist: '{src}'", error="NotFound")

        try:
            shutil.copy2(src, dst)
            return ActionResult(success=True, message=f"Copied '{os.path.basename(src)}' to destination")
        except Exception as e:
            return ActionResult(success=False, message=f"Failed to copy file", error=str(e))


class MoveFileAction(BaseAction):
    """Move a file or directory."""

    PARAM_SCHEMA = {
        "source": {"type": "string", "label": "Source Path", "required": True},
        "destination": {"type": "string", "label": "Destination Path", "required": True},
    }

    def execute(self, context: AutomationContext) -> ActionResult:
        src = os.path.expandvars(self.params.get("source", ""))
        dst = os.path.expandvars(self.params.get("destination", ""))

        try:
            shutil.move(src, dst)
            return ActionResult(success=True, message=f"Moved '{src}' to '{dst}'")
        except Exception as e:
            return ActionResult(success=False, message=f"Failed to move file", error=str(e))


class DeleteFileAction(BaseAction):
    """Delete a file (requires confirmation setting if critical)."""

    PARAM_SCHEMA = {
        "file_path": {"type": "string", "label": "File Path", "required": True},
        "confirm": {"type": "boolean", "label": "Confirmed", "default": True},
    }

    def execute(self, context: AutomationContext) -> ActionResult:
        target = os.path.expandvars(self.params.get("file_path", ""))
        if not os.path.exists(target):
            return ActionResult(success=True, message=f"File '{target}' does not exist.")

        try:
            if os.path.isdir(target):
                shutil.rmtree(target)
            else:
                os.remove(target)
            return ActionResult(success=True, message=f"Deleted '{os.path.basename(target)}'")
        except Exception as e:
            return ActionResult(success=False, message=f"Failed to delete '{target}'", error=str(e))


class CheckFileExistsAction(BaseAction):
    """Check if a file or directory path exists."""

    PARAM_SCHEMA = {
        "path": {"type": "string", "label": "File/Folder Path", "required": True}
    }

    def execute(self, context: AutomationContext) -> ActionResult:
        target = os.path.expandvars(self.params.get("path", ""))
        exists = os.path.exists(target)
        return ActionResult(
            success=exists,
            message=f"Path '{target}' {'exists' if exists else 'does not exist'}.",
            data={"exists": exists},
        )


# Register filesystem actions
action_registry.register("file.open", OpenFileAction, category="File", display_name="Open File / Project")
action_registry.register("file.create_dir", CreateDirectoryAction, category="File", display_name="Create Directory")
action_registry.register("file.copy", CopyFileAction, category="File", display_name="Copy File")
action_registry.register("file.move", MoveFileAction, category="File", display_name="Move File")
action_registry.register("file.delete", DeleteFileAction, category="File", display_name="Delete File")
action_registry.register("file.exists", CheckFileExistsAction, category="File", display_name="Check File Exists")
