from dataclasses import dataclass
from typing import Literal


@dataclass
class AudioDevice:
    """Represents a system audio interface or output/input device."""

    id: str
    name: str
    device_type: Literal["input", "output"]
    is_default: bool = False
    is_connected: bool = True
    channels: int = 2
    sample_rate: int = 44100


@dataclass
class MidiDevice:
    """Represents a connected MIDI input or output device."""

    id: str
    name: str
    device_type: Literal["input", "output"]
    is_connected: bool = True
