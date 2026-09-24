import json
import logging
from pathlib import Path
from app.models.settings import AppSettings

logger = logging.getLogger(__name__)


class SettingsStore:
    """Manages application persistent settings storage in JSON."""

    def __init__(self, file_path: Path):
        self.file_path = Path(file_path)
        self.file_path.parent.mkdir(parents=True, exist_ok=True)
        self.settings = self.load()

    def load(self) -> AppSettings:
        if not self.file_path.exists():
            default_settings = AppSettings()
            self.save(default_settings)
            return default_settings

        try:
            with open(self.file_path, "r", encoding="utf-8") as f:
                data = json.load(f)
            return AppSettings.model_validate(data)
        except Exception as e:
            logger.error(f"Error loading settings file '{self.file_path}': {e}. Using defaults.")
            return AppSettings()

    def save(self, settings: AppSettings) -> None:
        self.settings = settings
        with open(self.file_path, "w", encoding="utf-8") as f:
            json.dump(settings.model_dump(mode="json"), f, indent=4)
        logger.info(f"Saved application settings to {self.file_path}")
