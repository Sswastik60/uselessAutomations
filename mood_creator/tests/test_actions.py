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


def test_process_manager_shortcut_resolution():
    from app.windows.processes import ProcessManager
    # Test resolving existing shortcut if available
    dedicated_lnk = "DEDICATED_MODES/Game_mode/Steam.lnk"
    if os.path.exists(dedicated_lnk):
        target = ProcessManager.resolve_shortcut(dedicated_lnk)
        assert target is not None
        assert "Steam.exe" in target or os.path.exists(target)


def test_auto_discover_app_path():
    from app.windows.processes import ProcessManager
    # Test that auto_discover_app_path runs without NameError or unhandled exception
    res_steam = ProcessManager.auto_discover_app_path("steam")
    res_discord = ProcessManager.auto_discover_app_path("discord")
    res_code = ProcessManager.auto_discover_app_path("code")
    # At least one should be found on the dev machine
    assert res_steam is not None or res_discord is not None or res_code is not None


