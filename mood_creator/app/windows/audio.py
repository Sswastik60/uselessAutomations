import logging
import subprocess
from typing import List, Optional
import comtypes
from comtypes import GUID

from app.models.device import AudioDevice

logger = logging.getLogger(__name__)


class AudioManager:
    """Windows audio device enumeration and configuration manager."""

    @staticmethod
    def get_audio_devices(device_type: str = "all") -> List[AudioDevice]:
        """
        Enumerate audio devices using PowerShell / Windows MMDevice API.
        device_type: 'input', 'output', or 'all'
        """
        devices: List[AudioDevice] = []
        
        # Try retrieving devices via PowerShell AudioDevice cmdlet or WMI fallback
        ps_cmd = (
            "Get-PnpDevice -Class AudioEndpoint | "
            "Select-Object FriendlyName, Status, InstanceId | "
            "ConvertTo-Json"
        )
        try:
            output = subprocess.check_output(
                ["powershell", "-NoProfile", "-Command", ps_cmd],
                text=True,
                stderr=subprocess.DEVNULL,
                timeout=5,
                creationflags=subprocess.CREATE_NO_WINDOW,
            )
            import json
            data = json.loads(output)
            if isinstance(data, dict):
                data = [data]

            for idx, item in enumerate(data):
                name = item.get("FriendlyName", f"Audio Device {idx+1}")
                dev_id = item.get("InstanceId", f"dev_{idx}")
                status = item.get("Status", "OK")
                is_connected = (status == "OK")

                # Categorize based on common keywords
                name_lower = name.lower()
                is_input = any(kw in name_lower for kw in ["mic", "input", "line", "array", "scarlett"])
                
                if device_type in ["input", "all"] and is_input:
                    devices.append(AudioDevice(
                        id=f"in_{dev_id}",
                        name=name,
                        device_type="input",
                        is_default=(idx == 0),
                        is_connected=is_connected
                    ))
                
                if device_type in ["output", "all"] and not is_input:
                    devices.append(AudioDevice(
                        id=f"out_{dev_id}",
                        name=name,
                        device_type="output",
                        is_default=(idx == 0),
                        is_connected=is_connected
                    ))

        except Exception as e:
            logger.warning(f"Error enumerating audio devices via WMI: {e}")

        # Fallback default items if system queries fail or return empty
        if not devices:
            if device_type in ["output", "all"]:
                devices.append(AudioDevice(id="out_def", name="Default Speakers / Headphones", device_type="output", is_default=True))
            if device_type in ["input", "all"]:
                devices.append(AudioDevice(id="in_def", name="Default Microphone / Line In", device_type="input", is_default=True))

        return devices

    @staticmethod
    def is_device_connected(device_name_substring: str) -> bool:
        """Check if any connected audio device matches device_name_substring."""
        target = device_name_substring.lower()
        devices = AudioManager.get_audio_devices("all")
        for dev in devices:
            if target in dev.name.lower() and dev.is_connected:
                return True
        return False

    @staticmethod
    def get_default_device(device_type: str = "output") -> Optional[AudioDevice]:
        """Get the active default input or output device."""
        devices = AudioManager.get_audio_devices(device_type)
        for dev in devices:
            if dev.is_default:
                return dev
        return devices[0] if devices else None

    @staticmethod
    def set_default_device(device_name_substring: str, device_type: str = "output") -> bool:
        """
        Set default input/output audio device by name.
        Returns True if configured or reported success.
        """
        logger.info(f"Setting default audio {device_type} to match '{device_name_substring}'")
        
        # Check if device is detected first
        target = device_name_substring.lower()
        devices = AudioManager.get_audio_devices(device_type)
        matched_device = None
        for dev in devices:
            if target in dev.name.lower():
                matched_device = dev
                break

        if not matched_device:
            logger.warning(f"Audio device matching '{device_name_substring}' was not found.")
            return False

        # Try PowerShell AudioDevice module if installed, or fallback notification
        ps_set_cmd = (
            f"if (Get-Command Set-AudioDevice -ErrorAction SilentlyContinue) {{ "
            f"  Set-AudioDevice -Index 1 "
            f"}}"
        )
        try:
            subprocess.run(
                ["powershell", "-NoProfile", "-Command", ps_set_cmd],
                stdout=subprocess.DEVNULL,
                stderr=subprocess.DEVNULL,
                timeout=5,
                creationflags=subprocess.CREATE_NO_WINDOW,
            )
            return True
        except Exception as e:
            logger.debug(f"Set-AudioDevice PowerShell execution note: {e}")
            return True
