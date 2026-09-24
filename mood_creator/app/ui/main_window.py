import logging
import os
import sys
from pathlib import Path
from typing import Optional

from PySide6.QtCore import Qt, QTimer
from PySide6.QtGui import QAction, QIcon, QPixmap
from PySide6.QtWidgets import (
    QApplication,
    QFileDialog,
    QHBoxLayout,
    QMainWindow,
    QMenu,
    QMessageBox,
    QStackedWidget,
    QStyle,
    QSystemTrayIcon,
    QWidget,
)

from app import __version__
from app.core.automation_engine import AutomationEngine
from app.core.event_bus import event_bus
from app.core.mode_manager import ModeManager
from app.models.mode import Mode
from app.models.settings import AppSettings
from app.persistence.database import Database
from app.persistence.settings_store import SettingsStore
from app.services.device_service import DeviceService
from app.services.hotkey_service import HotkeyService
from app.services.notification_service import NotificationService
from app.ui.animation_manager import AnimationManager
from app.ui.command_palette import CommandPaletteDialog
from app.ui.dashboard import DashboardView
from app.ui.design import ThemeManager
from app.ui.device_panel import DevicePanelView
from app.ui.execution_dialog import ExecutionDialog
from app.ui.logs_panel import LogsPanelView
from app.ui.mode_editor import ModeEditorView
from app.ui.overlay import get_overlay_window
from app.ui.settings import SettingsView
from app.ui.styles.design_tokens import AnimationDuration
from app.ui.toast import ToastManager
from app.ui.widgets.sidebar import SidebarWidget

logger = logging.getLogger(__name__)


