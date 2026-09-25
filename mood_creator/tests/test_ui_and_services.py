import pytest
from PySide6.QtWidgets import QApplication
from app.models.mode import Mode
from app.ui.widgets.hotkey_input import HotkeyInputWidget
from app.ui.widgets.mode_card import ModeCard
from app.services.notification_service import NotificationService

# Ensure single QApplication instance for Qt tests
@pytest.fixture(scope="session")
def qapp():
    app = QApplication.instance()
    if app is None:
        app = QApplication([])
    yield app


def test_hotkey_input_widget(qapp):
    widget = HotkeyInputWidget()
    widget.setText("CTRL+ALT+G")
    assert widget.text() == "CTRL+ALT+G"

    widget.clear_btn.click()
    assert widget.text() == ""


def test_mode_card_widget(qapp):
    mode = Mode(
        schema_version=1,
        id="test_mode",
        name="Test Mode",
        description="A test mode",
        icon="🎸",
        hotkey="CTRL+ALT+G",
        actions=[]
    )
    card = ModeCard(mode)
    assert card.mode.id == "test_mode"


def test_notification_service():
    svc = NotificationService()
    # Should safely handle missing tray icon without raising exceptions
    svc.show_notification("Test Title", "Test Message")


def test_toggle_switch(qapp):
    from app.ui.settings import ToggleSwitch
    toggle = ToggleSwitch(checked=False)
    assert toggle.isChecked() is False
    assert toggle.thumb_pos == 0.0

    toggle.setChecked(True, animate=False)
    assert toggle.isChecked() is True
    assert toggle.thumb_pos == 1.0

    toggle.toggle()
    assert toggle.isChecked() is False


def test_settings_view(qapp):
    from app.models.settings import AppSettings
    from app.ui.settings import SettingsView

    settings = AppSettings(start_with_windows=True, minimize_to_tray=True)
    view = SettingsView(settings)
    assert view.autostart_toggle.isChecked() is True
    assert view.tray_toggle.isChecked() is True

    # Test category switching
    view._switch_category("applications")
    assert view.content_stack.currentIndex() == 4

    # Test dirty tracking
    assert view._dirty is False
    view.minimized_toggle.toggle()
    assert view._dirty is True
    assert view.save_btn.isEnabled() is True

