from app.actions.base import BaseAction
from app.core.action_registry import action_registry
from app.core.execution_context import AutomationContext
from app.models.action_result import ActionResult
from app.windows.audio import AudioManager


class DetectAudioDeviceAction(BaseAction):
    """Detect whether a specified audio interface or device is connected."""

    PARAM_SCHEMA = {
        "device": {"type": "string", "label": "Device Name Substring (e.g. Scarlett 2i2)", "required": True}
    }

    def execute(self, context: AutomationContext) -> ActionResult:
        device_name = self.params.get("device") or self.params.get("device_name")
        if not device_name:
            return ActionResult(success=False, message="Device name target is required", error="Missing device")

        connected = AudioManager.is_device_connected(device_name)
        if connected:
            return ActionResult(
                success=True,
                message=f"Audio device '{device_name}' detected and connected.",
                data={"device": device_name, "connected": True},
            )
        else:
            return ActionResult(
                success=False,
                message=f"Audio device '{device_name}' was not detected on system.",
                error=f"Device '{device_name}' disconnected or missing",
                data={"device": device_name, "connected": False},
            )


class SetAudioInputAction(BaseAction):
    """Set the active default system audio recording / input device."""

    PARAM_SCHEMA = {
        "device": {"type": "string", "label": "Input Device Name", "required": True}
    }

    def execute(self, context: AutomationContext) -> ActionResult:
        device_name = self.params.get("device")
        if not device_name:
            return ActionResult(success=False, message="Input device target required", error="Missing parameter")

        ok = AudioManager.set_default_device(device_name, device_type="input")
        if ok:
            return ActionResult(success=True, message=f"Audio input configured to '{device_name}'")
        return ActionResult(success=False, message=f"Failed to set audio input to '{device_name}'", error="Configuration error")


class SetAudioOutputAction(BaseAction):
    """Set the active default system playback / output device."""

    PARAM_SCHEMA = {
        "device": {"type": "string", "label": "Output Device Name", "required": True}
    }

    def execute(self, context: AutomationContext) -> ActionResult:
        device_name = self.params.get("device")
        if not device_name:
            return ActionResult(success=False, message="Output device target required", error="Missing parameter")

        ok = AudioManager.set_default_device(device_name, device_type="output")
        if ok:
            return ActionResult(success=True, message=f"Audio output configured to '{device_name}'")
        return ActionResult(success=False, message=f"Failed to set audio output to '{device_name}'", error="Configuration error")


# Register audio actions
action_registry.register("audio.detect_device", DetectAudioDeviceAction, category="Audio", display_name="Detect Audio Device")
action_registry.register("audio.set_input", SetAudioInputAction, category="Audio", display_name="Set Audio Input")
action_registry.register("audio.set_output", SetAudioOutputAction, category="Audio", display_name="Set Audio Output")
