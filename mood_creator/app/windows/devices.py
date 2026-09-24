import logging
from typing import Dict, List
from app.models.device import AudioDevice, MidiDevice
from app.windows.audio import AudioManager

logger = logging.getLogger(__name__)


class DeviceManager:
    """Unified Hardware Device Enumerator for Audio, MIDI, and USB peripherals."""

    def __init__(self):
        self.audio_manager = AudioManager()

    def get_audio_devices(self, device_type: str = "all") -> List[AudioDevice]:
        """Return list of audio input/output devices."""
        return self.audio_manager.get_audio_devices(device_type)

    def get_midi_devices(self) -> List[MidiDevice]:
        """Return list of connected MIDI input/output devices."""
        devices: List[MidiDevice] = []
        try:
            import ctypes
            winmm = ctypes.windll.winmm
            
            num_in = winmm.midiInGetNumDevs()
            num_out = winmm.midiOutGetNumDevs()

            # Structure for midi caps
            class MIDIINCAPSW(ctypes.Structure):
                _fields_ = [
                    ("wMid", ctypes.c_ushort),
                    ("wPid", ctypes.c_ushort),
                    ("vDriverVersion", ctypes.c_uint),
                    ("szPname", ctypes.c_wchar * 32),
                    ("dwSupport", ctypes.c_uint),
                ]

            for i in range(num_in):
                caps = MIDIINCAPSW()
                if winmm.midiInGetDevCapsW(i, ctypes.byref(caps), ctypes.sizeof(caps)) == 0:
                    devices.append(MidiDevice(id=f"midi_in_{i}", name=caps.szPname, device_type="input"))

            for i in range(num_out):
                caps = MIDIINCAPSW()
                if winmm.midiOutGetDevCapsW(i, ctypes.byref(caps), ctypes.sizeof(caps)) == 0:
                    devices.append(MidiDevice(id=f"midi_out_{i}", name=caps.szPname, device_type="output"))

        except Exception as e:
            logger.warning(f"Error enumerating MIDI devices via winmm: {e}")

        if not devices:
            devices.append(MidiDevice(id="midi_default", name="Virtual MIDI / Keyboard", device_type="input"))

        return devices

    def check_device_exists(self, device_name_substring: str) -> bool:
        """Check if any audio or MIDI device matches target substring."""
        target = device_name_substring.lower()
        
        # 1. Check Audio
        for dev in self.get_audio_devices("all"):
            if target in dev.name.lower() and dev.is_connected:
                return True

        # 2. Check MIDI
        for dev in self.get_midi_devices():
            if target in dev.name.lower() and dev.is_connected:
                return True

        return False
