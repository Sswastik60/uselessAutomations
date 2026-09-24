import json
import pytest
from app.core.mode_manager import ModeManager
from app.models.mode import Mode


def test_mode_manager_load_and_save(tmp_path):
    storage_dir = tmp_path / "modes"
    manager = ModeManager(storage_dir)

    mode = Mode(
        schema_version=1,
        id="unit_test_mode",
        name="Unit Test Mode",
        description="Testing ModeManager",
        icon="🧪",
        hotkey="CTRL+ALT+U",
        actions=[]
    )

    saved = manager.save_mode(mode)
    assert (storage_dir / "unit_test_mode.json").exists()

    loaded = manager.get_mode("unit_test_mode")
    assert loaded.name == "Unit Test Mode"

    # Export / Import
    export_path = tmp_path / "exported.json"
    manager.export_mode_to_file("unit_test_mode", export_path)
    assert export_path.exists()

    imported = manager.import_mode_from_file(export_path)
    assert imported.id == "unit_test_mode"
