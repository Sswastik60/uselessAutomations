"""Settings View - Configuration panel for browser, automation, and safety behavior."""

from PySide6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel, QComboBox,
    QCheckBox, QSpinBox, QMessageBox
)
from PySide6.QtCore import Qt, Signal
from PySide6.QtGui import QFont

from .components import (
    CardFrame, PrimaryButton, SecondaryButton,
    COLOR_BG_CARD, COLOR_BG_SURFACE, COLOR_TEXT_WHITE,
    COLOR_TEXT_MUTED, COLOR_TEXT_DIM, COLOR_BORDER, COLOR_WHITE
)
from ..services.settings import AppSettings, SettingsManager


class SettingsView(QWidget):
    """Settings interface for configuring HackFill runtime and safety parameters."""

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

        subtitle = QLabel("Configure browser execution, navigation limits, and safety pauses.")
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
        self.combo_browser.addItem("Chromium")
        self.combo_browser.setFixedHeight(34)
        b_row1.addWidget(b_label1)
        b_row1.addWidget(self.combo_browser, stretch=1)
        b_layout.addLayout(b_row1)

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

    def load_settings(self):
        s = self.manager.settings
        self.chk_visible.setChecked(s.browser_visible)
        self.spin_timeout.setValue(s.timeout_seconds)
        self.spin_max_pages.setValue(s.max_pages)
        self.chk_confirm_submit.setChecked(s.require_confirmation_before_submit)
        self.chk_pause_uncertain.setChecked(s.pause_on_uncertain_fields)
        self.chk_pause_captcha.setChecked(s.pause_on_captcha)
        self.chk_logging.setChecked(s.logging_enabled)

    def save_settings(self):
        s = self.manager.settings
        s.browser_visible = self.chk_visible.isChecked()
        s.timeout_seconds = self.spin_timeout.value()
        s.max_pages = self.spin_max_pages.value()
        s.require_confirmation_before_submit = self.chk_confirm_submit.isChecked()
        s.pause_on_uncertain_fields = self.chk_pause_uncertain.isChecked()
        s.pause_on_captcha = self.chk_pause_captcha.isChecked()
        s.logging_enabled = self.chk_logging.isChecked()

        self.manager.save()
        self.settings_saved.emit(s)
        QMessageBox.information(self, "Settings Saved", "Preferences updated and saved successfully.")

    def reset_defaults(self):
        default = AppSettings()
        self.chk_visible.setChecked(default.browser_visible)
        self.spin_timeout.setValue(default.timeout_seconds)
        self.spin_max_pages.setValue(default.max_pages)
        self.chk_confirm_submit.setChecked(default.require_confirmation_before_submit)
        self.chk_pause_uncertain.setChecked(default.pause_on_uncertain_fields)
        self.chk_pause_captcha.setChecked(default.pause_on_captcha)
        self.chk_logging.setChecked(default.logging_enabled)
