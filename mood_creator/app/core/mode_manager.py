import json
import logging
import os
from pathlib import Path
from typing import Dict, List, Optional
from pydantic import ValidationError

from app.core.exceptions import ModeNotFoundError, ModeValidationError
from app.models.mode import Mode

logger = logging.getLogger(__name__)


class ModeManager:
    """Manages creation, persistence, validation, and retrieval of automation Modes."""

    def __init__(self, storage_dir: Path, default_modes_dir: Optional[Path] = None):
        self.storage_dir = Path(storage_dir)
        self.default_modes_dir = Path(default_modes_dir) if default_modes_dir else None
        self._modes: Dict[str, Mode] = {}

        self.storage_dir.mkdir(parents=True, exist_ok=True)
        self.reload_all_modes()

    def reload_all_modes(self) -> None:
        """Load modes from default directory and user storage directory, auto-migrating collided user modes."""
        self._modes.clear()

        # 1. Load built-in default modes first
        default_modes: Dict[str, Mode] = {}
        if self.default_modes_dir and self.default_modes_dir.exists():
            for file_path in self.default_modes_dir.glob("*.json"):
                try:
                    mode = self._load_mode_file(file_path)
                    default_modes[mode.id] = mode
                except Exception as e:
                    logger.warning(f"Failed to load default mode from {file_path}: {e}")

        for m_id, m in default_modes.items():
            self._modes[m_id] = m

        # 2. Load user modes from storage directory
        for file_path in self.storage_dir.glob("*.json"):
            try:
                mode = self._load_mode_file(file_path)
                
                # Check for accidental overwrite of default mode with a different user custom mode
                if mode.id in default_modes:
                    def_mode = default_modes[mode.id]
                    # If the name is completely different (e.g. user created VALORANT or ASM and it saved as coding_mode)
                    if mode.name.strip().lower() != def_mode.name.strip().lower():
                        import re
                        slug = re.sub(r"[^a-zA-Z0-9_]", "", mode.name.strip().lower().replace(" ", "_").replace("-", "_"))
                        new_id = f"{slug}_mode" if not slug.endswith("_mode") else slug
                        logger.info(f"Auto-migrating collided user mode '{mode.name}' from {mode.id} to {new_id}")
                        mode.id = new_id
                        # Write migrated user mode to its own file
                        new_file_path = self.storage_dir / f"{new_id}.json"
                        with open(new_file_path, "w", encoding="utf-8") as f:
                            json.dump(mode.model_dump(mode="json"), f, indent=4)
                        # Remove conflicting file so default mode is restored
                        try:
                            file_path.unlink()
                        except Exception:
                            pass
                        self._modes[new_id] = mode
                        continue

                self._modes[mode.id] = mode
            except Exception as e:
                logger.error(f"Failed to load user mode from {file_path}: {e}")

    def generate_unique_mode_id(self, name: str, base_id: Optional[str] = None) -> str:
        """Generate a sanitized, unique mode ID that does not collide with existing modes."""
        import re
        if base_id and base_id.strip():
            slug = re.sub(r"[^a-zA-Z0-9_]", "", base_id.strip().lower().replace(" ", "_").replace("-", "_"))
        else:
            slug = re.sub(r"[^a-zA-Z0-9_]", "", name.strip().lower().replace(" ", "_").replace("-", "_"))
        
        if not slug:
            slug = "custom_mode"
        if not slug.endswith("_mode") and not any(k in slug for k in ["_mode", "mode_"]):
            candidate = f"{slug}_mode"
        else:
            candidate = slug
            
        if candidate not in self._modes:
            return candidate
            
        counter = 1
        while f"{candidate}_{counter}" in self._modes:
            counter += 1
        return f"{candidate}_{counter}"

    def _load_mode_file(self, path: Path) -> Mode:
        """Parse and validate a mode JSON file."""
        with open(path, "r", encoding="utf-8") as f:
            data = json.load(f)
        try:
            return Mode.model_validate(data)
        except ValidationError as ve:
            raise ModeValidationError(f"Invalid mode definition in '{path.name}': {ve}") from ve

    def get_all_modes(self) -> List[Mode]:
        """Return list of all loaded modes."""
        return list(self._modes.values())

    def get_mode(self, mode_id: str) -> Mode:
        """Retrieve a mode by ID."""
        if mode_id not in self._modes:
            raise ModeNotFoundError(f"Mode with ID '{mode_id}' was not found.")
        return self._modes[mode_id]

    def save_mode(self, mode: Mode) -> Mode:
        """Save or update a mode definition to JSON storage."""
        self._modes[mode.id] = mode
        file_path = self.storage_dir / f"{mode.id}.json"
        
        mode_data = mode.model_dump(mode="json")
        with open(file_path, "w", encoding="utf-8") as f:
            json.dump(mode_data, f, indent=4)
            
        logger.info(f"Saved mode '{mode.name}' to {file_path}")
        return mode

    def delete_mode(self, mode_id: str) -> bool:
        """Delete a mode by ID."""
        if mode_id not in self._modes:
            raise ModeNotFoundError(f"Cannot delete non-existent mode '{mode_id}'")

        del self._modes[mode_id]
        file_path = self.storage_dir / f"{mode_id}.json"
        if file_path.exists():
            try:
                file_path.unlink()
                logger.info(f"Deleted mode file {file_path}")
            except Exception as e:
                logger.error(f"Error deleting mode file {file_path}: {e}")
                return False
        return True

    def export_mode_to_file(self, mode_id: str, export_path: Path) -> Path:
        """Export a mode definition to an external JSON file."""
        mode = self.get_mode(mode_id)
        export_path = Path(export_path)
        with open(export_path, "w", encoding="utf-8") as f:
            json.dump(mode.model_dump(mode="json"), f, indent=4)
        logger.info(f"Exported mode '{mode.name}' to {export_path}")
        return export_path

    def import_mode_from_file(self, import_path: Path) -> Mode:
        """Import and validate a mode from an external JSON file."""
        import_path = Path(import_path)
        if not import_path.exists():
            raise FileNotFoundError(f"Import file '{import_path}' does not exist.")

        mode = self._load_mode_file(import_path)
        return self.save_mode(mode)
