import os
import pytest
from app.actions.filesystem import CreateDirectoryAction, CheckFileExistsAction
from app.actions.wait import WaitDurationAction
from app.actions.conditional import EnvVarExistsConditionAction
from app.core.execution_context import AutomationContext


def test_wait_duration_action():
    ctx = AutomationContext("test", "Test Mode")
    act = WaitDurationAction(seconds=0.1)
    res = act.execute(ctx)
    assert res.success is True


def test_filesystem_actions(tmp_path):
    ctx = AutomationContext("test", "Test Mode")
    target_dir = str(tmp_path / "new_folder")

    # Create dir
    act_create = CreateDirectoryAction(directory_path=target_dir)
    res_create = act_create.execute(ctx)
    assert res_create.success is True
    assert os.path.exists(target_dir)

    # Check exists
    act_chk = CheckFileExistsAction(path=target_dir)
    res_chk = act_chk.execute(ctx)
    assert res_chk.success is True


def test_env_var_condition_action():
    ctx = AutomationContext("test", "Test Mode")
    act = EnvVarExistsConditionAction(variable_name="PATH")
    res = act.execute(ctx)
    assert res.success is True
    assert res.data["condition_met"] is True
