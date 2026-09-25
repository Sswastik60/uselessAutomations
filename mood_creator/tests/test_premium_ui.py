"""Unit tests for Premium UI components (AnimationManager, CommandPalette, Overlay, ToastManager)."""

import pytest
from PySide6.QtWidgets import QApplication, QWidget

from app.models.mode import Mode
from app.ui.animation_manager import AnimationManager
from app.ui.command_palette import CommandPaletteDialog
from app.ui.overlay import FloatingOverlayWindow, get_overlay_window
from app.ui.toast import ToastManager, ToastWidget


@pytest.fixture(scope="module")
def qapp():
    app = QApplication.instance()
    if app is None:
        app = QApplication([])
    yield app


def test_animation_manager_reduce_motion(qapp):
    AnimationManager.set_reduce_motion(True)
    assert AnimationManager.reduce_motion is True

    w = QWidget()
    anim = AnimationManager.fade_in(w, duration=100)
    assert anim is None  # Instant show when reduce motion is True
    assert w.isVisible() is True

    AnimationManager.set_reduce_motion(False)
    assert AnimationManager.reduce_motion is False


def test_overlay_window(qapp):
    overlay = get_overlay_window()
    assert isinstance(overlay, FloatingOverlayWindow)

    overlay.start_mode("gaming_mode", "Gaming Mode", "🎮")
    assert overlay.title_lbl.text() == "Gaming Mode"

    overlay.update_action(1, 3, "Launch Steam")
    assert "Step 1/3" in overlay.status_sub_lbl.text()

    overlay.complete_mode("gaming_mode", "Gaming Mode", 0.5)
    assert overlay.badge_lbl.text() == "READY"

    overlay.hide_overlay()


def test_command_palette_dialog(qapp):
    modes = [
        Mode(id="test_mode", name="Test Mode", description="Test mode desc", icon="⚡"),
    ]
    dlg = CommandPaletteDialog(modes=modes)
    assert dlg.list_widget.count() > 0

    # Search filter
    dlg.search_input.setText("Test")
    assert dlg.list_widget.count() > 0

    dlg.search_input.setText("NonExistentQuery1234")
    # Only standard nav buttons remain or list filtered
    dlg.close()


def test_toast_manager(qapp):
    parent = QWidget()
    toast = ToastManager.show_toast(parent, "Test toast message", level="info", duration_ms=500)
    assert isinstance(toast, ToastWidget)
    assert toast.msg_lbl.text() == "Test toast message"
    toast.dismiss()


def test_smooth_scroll_filter(qapp):
    from PySide6.QtWidgets import QScrollArea, QLabel, QVBoxLayout
    from app.ui.smooth_scroll import install_smooth_scroll, SmoothScrollFilter

    scroll = QScrollArea()
    content = QWidget()
    layout = QVBoxLayout(content)
    for i in range(50):
        layout.addWidget(QLabel(f"Item {i}"))
    scroll.setWidget(content)
    scroll.resize(300, 200)

    smooth = install_smooth_scroll(scroll)
    assert isinstance(smooth, SmoothScrollFilter)
    assert smooth.scroll_area is scroll
    assert smooth.v_scroll_pos == 0.0

    # Test setter
    smooth.v_scroll_pos = 25.0
    assert scroll.verticalScrollBar().value() == 25


def test_smooth_stacked_widget(qapp):
    from PySide6.QtWidgets import QLabel
    from app.ui.smooth_stacked import SmoothStackedWidget

    stacked = SmoothStackedWidget()
    w1 = QLabel("Page 1")
    w2 = QLabel("Page 2")
    stacked.addWidget(w1)
    stacked.addWidget(w2)
    stacked.resize(400, 300)

    assert stacked.currentIndex() == 0

    # Smooth switch to page 1
    stacked.set_current_index_smooth(1)
    assert stacked.currentIndex() == 1

    # Smooth switch with reduce motion
    stacked.set_current_index_smooth(0, reduce_motion=True)
    assert stacked.currentIndex() == 0

