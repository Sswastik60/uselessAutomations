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


def test_mode_manager_preserves_defaults_when_adding_new_mode(tmp_path):
    default_dir = tmp_path / "defaults"
    default_dir.mkdir()
    user_dir = tmp_path / "user_modes"
    user_dir.mkdir()

    # Create 6 default modes
    for name in ["coding", "gaming", "guitar", "movie", "music", "study"]:
        m = Mode(schema_version=1, id=f"{name}_mode", name=f"{name.capitalize()} Mode", actions=[])
        with open(default_dir / f"{name}.json", "w", encoding="utf-8") as f:
            json.dump(m.model_dump(mode="json"), f)

    manager = ModeManager(user_dir, default_dir)
    assert len(manager.get_all_modes()) == 6

    # Add a brand new ASM mode
    asm_mode = Mode(
        schema_version=1,
        id="asm_mode",
        name="ASM Mode",
        description="Assembly development",
        background="hero_dunes.jpg",
        actions=[]
    )
    manager.save_mode(asm_mode)

    # Re-instantiate / reload
    manager2 = ModeManager(user_dir, default_dir)
    all_modes = manager2.get_all_modes()
    assert len(all_modes) == 7
    ids = {m.id for m in all_modes}
    assert "asm_mode" in ids
    assert "coding_mode" in ids
    assert "gaming_mode" in ids
    assert manager2.get_mode("asm_mode").background == "hero_dunes.jpg"


def test_mode_manager_unique_id_generation(tmp_path):
    storage_dir = tmp_path / "modes"
    manager = ModeManager(storage_dir)

    id1 = manager.generate_unique_mode_id("ASM Mode")
    assert id1 == "asm_mode"

    # Save mode with that ID
    manager.save_mode(Mode(schema_version=1, id=id1, name="ASM Mode", actions=[]))

    id2 = manager.generate_unique_mode_id("ASM Mode")
    assert id2 == "asm_mode_1"


def test_mode_manager_auto_migrates_collided_user_mode(tmp_path):
    default_dir = tmp_path / "defaults"
    default_dir.mkdir()
    user_dir = tmp_path / "user_modes"
    user_dir.mkdir()

    # Default coding mode
    def_mode = Mode(schema_version=1, id="coding_mode", name="Coding Mode", actions=[])
    with open(default_dir / "coding.json", "w", encoding="utf-8") as f:
        json.dump(def_mode.model_dump(mode="json"), f)

    # Accidentally collided user mode named VALORANT saved with coding_mode ID
    collided_mode = Mode(schema_version=1, id="coding_mode", name="VALORANT", actions=[])
    with open(user_dir / "coding_mode.json", "w", encoding="utf-8") as f:
        json.dump(collided_mode.model_dump(mode="json"), f)

    # When manager loads, it should detect the collision, auto-migrate VALORANT to valorant_mode, and restore Coding Mode
    manager = ModeManager(user_dir, default_dir)
    modes = manager.get_all_modes()
    assert len(modes) == 2
    ids = {m.id for m in modes}
    assert "coding_mode" in ids
    assert "valorant_mode" in ids
    assert manager.get_mode("coding_mode").name == "Coding Mode"
    assert manager.get_mode("valorant_mode").name == "VALORANT"

