from typing import Optional
from pydantic import BaseModel, Field


class AppSettings(BaseModel):
    """Application-wide user settings."""

    start_with_windows: bool = Field(False, description="Launch Automation Hub on Windows boot")
    minimize_to_tray: bool = Field(False, description="Minimize window to system tray when closed")
    launch_minimized: bool = Field(False, description="Start application hidden in system tray")

    notifications_enabled: bool = Field(True, description="Show Windows OS desktop notifications")
    dark_mode: bool = Field(True, description="Use dark theme aesthetic")
    reduce_motion: bool = Field(False, description="Reduce motion animations for accessibility")
    log_level: str = Field("INFO", description="Logging output level (DEBUG, INFO, WARNING, ERROR)")
    
    # Audio defaults
    preferred_input_device: Optional[str] = Field(None, description="Default audio input device filter")
    preferred_output_device: Optional[str] = Field(None, description="Default audio output device filter")
    
    # Executable path overrides for application adapters
    app_paths: dict[str, str] = Field(
        default_factory=dict, 
        description="Map of application keys (e.g. 'fl_studio') to executable paths"
    )

    def to_dict(self) -> dict:
        return self.model_dump(mode="json")
