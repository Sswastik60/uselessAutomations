import pytest
import app.actions  # Ensure all built-in actions are imported and registered
from app.core.action_registry import action_registry


def test_registered_action_types():
    assert action_registry.is_registered("process.launch")
    assert action_registry.is_registered("file.open")
    assert action_registry.is_registered("audio.set_output")
    assert action_registry.is_registered("wait.duration")
    assert action_registry.is_registered("condition.device_exists")


def test_list_categories():
    categories = action_registry.get_categories()
    assert "Process" in categories
    assert "File" in categories
    assert "Audio" in categories
    assert "Wait" in categories


def test_create_action_instance():
    act = action_registry.create_action("wait.duration", {"seconds": 0.5})
    assert act.params["seconds"] == 0.5
