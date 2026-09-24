from app.actions.base import BaseAction
from app.core.action_registry import action_registry
from app.core.execution_context import AutomationContext
from app.models.action_result import ActionResult
from app.windows.devices import DeviceManager


class DetectMidiDeviceAction(BaseAction):
    """Detect whether a MIDI controller or keyboard is connected."""

    PARAM_SCHEMA = {
        "device": {"type": "string", "label": "MIDI Device Name", "required": True}
    }

    def execute(self, context: AutomationContext) -> ActionResult:
        device_name = self.params.get("device")
        if not device_name:
            return ActionResult(success=False, message="MIDI device name required", error="Missing device")

        dev_mgr = context.get_service("device_manager") or DeviceManager()
        midi_devices = dev_mgr.get_midi_devices()
        
        target = device_name.lower()
        for dev in midi_devices:
            if target in dev.name.lower() and dev.is_connected:
                return ActionResult(success=True, message=f"MIDI device '{dev.name}' detected.")

        return ActionResult(
            success=False,
            message=f"MIDI device matching '{device_name}' not detected.",
            error="MIDI Device Missing",
        )


# Register MIDI actions
action_registry.register("midi.detect_device", DetectMidiDeviceAction, category="MIDI", display_name="Detect MIDI Device")
