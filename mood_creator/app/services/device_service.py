import logging
from typing import List
from app.models.device import AudioDevice, MidiDevice
from app.windows.devices import DeviceManager

logger = logging.getLogger(__name__)


class DeviceService:
    """Service wrapper for peripheral device querying."""

    def __init__(self):
        self.dev_manager = DeviceManager()

    def get_audio_devices(self) -> List[AudioDevice]:
        return self.dev_manager.get_audio_devices("all")

    def get_midi_devices(self) -> List[MidiDevice]:
        return self.dev_manager.get_midi_devices()

    def check_device_ready(self, device_name_substring: str) -> bool:
        return self.dev_manager.check_device_exists(device_name_substring)
