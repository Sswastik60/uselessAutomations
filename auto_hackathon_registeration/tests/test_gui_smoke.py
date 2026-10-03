"""GUI smoke test verifying PySide6 MainWindow, views, and navigation."""

import sys
import pytest
from pathlib import Path
from PySide6.QtWidgets import QApplication
from app.ui.main_window import MainWindow


@pytest.fixture(scope="module")
def app_instance():
    app = QApplication.instance()
    if not app:
        app = QApplication(sys.argv)
    yield app


def test_main_window_initialization(app_instance):
    window = MainWindow()
    assert window.windowTitle() == "HackFill — Fill hackathon registrations in seconds"
    assert window.stack.count() == 5  # Dashboard, Automation, Review, Profile, Settings

    # Check views
    assert window.dashboard_view is not None
    assert window.automation_view is not None
    assert window.review_view is not None
    assert window.profile_view is not None
    assert window.settings_view is not None

    # Test tab switching
    for i in range(5):
        window._set_active_nav(i)
        assert window.stack.currentIndex() == i

    # Verify example profile auto-load or reload
    ex = Path("profiles/example_profile.txt")
    if ex.exists():
        window.profile_view.load_profile_path(str(ex.absolute()))
        assert window.profile_view.current_profile is not None
        assert len(window.profile_view.current_profile) > 0

    window.close()
