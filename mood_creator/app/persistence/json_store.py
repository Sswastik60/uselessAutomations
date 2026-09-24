import json
import logging
from pathlib import Path
from typing import Any, Dict
from pydantic import ValidationError

from app.models.mode import Mode

logger = logging.getLogger(__name__)


class JsonModeStore:
    """Utility for reading, parsing, and writing Mode JSON files."""

    @staticmethod
    def read_mode(path: Path) -> Mode:
        with open(path, "r", encoding="utf-8") as f:
            data = json.load(f)
        return Mode.model_validate(data)

    @staticmethod
    def write_mode(mode: Mode, path: Path) -> None:
        path.parent.mkdir(parents=True, exist_ok=True)
        with open(path, "w", encoding="utf-8") as f:
            json.dump(mode.model_dump(mode="json"), f, indent=4)
        logger.debug(f"Wrote mode '{mode.id}' to {path}")
