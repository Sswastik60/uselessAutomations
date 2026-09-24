"""Unit tests for MainWindow initialization, theme loading, and mode execution."""

import pytest
from pathlib import Path
from PySide6.QtWidgets import QApplication

from app.ui.main_window import MainWindow
from app.ui.design import ThemeManager
from app.core.mode_manager import ModeManager
import app.actions


@pytest.fixture(scope="module")
def qapp():
    app = QApplication.instance()
    if app is None:
        app = QApplication([])
    yield app


def test_main_window_init(qapp):
    root_dir = Path(__file__).resolve().parent.parent
    window = MainWindow(app_dir=root_dir)
    assert window is not None
    assert window.windowTitle() == "Windows 11 Automation Hub"
    assert window.stacked_widget.count() == 5

    # Check theme applied
    tm = ThemeManager.get_instance()
    assert tm.current_theme in ("dark", "light")

    # Check modes loaded
    modes = window.mode_manager.get_all_modes()
    assert len(modes) >= 1

    # Verify Gaming Mode exists and is configured
    gaming = window.mode_manager.get_mode("gaming_mode")
    assert gaming is not None
    assert gaming.name == "Gaming Mode"

    window.close()


def test_main_window_page_navigation(qapp):
    root_dir = Path(__file__).resolve().parent.parent
    window = MainWindow(app_dir=root_dir)

    # Test navigating through all pages without crash or NameError
    for page_idx in range(window.stacked_widget.count()):
        window._on_page_changed(page_idx)
        assert window.stacked_widget.currentIndex() == page_idx

    window.close()

