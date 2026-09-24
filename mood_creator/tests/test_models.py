import pytest
from app.models.action import ActionConfig
from app.models.action_result import ActionResult
from app.models.mode import Mode
from app.models.settings import AppSettings


def test_action_config_display_name():
    cfg = ActionConfig(type="process.launch", params={"application": "FL Studio"})
    assert cfg.get_display_name() == "Process: Launch"

    cfg_custom = ActionConfig(type="process.launch", name="Open DAW", params={})
    assert cfg_custom.get_display_name() == "Open DAW"


def test_mode_parsing():
    data = {
        "schema_version": 1,
        "id": "test_mode",
        "name": "Test Mode",
        "description": "Test description",
        "icon": "🎸",
        "hotkey": "CTRL+ALT+T",
        "actions": [
            {"type": "wait.duration", "params": {"seconds": 1.0}}
        ]
    }
    mode = Mode.model_validate(data)
    assert mode.id == "test_mode"
    assert len(mode.actions) == 1
    assert mode.actions[0].type == "wait.duration"


def test_action_result_to_dict():
    res = ActionResult(success=True, message="Done", duration=1.23456)
    d = res.to_dict()
    assert d["success"] is True
    assert d["duration"] == 1.2346
