"""Profile View - Manage, inspect, validate, and create TXT profiles."""

import os
import subprocess
from pathlib import Path
from typing import Optional
from PySide6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel, QTableWidget,
    QTableWidgetItem, QHeaderView, QFileDialog, QMessageBox, QListWidget, QListWidgetItem
)
from PySide6.QtCore import Qt, Signal
from PySide6.QtGui import QFont

from .components import (
    CardFrame, PrimaryButton, SecondaryButton, BadgeLabel,
    COLOR_BG_CARD, COLOR_BG_SURFACE, COLOR_BG_BLACK,
    COLOR_TEXT_WHITE, COLOR_TEXT_MUTED, COLOR_TEXT_DIM,
    COLOR_BORDER, COLOR_WHITE
)
from ..models.profile import UserProfile
from ..profile.parser import ProfileParser
from ..profile.validator import ProfileValidator
from ..services.logger import get_logger


class ProfileView(QWidget):
    """Screen for loading, viewing, validating, and generating user profiles."""

    profile_updated = Signal(str, bool, int)  # (path, is_valid, field_count)

    def __init__(self, parent=None):
        super().__init__(parent)
        self.logger = get_logger()
        self.current_profile: Optional[UserProfile] = None
        self.current_path: str = ""
        self._init_ui()
        self._connect_signals()

    def _init_ui(self):
        layout = QVBoxLayout(self)
        layout.setContentsMargins(32, 28, 32, 28)
        layout.setSpacing(20)

        # 1. Header & Actions Toolbar
        top_row = QHBoxLayout()
        header_vbox = QVBoxLayout()
        header_vbox.setSpacing(4)

        title = QLabel("PROFILE MANAGEMENT")
        title.setFont(QFont("-apple-system", 18, QFont.Bold))
        title.setStyleSheet(f"color: {COLOR_WHITE}; letter-spacing: -0.5px;")

        self.path_label = QLabel("No profile selected.")
        self.path_label.setFont(QFont("-apple-system", 11))
        self.path_label.setStyleSheet(f"color: {COLOR_TEXT_MUTED};")

        header_vbox.addWidget(title)
        header_vbox.addWidget(self.path_label)
        top_row.addLayout(header_vbox, stretch=1)

        self.validation_badge = BadgeLabel("NOT LOADED", "INFO")
        self.validation_badge.setFixedHeight(30)
        top_row.addWidget(self.validation_badge)

        layout.addLayout(top_row)

        # Toolbar
        toolbar_card = CardFrame()
        toolbar_layout = QHBoxLayout(toolbar_card)
        toolbar_layout.setContentsMargins(14, 10, 14, 10)
        toolbar_layout.setSpacing(10)

        self.btn_browse = SecondaryButton("Select Profile (.txt)")
        self.btn_reload = SecondaryButton("Reload")
        self.btn_validate = SecondaryButton("Validate Profile")
        self.btn_open_folder = SecondaryButton("Open File Location")
        self.btn_create_example = PrimaryButton("Create Example Profile")

        toolbar_layout.addWidget(self.btn_browse)
        toolbar_layout.addWidget(self.btn_reload)
        toolbar_layout.addWidget(self.btn_validate)
        toolbar_layout.addWidget(self.btn_open_folder)
        toolbar_layout.addStretch()
        toolbar_layout.addWidget(self.btn_create_example)

        layout.addWidget(toolbar_card)

        # 2. Parsed Fields Table
        fields_label = QLabel("PARSED ATTRIBUTES")
        fields_label.setFont(QFont("-apple-system", 10, QFont.DemiBold))
        fields_label.setStyleSheet(f"color: {COLOR_TEXT_MUTED}; letter-spacing: 0.5px;")
        layout.addWidget(fields_label)

        self.fields_table = QTableWidget()
        self.fields_table.setColumnCount(4)
        self.fields_table.setHorizontalHeaderLabels(["SECTION", "KEY", "VALUE", "LINE #"])
        self.fields_table.horizontalHeader().setSectionResizeMode(0, QHeaderView.ResizeToContents)
        self.fields_table.horizontalHeader().setSectionResizeMode(1, QHeaderView.ResizeToContents)
        self.fields_table.horizontalHeader().setSectionResizeMode(2, QHeaderView.Stretch)
        self.fields_table.horizontalHeader().setSectionResizeMode(3, QHeaderView.ResizeToContents)
        self.fields_table.verticalHeader().setVisible(False)
        self.fields_table.setSelectionBehavior(QTableWidget.SelectRows)
        self.fields_table.setEditTriggers(QTableWidget.NoEditTriggers)

        layout.addWidget(self.fields_table, stretch=2)

        # 3. Validation Diagnostics Section
        diag_label = QLabel("VALIDATION DIAGNOSTICS")
        diag_label.setFont(QFont("-apple-system", 10, QFont.DemiBold))
        diag_label.setStyleSheet(f"color: {COLOR_TEXT_MUTED}; letter-spacing: 0.5px;")
        layout.addWidget(diag_label)

        self.diag_list = QListWidget()
        self.diag_list.setFixedHeight(110)
        self.diag_list.setStyleSheet(f"""
            QListWidget {{
                background-color: {COLOR_BG_CARD};
                border: 1px solid {COLOR_BORDER};
                border-radius: 6px;
                padding: 6px;
                font-family: Consolas, monospace;
                font-size: 11px;
            }}
        """)
        layout.addWidget(self.diag_list, stretch=1)

    def _connect_signals(self):
        self.btn_browse.clicked.connect(self._on_browse)
        self.btn_reload.clicked.connect(self.reload_profile)
        self.btn_validate.clicked.connect(self.validate_current)
        self.btn_open_folder.clicked.connect(self._on_open_location)
        self.btn_create_example.clicked.connect(self._on_create_example)

    def load_profile_path(self, filepath: str):
        self.current_path = filepath
        self.reload_profile()

    def reload_profile(self):
        if not self.current_path or not Path(self.current_path).exists():
            self.path_label.setText("No profile found at specified location.")
            self.validation_badge.set_level("WARNING", "NOT FOUND")
            return

        self.path_label.setText(f"Active Profile: {self.current_path}")
        profile, parse_issues = ProfileParser.parse_file(self.current_path)
        self.current_profile = profile

        # Update table
        self.fields_table.setRowCount(0)
        for row, entry in enumerate(profile.raw_entries):
            self.fields_table.insertRow(row)

            sec_item = QTableWidgetItem(entry.section or "General")
            sec_item.setFont(QFont("-apple-system", 9, QFont.DemiBold))
            sec_item.setTextAlignment(Qt.AlignCenter)

            key_item = QTableWidgetItem(entry.key)
            key_item.setFont(QFont("Consolas", 10))

            val_item = QTableWidgetItem(entry.value)
            val_item.setFont(QFont("-apple-system", 10))

            line_item = QTableWidgetItem(str(entry.line_number))
            line_item.setTextAlignment(Qt.AlignCenter)
            line_item.setFont(QFont("Consolas", 9))

            self.fields_table.setItem(row, 0, sec_item)
            self.fields_table.setItem(row, 1, key_item)
            self.fields_table.setItem(row, 2, val_item)
            self.fields_table.setItem(row, 3, line_item)

        # Validate
        res = ProfileValidator.validate(profile)
        self.diag_list.clear()

        # Combine parse issues and validator issues
        all_issues = parse_issues + res.issues

        if not all_issues:
            self.validation_badge.set_level("SUCCESS", f"VALID ({len(profile)} FIELDS)")
            self.diag_list.addItem("✓ All fields syntactically and semantically valid.")
        else:
            if res.error_count > 0:
                self.validation_badge.set_level("ERROR", f"{res.error_count} ERRORS")
            else:
                self.validation_badge.set_level("WARNING", f"{len(all_issues)} WARNINGS")

            for issue in all_issues:
                prefix = "[ERROR]" if issue.severity == "ERROR" else "[WARN]"
                line_str = f" Line {issue.line_number}:" if issue.line_number else ""
                self.diag_list.addItem(f"{prefix}{line_str} {issue.message}")

        self.profile_updated.emit(self.current_path, res.is_valid, len(profile))
        self.logger.info(f"Loaded profile '{Path(self.current_path).name}' ({len(profile)} fields)")

    def validate_current(self):
        self.reload_profile()
        QMessageBox.information(
            self, "Profile Validation",
            f"Validation complete for '{Path(self.current_path).name}'.\n"
            f"Fields detected: {len(self.current_profile) if self.current_profile else 0}"
        )

    def _on_browse(self):
        filepath, _ = QFileDialog.getOpenFileName(
            self, "Open Profile File", str(Path("profiles").absolute()), "Text Files (*.txt);;All Files (*)"
        )
        if filepath:
            self.load_profile_path(filepath)

    def _on_open_location(self):
        if self.current_path and Path(self.current_path).exists():
            folder = str(Path(self.current_path).parent.absolute())
            if os.name == "nt":
                os.startfile(folder)
            else:
                subprocess.Popen(["xdg-open", folder])
        else:
            QMessageBox.warning(self, "Notice", "No active profile file exists yet.")

    def _on_create_example(self):
        default_dir = Path("profiles")
        default_dir.mkdir(parents=True, exist_ok=True)
        example_path = default_dir / "example_profile.txt"

        if not example_path.exists():
            # Create standard example content
            content = (
                "# Personal Information\n"
                "name=Swastik\n"
                "email=swastik@example.com\n"
                "phone=9876543210\n"
                "gender=Male\n\n"
                "# Education\n"
                "college=Example University\n"
                "degree=B.Tech\n"
                "branch=Computer Science and Engineering\n"
                "year=3\n"
                "graduation_year=2026\n\n"
                "# Location\n"
                "city=Bengaluru\n"
                "country=India\n\n"
                "# Links\n"
                "github=https://github.com/example\n"
                "linkedin=https://linkedin.com/in/example\n"
                "portfolio=https://example.com\n\n"
                "# Team Details\n"
                "team_name=ByteForce\n"
                "team_size=3\n\n"
                "# Hackathon Experience\n"
                "skills=Python, C++, JavaScript, React\n"
                "hackathon_experience=Yes\n"
                "why_participate=I want to build practical projects and learn from other developers.\n"
            )
            with open(example_path, "w", encoding="utf-8") as f:
                f.write(content)

        self.load_profile_path(str(example_path.absolute()))
        QMessageBox.information(
            self, "Example Profile Ready",
            f"Created and loaded example profile at:\n{example_path.absolute()}"
        )
