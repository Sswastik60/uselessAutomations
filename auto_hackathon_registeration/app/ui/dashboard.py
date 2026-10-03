"""Dashboard View - Primary control center for HackFill."""

from pathlib import Path
from typing import Optional, List
from PySide6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel, QLineEdit,
    QComboBox, QTableWidget, QTableWidgetItem, QHeaderView, QFileDialog
)
from PySide6.QtCore import Qt, Signal
from PySide6.QtGui import QFont

from .components import (
    CardFrame, PrimaryButton, SecondaryButton, BadgeLabel,
    COLOR_TEXT_WHITE, COLOR_TEXT_MUTED, COLOR_TEXT_DIM, COLOR_BORDER, COLOR_WHITE
)
from ..utils.helpers import validate_url
from ..services.logger import ActivityLogger, LogEntry, get_logger


class DashboardView(QWidget):
    """Main Dashboard interface for launching hackathon registrations."""

    start_automation_requested = Signal(str, str)  # (url, profile_path)
    view_profile_requested = Signal(str)           # (profile_path)

    def __init__(self, parent=None):
        super().__init__(parent)
        self.logger = get_logger()
        self.selected_profile_path: str = ""
        self._init_ui()
        self._connect_signals()

    def _init_ui(self):
        layout = QVBoxLayout(self)
        layout.setContentsMargins(32, 28, 32, 28)
        layout.setSpacing(24)

        # 1. Top Header
        header_layout = QVBoxLayout()
        header_layout.setSpacing(4)

        title = QLabel("HackFill")
        title.setFont(QFont("-apple-system", 22, QFont.Bold))
        title.setStyleSheet(f"color: {COLOR_WHITE}; letter-spacing: -0.5px;")

        subtitle = QLabel("Fill hackathon registrations in seconds.")
        subtitle.setFont(QFont("-apple-system", 12))
        subtitle.setStyleSheet(f"color: {COLOR_TEXT_MUTED};")

        header_layout.addWidget(title)
        header_layout.addWidget(subtitle)
        layout.addLayout(header_layout)

        # 2. Main Action Card
        action_card = CardFrame()
        card_layout = QVBoxLayout(action_card)
        card_layout.setContentsMargins(24, 24, 24, 24)
        card_layout.setSpacing(20)

        # URL Input Section
        url_section = QVBoxLayout()
        url_section.setSpacing(8)

        url_label = QLabel("HACKATHON REGISTRATION URL")
        url_label.setFont(QFont("-apple-system", 10, QFont.DemiBold))
        url_label.setStyleSheet(f"color: {COLOR_TEXT_MUTED}; letter-spacing: 0.5px;")

        self.url_input = QLineEdit()
        self.url_input.setPlaceholderText("https://example.com/hackathon/register or test_pages/basic_form.html")
        self.url_input.setFixedHeight(42)

        self.url_validation_label = QLabel("")
        self.url_validation_label.setFont(QFont("-apple-system", 10))
        self.url_validation_label.setStyleSheet(f"color: {COLOR_TEXT_DIM};")

        url_section.addWidget(url_label)
        url_section.addWidget(self.url_input)
        url_section.addWidget(self.url_validation_label)
        card_layout.addLayout(url_section)

        # Profile Selector Section
        profile_section = QVBoxLayout()
        profile_section.setSpacing(8)

        profile_label = QLabel("USER PROFILE (.TXT)")
        profile_label.setFont(QFont("-apple-system", 10, QFont.DemiBold))
        profile_label.setStyleSheet(f"color: {COLOR_TEXT_MUTED}; letter-spacing: 0.5px;")

        profile_row = QHBoxLayout()
        profile_row.setSpacing(10)

        self.profile_combo = QComboBox()
        self.profile_combo.setFixedHeight(38)
        self.profile_combo.setMinimumWidth(320)

        self.btn_browse = SecondaryButton("Browse...")
        self.btn_browse.setFixedHeight(38)

        self.btn_view_profile = SecondaryButton("View / Edit")
        self.btn_view_profile.setFixedHeight(38)

        self.profile_badge = BadgeLabel("NO PROFILE", "WARNING")
        self.profile_badge.setFixedHeight(28)

        profile_row.addWidget(self.profile_combo, stretch=1)
        profile_row.addWidget(self.btn_browse)
        profile_row.addWidget(self.btn_view_profile)
        profile_row.addWidget(self.profile_badge)

        profile_section.addWidget(profile_label)
        profile_section.addLayout(profile_row)
        card_layout.addLayout(profile_section)

        # Start Automation Button
        self.btn_start = PrimaryButton("START AUTOMATION")
        self.btn_start.setFixedHeight(46)
        self.btn_start.setFont(QFont("-apple-system", 11, QFont.Bold))
        card_layout.addWidget(self.btn_start)

        layout.addWidget(action_card)

        # 3. Status Summary Card
        status_card = CardFrame()
        status_card_layout = QHBoxLayout(status_card)
        status_card_layout.setContentsMargins(18, 14, 18, 14)
        status_card_layout.setSpacing(14)

        self.status_badge = BadgeLabel("READY", "SUCCESS")
        self.status_badge.setFixedWidth(70)

        self.status_text = QLabel("Paste a hackathon registration URL to begin.")
        self.status_text.setFont(QFont("-apple-system", 11))
        self.status_text.setStyleSheet(f"color: {COLOR_TEXT_WHITE};")

        status_card_layout.addWidget(self.status_badge)
        status_card_layout.addWidget(self.status_text, stretch=1)
        layout.addWidget(status_card)

        # 4. Recent Activity Log Table
        activity_section = QVBoxLayout()
        activity_section.setSpacing(8)

        activity_label = QLabel("RECENT ACTIVITY")
        activity_label.setFont(QFont("-apple-system", 10, QFont.DemiBold))
        activity_label.setStyleSheet(f"color: {COLOR_TEXT_MUTED}; letter-spacing: 0.5px;")
        activity_section.addWidget(activity_label)

        self.log_table = QTableWidget()
        self.log_table.setColumnCount(3)
        self.log_table.setHorizontalHeaderLabels(["TIME", "LEVEL", "EVENT"])
        self.log_table.horizontalHeader().setSectionResizeMode(0, QHeaderView.ResizeToContents)
        self.log_table.horizontalHeader().setSectionResizeMode(1, QHeaderView.ResizeToContents)
        self.log_table.horizontalHeader().setSectionResizeMode(2, QHeaderView.Stretch)
        self.log_table.verticalHeader().setVisible(False)
        self.log_table.setSelectionBehavior(QTableWidget.SelectRows)
        self.log_table.setEditTriggers(QTableWidget.NoEditTriggers)
        self.log_table.setMinimumHeight(180)

        activity_section.addWidget(self.log_table)
        layout.addLayout(activity_section, stretch=1)

        # Scan for existing profiles in profiles/ directory
        self._populate_profile_combo()

    def _connect_signals(self):
        self.url_input.textChanged.connect(self._validate_current_url)
        self.btn_browse.clicked.connect(self._browse_profile)
        self.btn_view_profile.clicked.connect(self._on_view_profile)
        self.btn_start.clicked.connect(self._on_start_clicked)
        self.profile_combo.currentIndexChanged.connect(self._on_profile_selected)

        # Connect activity logger
        self.logger.entry_added.connect(self._append_log_entry)

    def _validate_current_url(self, text: str):
        text = text.strip()
        if not text:
            self.url_validation_label.setText("")
            return

        # Check local test page convenience
        if text.endswith(".html") and Path(text).exists():
            self.url_validation_label.setText("Local HTML test form detected.")
            self.url_validation_label.setStyleSheet(f"color: {COLOR_TEXT_MUTED};")
            return

        is_valid, msg = validate_url(text, allow_local_file=True)
        if is_valid:
            self.url_validation_label.setText("URL format valid.")
            self.url_validation_label.setStyleSheet(f"color: {COLOR_TEXT_MUTED};")
        else:
            self.url_validation_label.setText(f"Invalid URL: {msg}")
            self.url_validation_label.setStyleSheet("color: #FFFFFF; font-weight: bold;")

    def _populate_profile_combo(self):
        self.profile_combo.clear()
        profiles_dir = Path("profiles")
        found_any = False

        if profiles_dir.exists():
            for p in profiles_dir.glob("*.txt"):
                self.profile_combo.addItem(p.name, str(p.absolute()))
                found_any = True

        if not found_any:
            # Fallback to example_profile if created
            ex = Path("profiles/example_profile.txt")
            if ex.exists():
                self.profile_combo.addItem(ex.name, str(ex.absolute()))
                found_any = True

        if found_any:
            self.selected_profile_path = self.profile_combo.currentData() or ""
            self.profile_badge.set_level("SUCCESS", "PROFILE LOADED")
        else:
            self.profile_badge.set_level("WARNING", "NO PROFILE")

    def _on_profile_selected(self, index: int):
        path = self.profile_combo.itemData(index)
        if path:
            self.selected_profile_path = path
            self.profile_badge.set_level("SUCCESS", "PROFILE LOADED")

    def _browse_profile(self):
        filepath, _ = QFileDialog.getOpenFileName(
            self, "Select Profile File", str(Path("profiles").absolute()), "Text Files (*.txt);;All Files (*)"
        )
        if filepath:
            self.selected_profile_path = filepath
            # Add to combo if not present
            existing_idx = -1
            for i in range(self.profile_combo.count()):
                if self.profile_combo.itemData(i) == filepath:
                    existing_idx = i
                    break
            if existing_idx >= 0:
                self.profile_combo.setCurrentIndex(existing_idx)
            else:
                self.profile_combo.addItem(Path(filepath).name, filepath)
                self.profile_combo.setCurrentIndex(self.profile_combo.count() - 1)

            self.profile_badge.set_level("SUCCESS", "PROFILE LOADED")

    def _on_view_profile(self):
        if self.selected_profile_path:
            self.view_profile_requested.emit(self.selected_profile_path)

    def _on_start_clicked(self):
        url = self.url_input.text().strip()

        # Handle local html test pages convenience (e.g. "test_pages/basic_form.html")
        if url.endswith(".html") and Path(url).exists():
            url = Path(url).absolute().as_uri()

        valid, err = validate_url(url, allow_local_file=True)
        if not valid:
            self.status_badge.set_level("ERROR", "ERROR")
            self.status_text.setText(f"Invalid URL: {err}")
            return

        if not self.selected_profile_path or not Path(self.selected_profile_path).exists():
            self.status_badge.set_level("WARNING", "WARNING")
            self.status_text.setText("Please select a valid user profile (.txt) before starting.")
            return

        self.status_badge.set_level("INFO", "STARTING")
        self.status_text.setText(f"Starting automation for: {url}")
        self.start_automation_requested.emit(url, self.selected_profile_path)

    def _append_log_entry(self, entry: LogEntry):
        row = self.log_table.rowCount()
        self.log_table.insertRow(row)

        time_item = QTableWidgetItem(entry.formatted_time)
        time_item.setTextAlignment(Qt.AlignCenter)
        time_item.setFont(QFont("Consolas", 10))

        level_item = QTableWidgetItem(entry.level.value)
        level_item.setTextAlignment(Qt.AlignCenter)
        level_item.setFont(QFont("Consolas", 9, QFont.Bold))

        msg_item = QTableWidgetItem(entry.message)
        msg_item.setFont(QFont("-apple-system", 10))

        self.log_table.setItem(row, 0, time_item)
        self.log_table.setItem(row, 1, level_item)
        self.log_table.setItem(row, 2, msg_item)
        self.log_table.scrollToBottom()

        # Update status card
        if entry.level.value in ("SUCCESS", "WARNING", "ERROR"):
            self.status_badge.set_level(entry.level.value, entry.level.value)
            self.status_text.setText(entry.message)

    def update_profile_status(self, path: str, is_valid: bool, count: int):
        self.selected_profile_path = path
        if is_valid and count > 0:
            self.profile_badge.set_level("SUCCESS", f"{count} FIELDS")
        else:
            self.profile_badge.set_level("WARNING", "PROFILE WARNINGS")