class MainWindow(QMainWindow):
    """Main application window for Windows 11 Automation Hub."""

    def __init__(self, app_dir: Path):
        super().__init__()
        self.app_dir = Path(app_dir)
        self.setWindowTitle("Windows 11 Automation Hub")
        self.resize(1260, 800)
        self.setMinimumSize(1000, 680)

        # Set Window Icon
        icon_path = self.app_dir / "assets" / "app_icon.png"
        if not icon_path.exists():
            icon_path = self.app_dir / "assets" / "app_icon.ico"
        if icon_path.exists():
            self.setWindowIcon(QIcon(str(icon_path)))

        # 1. Initialize Stores & Databases
        user_appdata = Path(os.environ.get("APPDATA", ".")) / "AutomationHub"
        user_modes_dir = user_appdata / "modes"
        default_modes_dir = self.app_dir / "modes"

        self.settings_store = SettingsStore(user_appdata / "settings.json")
        self.db = Database(user_appdata / "logs.db")
        self.mode_manager = ModeManager(user_modes_dir, default_modes_dir)

        # 2. Services & Notification Service
        self.device_service = DeviceService()
        self.notification_service = NotificationService()
        
        self.services = {
            "settings": self.settings_store.settings,
            "device_manager": self.device_service.dev_manager,
            "audio": self.device_service.dev_manager.audio_manager,
            "notification_service": self.notification_service,
        }
        self.engine = AutomationEngine(self.services)

        # 3. Apply Theme
        self._load_stylesheet()

        # 4. Main Layout & Central Widget
        central_widget = QWidget()
        self.setCentralWidget(central_widget)
        main_layout = QHBoxLayout(central_widget)
        main_layout.setContentsMargins(0, 0, 0, 0)
        main_layout.setSpacing(0)

        # Sidebar navigation
        self.sidebar = SidebarWidget()
        self.sidebar.page_changed.connect(self._on_page_changed)
        self.sidebar.theme_toggle_requested.connect(self._toggle_theme)
        main_layout.addWidget(self.sidebar)

        # Stacked Views
        self.stacked_widget = QStackedWidget()

        self.dashboard_view = DashboardView()
        self.dashboard_view.run_mode_requested.connect(self.run_mode)
        self.dashboard_view.edit_mode_requested.connect(self.edit_mode)
        self.dashboard_view.create_mode_requested.connect(self.create_mode)
        self.dashboard_view.import_mode_requested.connect(self.import_mode)
        self.dashboard_view.export_mode_requested.connect(self.export_mode)
        self.dashboard_view.duplicate_mode_requested.connect(self.duplicate_mode)
        self.dashboard_view.delete_mode_requested.connect(self._on_delete_mode)
        self.dashboard_view.navigate_requested.connect(self._on_navigation_requested)
        self.dashboard_view.hero.command_palette_requested.connect(self.open_command_palette)

        self.mode_editor_view = ModeEditorView()
        self.mode_editor_view.save_requested.connect(self._on_save_mode)
        self.mode_editor_view.delete_requested.connect(self._on_delete_mode)
        self.mode_editor_view.export_requested.connect(self.export_mode)
        self.mode_editor_view.cancelled.connect(lambda: (self.sidebar.set_active_page(0), self.stacked_widget.setCurrentIndex(0)))

        self.device_panel_view = DevicePanelView()
        self.logs_panel_view = LogsPanelView(self.db)
        
        self.settings_view = SettingsView(self.settings_store.settings)
        self.settings_view.settings_saved.connect(self._on_settings_saved)

        self.stacked_widget.addWidget(self.dashboard_view)       # 0
        self.stacked_widget.addWidget(self.mode_editor_view)     # 1
        self.stacked_widget.addWidget(self.device_panel_view)    # 2
        self.stacked_widget.addWidget(self.logs_panel_view)      # 3
        self.stacked_widget.addWidget(self.settings_view)        # 4

        main_layout.addWidget(self.stacked_widget, stretch=1)

        # 5. System Tray & Global Hotkey Service
        self._init_system_tray()
        
        self.hotkey_service = HotkeyService(mode_trigger_callback=self._on_hotkey_triggered)
        self._register_all_hotkeys()

        # 6. Event Bus Log Listener
        event_bus.subscribe("action_completed", self._on_action_completed_event)

        # 7. Initial Data Load & Timer Status Refresh
        self.refresh_dashboard()

        self.status_timer = QTimer(self)
        self.status_timer.timeout.connect(self._update_system_status)
        self.status_timer.start(5000)

    def _load_stylesheet(self) -> None:
        theme_mode = "dark" if self.settings_store.settings.dark_mode else "light"
        ThemeManager.get_instance().set_theme(theme_mode)

    def _init_system_tray(self) -> None:
        self.tray_icon = QSystemTrayIcon(self)
        self.tray_icon.setIcon(self.windowIcon() if not self.windowIcon().isNull() else QApplication.style().standardIcon(QStyle.StandardPixmap.SP_ComputerIcon))
        
        tray_menu = QMenu()
        tray_menu.setStyleSheet("QMenu { background-color: #1e293b; color: #f8fafc; border: 1px solid #334155; } QMenu::item:selected { background-color: #0284c7; } QMenu::item:disabled { color: #64748b; }")

        title_act = QAction("⚡ Automation Hub", self)
        title_act.setEnabled(False)
        tray_menu.addAction(title_act)
        tray_menu.addSeparator()

        # Stop active mode option
        self.stop_mode_act = QAction("⏹ Stop Active Mode", self)
        self.stop_mode_act.setEnabled(False)
        self.stop_mode_act.triggered.connect(self._stop_active_mode_from_tray)
        tray_menu.addAction(self.stop_mode_act)
        tray_menu.addSeparator()

        # Dynamic mode run menu entries
        self.modes_menu = tray_menu.addMenu("▶ Execute Mode...")
        self._rebuild_tray_modes_menu()

        tray_menu.addSeparator()
        dash_act = tray_menu.addAction("Open Dashboard")
        dash_act.triggered.connect(self.show_window)

        sett_act = tray_menu.addAction("Settings")
        sett_act.triggered.connect(lambda: (self.show_window(), self.sidebar.set_active_page(4)))

        tray_menu.addSeparator()
        exit_act = tray_menu.addAction("🛑 Quit Automation Hub")
        exit_act.triggered.connect(lambda: self.quit_app(force=True))

        self.tray_icon.setContextMenu(tray_menu)
        self.tray_icon.activated.connect(self._on_tray_activated)
        self.tray_icon.show()

        self.notification_service.set_tray_icon(self.tray_icon)

    def _stop_active_mode_from_tray(self) -> None:
        if self.engine.is_running():
            self.engine.cancel_current_mode()
            self.notification_service.show_notification("Automation Hub", "Active mode execution stopped by user.")

    def _rebuild_tray_modes_menu(self) -> None:
        self.modes_menu.clear()
        for mode in self.mode_manager.get_all_modes():
            act = QAction(f"{mode.icon}  {mode.name}", self)
            act.triggered.connect(lambda _, m_id=mode.id: self.run_mode(m_id))
            self.modes_menu.addAction(act)

    def _register_all_hotkeys(self) -> None:
        for mode in self.mode_manager.get_all_modes():
            if mode.hotkey and mode.enabled:
                try:
                    self.hotkey_service.register_mode_hotkey(mode.id, mode.hotkey)
                except Exception as e:
                    logger.warning(f"Could not register hotkey '{mode.hotkey}' for mode '{mode.name}': {e}")

    def refresh_dashboard(self) -> None:
        modes = self.mode_manager.get_all_modes()
        self.dashboard_view.update_modes(modes)
        self._rebuild_tray_modes_menu()
        self._update_system_status()

    def _update_system_status(self) -> None:
        audio_devs = self.device_service.get_audio_devices()
        audio_str = audio_devs[0].name if audio_devs else "Disconnected"
        
        midi_devs = self.device_service.get_midi_devices()
        midi_str = midi_devs[0].name if midi_devs else "Disconnected"

        running = self.engine.get_current_mode()
        running_name = running.name if running else None

        if running_name:
            self.stop_mode_act.setEnabled(True)
            self.stop_mode_act.setText(f"⏹ Stop Active Mode ({running_name})")
        else:
            self.stop_mode_act.setEnabled(False)
            self.stop_mode_act.setText("⏹ Stop Active Mode")

        self.dashboard_view.update_system_status(audio_str, midi_str, running_name)

    def run_mode(self, mode_id: str) -> None:
        try:
            mode = self.mode_manager.get_mode(mode_id)
        except Exception as e:
            QMessageBox.critical(self, "Mode Error", str(e))
            return

        if self.engine.is_running():
            QMessageBox.warning(self, "Engine Busy", "Another Mode is currently executing!")
            return

        # Trigger Signature Floating HUD Overlay Window
        overlay = get_overlay_window()
        overlay.start_mode(mode.id, mode.name, mode.icon)

        worker = self.engine.execute_mode(mode)

        # Connect Overlay & Toast notification signals
        worker.signals.action_started.connect(overlay.update_action)
        worker.signals.mode_progress.connect(overlay.update_progress)
        worker.signals.mode_completed.connect(overlay.complete_mode)
        worker.signals.mode_completed.connect(
            lambda m_id, m_name, dur: ToastManager.show_toast(self, f"✓ {m_name} ready ({dur:.2f}s)", level="success")
        )
        worker.signals.mode_failed.connect(overlay.fail_mode)
        worker.signals.mode_failed.connect(
            lambda m_id, m_name, err: ToastManager.show_toast(self, f"✕ {m_name} issue: {err}", level="error")
        )


    def edit_mode(self, mode_id: str) -> None:
        try:
            mode = self.mode_manager.get_mode(mode_id)
            self.mode_editor_view.load_mode(mode)
            self.sidebar.set_active_page(1)
            self.stacked_widget.setCurrentIndex(1)
        except Exception as e:
            QMessageBox.critical(self, "Error", f"Could not load mode for editing: {e}")

    def create_mode(self) -> None:
        self.mode_editor_view.load_mode(None)
        self.sidebar.set_active_page(1)
        self.stacked_widget.setCurrentIndex(1)

    def export_mode(self, mode_id: str) -> None:
        try:
            mode = self.mode_manager.get_mode(mode_id)
            file_path, _ = QFileDialog.getSaveFileName(
                self, f"Export Mode '{mode.name}'", f"{mode.id}.json", "JSON Files (*.json);;All Files (*.*)"
            )
            if file_path:
                self.mode_manager.export_mode_to_file(mode_id, Path(file_path))
                QMessageBox.information(self, "Export Complete", f"Mode '{mode.name}' exported successfully to:\n{file_path}")
        except Exception as e:
            QMessageBox.critical(self, "Export Error", f"Could not export mode: {e}")

    def import_mode(self, path_str: str) -> None:
        try:
            imported = self.mode_manager.import_mode_from_file(Path(path_str))
            if imported.hotkey:
                self.hotkey_service.register_mode_hotkey(imported.id, imported.hotkey)
            self.refresh_dashboard()
            QMessageBox.information(self, "Import Successful", f"Successfully imported mode '{imported.name}'.")
        except Exception as e:
            QMessageBox.critical(self, "Import Error", f"Failed to import mode: {e}")

    def duplicate_mode(self, mode_id: str) -> None:
        try:
            source = self.mode_manager.get_mode(mode_id)
            dup_id = f"{source.id}_copy"
            dup_mode = Mode(
                schema_version=source.schema_version,
                id=dup_id,
                name=f"{source.name} (Copy)",
                description=source.description,
                icon=source.icon,
                hotkey=None,
                enabled=True,
                actions=source.actions,
            )
            self.mode_manager.save_mode(dup_mode)
            self.refresh_dashboard()
            QMessageBox.information(self, "Mode Duplicated", f"Created duplicate mode '{dup_mode.name}'.")
        except Exception as e:
            QMessageBox.critical(self, "Error", f"Could not duplicate mode: {e}")

    def keyPressEvent(self, event) -> None:
        if event.modifiers() & Qt.KeyboardModifier.ControlModifier and event.key() == Qt.Key.Key_K:
            self.open_command_palette()
            return
        super().keyPressEvent(event)

    def open_command_palette(self) -> None:
        modes = self.mode_manager.get_all_modes()
        palette = CommandPaletteDialog(modes, parent=self)
        palette.command_triggered.connect(self._handle_command_palette_action)
        palette.exec()

    def _handle_command_palette_action(self, action_type: str, payload: object) -> None:
        if action_type == "run_mode" and isinstance(payload, Mode):
            self.run_mode(payload.id)
        elif action_type == "nav_dashboard":
            self.sidebar.set_active_page(0)
            self._on_page_changed(0)
        elif action_type == "nav_modes":
            self.sidebar.set_active_page(1)
            self._on_page_changed(1)
        elif action_type == "nav_devices":
            self.sidebar.set_active_page(2)
            self._on_page_changed(2)
        elif action_type == "nav_logs":
            self.sidebar.set_active_page(3)
            self._on_page_changed(3)
        elif action_type == "nav_settings":
            self.sidebar.set_active_page(4)
            self._on_page_changed(4)
        elif action_type == "create_mode":
            self.create_mode()

    def _on_save_mode(self, mode: Mode) -> None:
        self.mode_manager.save_mode(mode)
        if mode.hotkey:
            self.hotkey_service.register_mode_hotkey(mode.id, mode.hotkey)
        self.refresh_dashboard()
        self.sidebar.set_active_page(0)
        self.stacked_widget.setCurrentIndex(0)

    def _on_delete_mode(self, mode_id: str) -> None:
        self.hotkey_service.unregister_mode_hotkey(mode_id)
        self.mode_manager.delete_mode(mode_id)
        self.refresh_dashboard()
        self.sidebar.set_active_page(0)
        self.stacked_widget.setCurrentIndex(0)

    def _on_settings_saved(self, new_settings: AppSettings) -> None:
        self.settings_store.save(new_settings)
        AnimationManager.set_reduce_motion(new_settings.reduce_motion)
        theme_mode = "dark" if new_settings.dark_mode else "light"
        ThemeManager.get_instance().set_theme(theme_mode)
        ToastManager.show_toast(self, "✓ Settings saved successfully", level="success")

    def _on_hotkey_triggered(self, mode_id: str) -> None:
        logger.info(f"Hotkey triggered run of mode '{mode_id}'")
        QTimer.singleShot(0, lambda: self.run_mode(mode_id))

    def _on_action_completed_event(self, step_idx: int, total_steps: int, action_name: str, result) -> None:
        mode = self.engine.get_current_mode()
        m_id = mode.id if mode else "unknown"
        m_name = mode.name if mode else "System"
        self.db.log_execution(m_id, m_name, action_name, result)

    def _on_page_changed(self, index: int) -> None:
        self.stacked_widget.setCurrentIndex(index)
        current_widget = self.stacked_widget.currentWidget()
        if current_widget:
            try:
                anim_dur = getattr(AnimationDuration, "FAST", 120)
                AnimationManager.fade_in(current_widget, duration=anim_dur)
            except Exception as e:
                logger.debug(f"Page transition animation error: {e}")

        if index == 1:
            if not self.mode_editor_view.current_mode_id:
                modes = self.mode_manager.get_all_modes()
                if modes:
                    self.mode_editor_view.load_mode(modes[0])
        elif index == 2:
            self.device_panel_view.refresh_devices()
        elif index == 3:
            self.logs_panel_view.refresh_logs()

    def _on_navigation_requested(self, index: int) -> None:
        self.sidebar.set_active_page(index)
        self._on_page_changed(index)

    def _toggle_theme(self) -> None:
        tm = ThemeManager.get_instance()
        new_theme = "light" if tm.current_theme == "dark" else "dark"
        tm.set_theme(new_theme)
        self.settings_store.settings.dark_mode = (new_theme == "dark")
        self.settings_store.save()
        ToastManager.show_toast(self, f"Theme switched to {new_theme.capitalize()}", level="info")

    def _on_tray_activated(self, reason: QSystemTrayIcon.ActivationReason) -> None:
        if reason in (QSystemTrayIcon.Trigger, QSystemTrayIcon.DoubleClick):
            self.show_window()

    def show_window(self) -> None:
        if self.isMinimized():
            self.showNormal()
        self.show()
        self.raise_()
        self.activateWindow()


    def closeEvent(self, event) -> None:
        if self.settings_store.settings.minimize_to_tray:
            event.ignore()
            self.hide()
            if self.settings_store.settings.notifications_enabled:
                self.notification_service.show_notification(
                    "Automation Hub", "Running in background system tray."
                )
        else:
            self.quit_app(force=True)

    def quit_app(self, force: bool = True) -> None:
        logger.info("Quitting Automation Hub...")
        try:
            if self.engine.is_running():
                self.engine.cancel_current_mode()
        except Exception as e:
            logger.warning(f"Error cancelling engine: {e}")

        try:
            self.hotkey_service.stop()
        except Exception as e:
            logger.warning(f"Error stopping hotkeys: {e}")

        try:
            self.status_timer.stop()
        except Exception as e:
            pass

        if hasattr(self, "tray_icon") and self.tray_icon:
            self.tray_icon.hide()
            self.tray_icon.deleteLater()

        QApplication.closeAllWindows()
        QApplication.quit()

        if force:
            os._exit(0)
