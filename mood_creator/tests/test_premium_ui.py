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


def test_mode_card_background_artwork(qapp):
    from app.ui.widgets.mode_card import ModeCard
    
    # 1. Mode with explicit background preset
    mode_dunes = Mode(
        id="asm_mode",
        name="ASM Mode",
        description="Low level assembly",
        icon="💻",
        background="hero_dunes.jpg",
        actions=[]
    )
    card1 = ModeCard(mode_dunes)
    assert card1.bg_pixmap is not None
    assert not card1.bg_pixmap.isNull()

    # 2. Mode with keyword fallback
    mode_guitar = Mode(
        id="guitar_mode",
        name="Guitar Practice",
        actions=[]
    )
    card2 = ModeCard(mode_guitar)
    assert card2.bg_pixmap is not None
    assert not card2.bg_pixmap.isNull()


def test_mode_editor_create_new_mode(qapp):
    from app.ui.mode_editor import ModeEditorView

    editor = ModeEditorView()
    editor.set_available_modes([
        Mode(id="coding_mode", name="Coding Mode", actions=[]),
        Mode(id="gaming_mode", name="Gaming Mode", actions=[]),
    ])

    # Initiate create new mode
    editor.load_mode(None)
    assert editor.is_new_mode is True
    assert editor.current_mode_id is None
    assert editor.id_input.isEnabled() is True

    # Type new name
    editor.name_input.setText("ASM Mode")
    assert editor.id_input.text() == "asm_mode"

    # Select background preset
    editor._select_bg_preset("banner_mountain.jpg", None, "🏔 Mountain")
    assert editor.current_background == "banner_mountain.jpg"
    assert editor.preview_card.banner_pixmap is not None

    # Test saving
    emitted_modes = []
    editor.save_requested.connect(emitted_modes.append)
    editor._on_save_clicked()

    assert len(emitted_modes) == 1
    new_m = emitted_modes[0]
    assert new_m.id == "asm_mode"
    assert new_m.name == "ASM Mode"
    assert new_m.background == "banner_mountain.jpg"


