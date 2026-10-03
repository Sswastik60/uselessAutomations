"""Application settings model and JSON persistent storage."""

import json
from dataclasses import dataclass, asdict, fields
from pathlib import Path
from typing import Optional


@dataclass
class AppSettings:
    """Configuration options for HackFill automation and behavior."""
    browser: str = "Brave"  # "Chromium", "Brave", "Chrome", "Edge", "Custom"
    custom_browser_path: str = ""
    browser_visible: bool = True
    timeout_seconds: int = 30
    max_pages: int = 30
    require_confirmation_before_submit: bool = True
    pause_on_uncertain_fields: bool = False
    pause_on_captcha: bool = True
    logging_enabled: bool = True
    
    # Auto-Pilot (Zero-Click) Automation Controls
    auto_pilot_mode: bool = True
    auto_check_checkboxes: bool = True
    auto_advance_pages: bool = True
    smart_fallback_for_unknown: bool = True
    auto_submit_final: bool = False

    # Already-Running Browser & CDP Controls
    connect_to_existing_browser: bool = True
    cdp_port: int = 9222
    auto_restart_browser_with_debugging: bool = True

    last_profile_path: str = ""
    last_url: str = ""


class SettingsManager:
    """Manages loading, updating, and saving AppSettings."""
    def __init__(self, settings_file: Optional[Path] = None):
        self.settings_file = settings_file or Path("settings.json")
        self.settings = self.load()

    def load(self) -> AppSettings:
        """Load settings from JSON file or return defaults."""
        if self.settings_file.exists():
            try:
                with open(self.settings_file, "r", encoding="utf-8") as f:
                    data = json.load(f)
                    valid_keys = {f.name for f in fields(AppSettings)}
                    filtered_data = {k: v for k, v in data.items() if k in valid_keys}
                    return AppSettings(**filtered_data)
            except Exception:
                return AppSettings()
        return AppSettings()

    def save(self) -> bool:
        """Persist current settings to JSON file."""
        try:
            with open(self.settings_file, "w", encoding="utf-8") as f:
                json.dump(asdict(self.settings), f, indent=2)
            return True
        except Exception:
            return False

    def update(self, **kwargs) -> bool:
        """Update specific settings attributes and save."""
        for key, value in kwargs.items():
            if hasattr(self.settings, key):
                setattr(self.settings, key, value)
        return self.save()
