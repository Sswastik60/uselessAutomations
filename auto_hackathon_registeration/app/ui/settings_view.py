"""Settings View - Configuration panel for browser, automation, and safety behavior."""

from pathlib import Path
from PySide6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel, QComboBox,
    QCheckBox, QSpinBox, QLineEdit, QFileDialog, QMessageBox
)
from PySide6.QtCore import Qt, Signal
from PySide6.QtGui import QFont

from .components import (
    CardFrame, PrimaryButton, SecondaryButton, BadgeLabel,
    COLOR_BG_CARD, COLOR_BG_SURFACE, COLOR_TEXT_WHITE,
    COLOR_TEXT_MUTED, COLOR_TEXT_DIM, COLOR_BORDER, COLOR_WHITE
)
from ..services.settings import AppSettings, SettingsManager
from ..automation.browser import find_browser_executable


class SettingsView(QWidget):
    """Settings interface for configuring HackFill runtime, browser choice, and safety parameters."""

    settings_saved = Signal(AppSettings)

    def __init__(self, manager: SettingsManager, parent=None):
        super().__init__(parent)
        self.manager = manager
        self._init_ui()
        self.load_settings()

    def _init_ui(self):
        layout = QVBoxLayout(self)
        layout.setContentsMargins(32, 28, 32, 28)
        layout.setSpacing(20)

        # Header
        header_vbox = QVBoxLayout()
        header_vbox.setSpacing(4)

        title = QLabel("SETTINGS")
        title.setFont(QFont("-apple-system", 18, QFont.Bold))
        title.setStyleSheet(f"color: {COLOR_WHITE}; letter-spacing: -0.5px;")

        subtitle = QLabel("Configure browser execution (Chromium, Brave, Chrome, Edge), navigation limits, and safety pauses.")
        subtitle.setFont(QFont("-apple-system", 11))
        subtitle.setStyleSheet(f"color: {COLOR_TEXT_MUTED};")

        header_vbox.addWidget(title)
        header_vbox.addWidget(subtitle)
        layout.addLayout(header_vbox)

        # 1. Browser Configuration Card
        browser_card = CardFrame()
        b_layout = QVBoxLayout(browser_card)
        b_layout.setContentsMargins(20, 18, 20, 18)
        b_layout.setSpacing(14)

        b_title = QLabel("BROWSER ENGINE")
        b_title.setFont(QFont("-apple-system", 10, QFont.Bold))
        b_title.setStyleSheet(f"color: {COLOR_TEXT_MUTED}; letter-spacing: 0.5px;")
        b_layout.addWidget(b_title)

        b_row1 = QHBoxLayout()
        b_label1 = QLabel("Browser Type:")
        b_label1.setFixedWidth(200)

        self.combo_browser = QComboBox()
        self.combo_browser.addItem("Brave", "Brave")
        self.combo_browser.addItem("Chromium", "Chromium")
        self.combo_browser.addItem("Chrome", "Chrome")
        self.combo_browser.addItem("Edge", "Edge")
        self.combo_browser.setFixedHeight(34)
        self.combo_browser.currentIndexChanged.connect(self._on_browser_changed)

        self.browser_detected_badge = BadgeLabel("DETECTED", "SUCCESS")
        self.browser_detected_badge.setFixedHeight(28)

        b_row1.addWidget(b_label1)
        b_row1.addWidget(self.combo_browser, stretch=1)
        b_row1.addWidget(self.browser_detected_badge)
        b_layout.addLayout(b_row1)

        # Detected path info label
        self.browser_path_info = QLabel("")
        self.browser_path_info.setFont(QFont("Consolas", 9))
        self.browser_path_info.setStyleSheet(f"color: {COLOR_TEXT_MUTED};")
        b_layout.addWidget(self.browser_path_info)

        # Custom executable path row
        b_row2 = QHBoxLayout()
        b_label2 = QLabel("Custom Executable Path:")
        b_label2.setFixedWidth(200)

        self.input_custom_path = QLineEdit()
        self.input_custom_path.setPlaceholderText("Optional: C:\\Path\\To\\brave.exe")
        self.input_custom_path.setFixedHeight(34)
        self.input_custom_path.textChanged.connect(lambda _: self._on_browser_changed())

        self.btn_browse_browser = SecondaryButton("Browse...")
        self.btn_browse_browser.setFixedHeight(34)
        self.btn_browse_browser.clicked.connect(self._browse_custom_browser)

        b_row2.addWidget(b_label2)
        b_row2.addWidget(self.input_custom_path, stretch=1)
        b_row2.addWidget(self.btn_browse_browser)
        b_layout.addLayout(b_row2)

        self.chk_visible = QCheckBox("Keep browser visible while automating (Recommended)")
        self.chk_visible.setChecked(True)
        b_layout.addWidget(self.chk_visible)

        layout.addWidget(browser_card)

        # 2. Limits & Timeouts Card
        limits_card = CardFrame()
        l_layout = QVBoxLayout(limits_card)
        l_layout.setContentsMargins(20, 18, 20, 18)
        l_layout.setSpacing(14)

        l_title = QLabel("LIMITS & TIMEOUTS")
        l_title.setFont(QFont("-apple-system", 10, QFont.Bold))
        l_title.setStyleSheet(f"color: {COLOR_TEXT_MUTED}; letter-spacing: 0.5px;")
        l_layout.addWidget(l_title)

        l_row1 = QHBoxLayout()
        l_lbl1 = QLabel("Page Timeout (seconds):")
        l_lbl1.setFixedWidth(200)
        self.spin_timeout = QSpinBox()
        self.spin_timeout.setRange(5, 180)
        self.spin_timeout.setValue(30)
        self.spin_timeout.setFixedHeight(34)
        l_row1.addWidget(l_lbl1)
        l_row1.addWidget(self.spin_timeout, stretch=1)
        l_layout.addLayout(l_row1)

        l_row2 = QHBoxLayout()
        l_lbl2 = QLabel("Maximum Pages / Steps:")
        l_lbl2.setFixedWidth(200)
        self.spin_max_pages = QSpinBox()
        self.spin_max_pages.setRange(1, 100)
        self.spin_max_pages.setValue(30)
        self.spin_max_pages.setFixedHeight(34)
        l_row2.addWidget(l_lbl2)
        l_row2.addWidget(self.spin_max_pages, stretch=1)
        l_layout.addLayout(l_row2)

        layout.addWidget(limits_card)

        # 3. Safety & Automation Behavior Card
        safety_card = CardFrame()
        s_layout = QVBoxLayout(safety_card)
        s_layout.setContentsMargins(20, 18, 20, 18)
        s_layout.setSpacing(12)

        s_title = QLabel("SAFETY & AUTOMATION BEHAVIOR")
        s_title.setFont(QFont("-apple-system", 10, QFont.Bold))
        s_title.setStyleSheet(f"color: {COLOR_TEXT_MUTED}; letter-spacing: 0.5px;")
        s_layout.addWidget(s_title)

        self.chk_confirm_submit = QCheckBox("Require explicit user review and confirmation before final submission")
        self.chk_confirm_submit.setChecked(True)
        s_layout.addWidget(self.chk_confirm_submit)

        self.chk_pause_uncertain = QCheckBox("Pause on uncertain or unmapped custom fields to request user answer")
        self.chk_pause_uncertain.setChecked(True)
        s_layout.addWidget(self.chk_pause_uncertain)

        self.chk_pause_captcha = QCheckBox("Pause on CAPTCHA / bot verification challenges for manual user solving")
        self.chk_pause_captcha.setChecked(True)
        s_layout.addWidget(self.chk_pause_captcha)

        self.chk_logging = QCheckBox("Enable local activity logging")
        self.chk_logging.setChecked(True)
        s_layout.addWidget(self.chk_logging)

        layout.addWidget(safety_card)

        # Bottom Actions
        actions_row = QHBoxLayout()
        self.btn_reset = SecondaryButton("Restore Defaults")
        self.btn_reset.setFixedHeight(40)
        self.btn_reset.clicked.connect(self.reset_defaults)

        self.btn_save = PrimaryButton("Save Settings")
        self.btn_save.setFixedHeight(40)
        self.btn_save.clicked.connect(self.save_settings)

        actions_row.addWidget(self.btn_reset)
        actions_row.addStretch()
        actions_row.addWidget(self.btn_save)

        layout.addLayout(actions_row)
        layout.addStretch()

    def _on_browser_changed(self):
        b_type = self.combo_browser.currentData() or "Chromium"
        custom_path = self.input_custom_path.text().strip()

        if b_type == "Chromium":
            self.browser_detected_badge.set_level("SUCCESS", "PLAYWRIGHT BUILT-IN")
            self.browser_path_info.setText("Using Playwright's managed Chromium browser.")
        else:
            path = find_browser_executable(b_type, custom_path)
            if path:
                self.browser_detected_badge.set_level("SUCCESS", "INSTALLED")
                self.browser_path_info.setText(f"Found binary: {path}")
            else:
                self.browser_detected_badge.set_level("WARNING", "NOT DETECTED")
                self.browser_path_info.setText(f"Could not locate {b_type}. Specify custom path or install it.")

    def _browse_custom_browser(self):
        filepath, _ = QFileDialog.getOpenFileName(
            self, "Select Browser Binary", "C:\\", "Executable Files (*.exe);;All Files (*)"
        )
        if filepath:
            self.input_custom_path.setText(filepath)
            self._on_browser_changed()

    def load_settings(self):
        s = self.manager.settings
        # Find matching combo index
        idx = self.combo_browser.findData(s.browser)
        if idx >= 0:
            self.combo_browser.setCurrentIndex(idx)
        else:
            self.combo_browser.setCurrentIndex(0)

        self.input_custom_path.setText(s.custom_browser_path)
        self.chk_visible.setChecked(s.browser_visible)
        self.spin_timeout.setValue(s.timeout_seconds)
        self.spin_max_pages.setValue(s.max_pages)
        self.chk_confirm_submit.setChecked(s.require_confirmation_before_submit)
        self.chk_pause_uncertain.setChecked(s.pause_on_uncertain_fields)
        self.chk_pause_captcha.setChecked(s.pause_on_captcha)
        self.chk_logging.setChecked(s.logging_enabled)
        self._on_browser_changed()

    def save_settings(self):
        s = self.manager.settings
        s.browser = self.combo_browser.currentData() or "Chromium"
        s.custom_browser_path = self.input_custom_path.text().strip()
        s.browser_visible = self.chk_visible.isChecked()
        s.timeout_seconds = self.spin_timeout.value()
        s.max_pages = self.spin_max_pages.value()
        s.require_confirmation_before_submit = self.chk_confirm_submit.isChecked()
        s.pause_on_uncertain_fields = self.chk_pause_uncertain.isChecked()
        s.pause_on_captcha = self.chk_pause_captcha.isChecked()
        s.logging_enabled = self.chk_logging.isChecked()

        self.manager.save()
        self.settings_saved.emit(s)
        QMessageBox.information(self, "Settings Saved", f"Preferences updated! Engine set to: {s.browser}")

    def reset_defaults(self):
        default = AppSettings()
        idx = self.combo_browser.findData(default.browser)
        if idx >= 0:
            self.combo_browser.setCurrentIndex(idx)
        self.input_custom_path.setText("")
        self.chk_visible.setChecked(default.browser_visible)
        self.spin_timeout.setValue(default.timeout_seconds)
        self.spin_max_pages.setValue(default.max_pages)
        self.chk_confirm_submit.setChecked(default.require_confirmation_before_submit)
        self.chk_pause_uncertain.setChecked(default.pause_on_uncertain_fields)
        self.chk_pause_captcha.setChecked(default.pause_on_captcha)
        self.chk_logging.setChecked(default.logging_enabled)
        self._on_browser_changed()
