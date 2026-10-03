"""Unit and integration tests for Brave Browser detection and execution."""

import os
from pathlib import Path
import pytest
from app.automation.browser import find_browser_executable, get_available_browsers, BrowserManager


def test_brave_executable_detection():
    brave_path = find_browser_executable("Brave")
    # On this machine, Brave is installed in Program Files
    if brave_path:
        assert Path(brave_path).exists()
        assert "brave" in Path(brave_path).name.lower()


def test_custom_browser_path():
    dummy_path = Path("main.py").absolute()
    res = find_browser_executable("Brave", custom_path=str(dummy_path))
    assert res == str(dummy_path)


def test_get_available_browsers():
    browsers = get_available_browsers()
    assert "Chromium" in browsers
    assert "Brave" in browsers
    assert "Chrome" in browsers
    assert "Edge" in browsers


def test_brave_launch_and_navigate():
    brave_path = find_browser_executable("Brave")
    if not brave_path:
        pytest.skip("Brave browser not installed in this environment.")

    manager = BrowserManager(browser_type="Brave", visible=False, timeout_seconds=15)
    ok, err = manager.launch()
    assert ok, f"Brave failed to launch: {err}"
    assert manager.is_alive()

    # Navigate to local test form using Brave
    test_url = Path("test_pages/basic_form.html").absolute().as_uri()
    nav_ok, nav_err = manager.navigate(test_url)
    assert nav_ok, f"Navigation with Brave failed: {nav_err}"
    assert "Basic Hackathon" in manager.page.title()

    manager.close()
    assert not manager.is_alive()


def test_is_browser_running_detection():
    from app.automation.browser import is_browser_running
    # Brave is running on this Windows system
    running = is_browser_running("Brave")
    assert isinstance(running, bool)
    # A non-existent fake browser name should return False
    assert not is_browser_running("non_existent_fake_browser_xyz")


def test_is_cdp_port_active_check():
    from app.automation.browser import is_cdp_port_active
    # Port 59999 should not be active
    assert not is_cdp_port_active(59999)

