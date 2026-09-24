from PySide6.QtCore import Signal
from PySide6.QtWidgets import (
    QCheckBox,
    QFileDialog,
    QFormLayout,
    QFrame,
    QHBoxLayout,
    QLabel,
    QLineEdit,
    QPushButton,
    QVBoxLayout,
    QWidget,
)

from app.models.settings import AppSettings
from app.services.startup_service import StartupService


class SettingsView(QWidget):
    """Application Settings Configuration Screen."""

    settings_saved = Signal(AppSettings)

    def __init__(self, settings: AppSettings, parent=None):
        super().__init__(parent)
        self.current_settings = settings

        main_layout = QVBoxLayout(self)
        main_layout.setContentsMargins(24, 24, 24, 24)
        main_layout.setSpacing(20)

        # Title
        title_lbl = QLabel("Application Settings")
        title_lbl.setStyleSheet("font-size: 24px; font-weight: 700; color: #f8fafc;")
        main_layout.addWidget(title_lbl)

        # General Section
        gen_frame = QFrame()
        gen_frame.setStyleSheet("QFrame { background-color: #1e293b; border: 1px solid #334155; border-radius: 12px; padding: 16px; }")
        gen_layout = QVBoxLayout(gen_frame)
        
        gen_lbl = QLabel("General System Settings")
        gen_lbl.setStyleSheet("font-size: 16px; font-weight: 700; color: #38bdf8; margin-bottom: 8px;")
        gen_layout.addWidget(gen_lbl)

        self.autostart_cb = QCheckBox("Start Automation Hub on Windows boot")
        self.autostart_cb.setChecked(settings.start_with_windows)

        self.tray_cb = QCheckBox("Minimize to Windows System Tray on close")
        self.tray_cb.setChecked(settings.minimize_to_tray)

        self.minimized_cb = QCheckBox("Launch application minimized in tray")
        self.minimized_cb.setChecked(settings.launch_minimized)

        self.notif_cb = QCheckBox("Enable Windows desktop toast notifications")
        self.notif_cb.setChecked(settings.notifications_enabled)

        gen_layout.addWidget(self.autostart_cb)
        gen_layout.addWidget(self.tray_cb)
        gen_layout.addWidget(self.minimized_cb)
        gen_layout.addWidget(self.notif_cb)

        main_layout.addWidget(gen_frame)

        # Applications Executable Paths Section
        app_frame = QFrame()
        app_frame.setStyleSheet("QFrame { background-color: #1e293b; border: 1px solid #334155; border-radius: 12px; padding: 16px; }")
        app_form = QFormLayout(app_frame)
        app_form.setSpacing(12)

        app_lbl = QLabel("Application Executable Paths")
        app_lbl.setStyleSheet("font-size: 16px; font-weight: 700; color: #38bdf8;")
        app_form.addRow(app_lbl)

        self.app_path_inputs = {}
        for app_key, app_title in [
            ("fl_studio", "FL Studio Executable (FL64.exe):"),
            ("vscode", "VS Code Executable (Code.exe):"),
            ("steam", "Steam Executable (steam.exe):"),
            ("spotify", "Spotify Executable (Spotify.exe):"),
            ("discord", "Discord Executable (Discord.exe):"),
        ]:
            h_layout = QHBoxLayout()
            inp = QLineEdit()
            inp.setText(settings.app_paths.get(app_key, ""))
            inp.setPlaceholderText("Auto-discovered if empty")
            
            browse_btn = QPushButton("Browse...")
            browse_btn.setProperty("class", "SecondaryButton")
            browse_btn.clicked.connect(lambda _, k=app_key, field=inp: self._browse_exe(k, field))

            h_layout.addWidget(inp, stretch=1)
            h_layout.addWidget(browse_btn)

            app_form.addRow(app_title, h_layout)
            self.app_path_inputs[app_key] = inp

        main_layout.addWidget(app_frame)
        main_layout.addStretch()

        # Save Button Bar
        btn_layout = QHBoxLayout()
        btn_layout.addStretch()

        self.save_btn = QPushButton("Save Settings")
        self.save_btn.setProperty("class", "PrimaryButton")
        self.save_btn.clicked.connect(self._on_save_clicked)

        btn_layout.addWidget(self.save_btn)
        main_layout.addLayout(btn_layout)

    def _browse_exe(self, app_key: str, line_edit: QLineEdit) -> None:
        file_path, _ = QFileDialog.getOpenFileName(
            self, f"Select Executable for {app_key}", "", "Executable Files (*.exe);;All Files (*.*)"
        )
        if file_path:
            line_edit.setText(file_path)

    def _on_save_clicked(self) -> None:
        autostart = self.autostart_cb.isChecked()
        
        # Apply registry autostart setting
        StartupService.set_start_with_windows(autostart)

        app_paths = {k: inp.text().strip() for k, inp in self.app_path_inputs.items() if inp.text().strip()}

        updated = AppSettings(
            start_with_windows=autostart,
            minimize_to_tray=self.tray_cb.isChecked(),
            launch_minimized=self.minimized_cb.isChecked(),
            notifications_enabled=self.notif_cb.isChecked(),
            app_paths=app_paths,
        )

        self.settings_saved.emit(updated)
