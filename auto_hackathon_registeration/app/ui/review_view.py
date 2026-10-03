"""Review View - Mandatory pre-submission review screen with explicit user confirmation."""

from typing import List, Optional, Dict
from PySide6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel, QScrollArea,
    QFrame, QMessageBox, QCheckBox
)
from PySide6.QtCore import Qt, Signal
from PySide6.QtGui import QFont

from .components import (
    CardFrame, PrimaryButton, SecondaryButton, BadgeLabel,
    COLOR_BG_CARD, COLOR_BG_SURFACE, COLOR_BG_BLACK,
    COLOR_TEXT_WHITE, COLOR_TEXT_MUTED, COLOR_TEXT_DIM,
    COLOR_BORDER, COLOR_BORDER_LIGHT, COLOR_WHITE, COLOR_DARK
)
from ..models.form_field import FieldMatch, FieldType
from ..models.scan_result import ScanResult


class ReviewView(QWidget):
    """Mandatory review screen displaying filled, pending, and legal declaration fields."""

    back_requested = Signal()
    submit_confirmed = Signal()

    def __init__(self, parent=None):
        super().__init__(parent)
        self.matches: List[FieldMatch] = []
        self.scan_result: Optional[ScanResult] = None
        self._init_ui()

    def _init_ui(self):
        layout = QVBoxLayout(self)
        layout.setContentsMargins(32, 28, 32, 28)
        layout.setSpacing(20)

        # 1. Header
        header_vbox = QVBoxLayout()
        header_vbox.setSpacing(4)

        title = QLabel("REVIEW REGISTRATION")
        title.setFont(QFont("-apple-system", 20, QFont.Bold))
        title.setStyleSheet(f"color: {COLOR_WHITE}; letter-spacing: -0.5px;")

        subtitle = QLabel("Inspect all populated fields. The application will never submit without your explicit confirmation.")
        subtitle.setFont(QFont("-apple-system", 11))
        subtitle.setStyleSheet(f"color: {COLOR_TEXT_MUTED};")

        header_vbox.addWidget(title)
        header_vbox.addWidget(subtitle)
        layout.addLayout(header_vbox)

        # 2. Scrollable Body
        self.scroll_area = QScrollArea()
        self.scroll_area.setWidgetResizable(True)
        self.scroll_area.setFrameShape(QFrame.NoFrame)
        self.scroll_area.setStyleSheet(f"background-color: {COLOR_BG_BLACK}; border: none;")

        self.scroll_widget = QWidget()
        self.scroll_layout = QVBoxLayout(self.scroll_widget)
        self.scroll_layout.setContentsMargins(0, 0, 8, 0)
        self.scroll_layout.setSpacing(16)
        self.scroll_area.setWidget(self.scroll_widget)

        layout.addWidget(self.scroll_area, stretch=1)

        # 3. Bottom Action Bar
        action_bar = QHBoxLayout()
        action_bar.setSpacing(14)

        self.btn_back = SecondaryButton("Back to Dashboard")
        self.btn_back.setFixedHeight(44)
        self.btn_back.clicked.connect(self.back_requested.emit)

        self.btn_submit = PrimaryButton("SUBMIT REGISTRATION")
        self.btn_submit.setFixedHeight(44)
        self.btn_submit.setFont(QFont("-apple-system", 11, QFont.Bold))
        self.btn_submit.clicked.connect(self._on_submit_clicked)

        action_bar.addWidget(self.btn_back)
        action_bar.addStretch()
        action_bar.addWidget(self.btn_submit)

        layout.addLayout(action_bar)

    def load_review_data(self, matches: List[FieldMatch], scan_result: ScanResult):
        """Populate review sections with detected and filled fields."""
        self.matches = matches
        self.scan_result = scan_result

        # Clear existing review cards
        while self.scroll_layout.count():
            item = self.scroll_layout.takeAt(0)
            widget = item.widget()
            if widget:
                widget.deleteLater()

        # Categorize matches
        personal_matches = []
        education_matches = []
        team_matches = []
        custom_matches = []
        unresolved_matches = []
        legal_matches = []

        for m in matches:
            key = (m.matched_key or "").lower()
            field_name = m.field.identifier_context.lower()

            if m.field.is_terms_or_legal or "terms" in field_name or "conduct" in field_name or "agree" in field_name:
                legal_matches.append(m)
            elif key in ("name", "first_name", "last_name", "email", "phone", "gender", "city", "country"):
                personal_matches.append(m)
            elif key in ("college", "degree", "branch", "year", "graduation_year"):
                education_matches.append(m)
            elif key in ("team_name", "team_size"):
                team_matches.append(m)
            elif key in ("why_participate", "project_idea", "skills", "hackathon_experience") or m.field.field_type == FieldType.TEXTAREA:
                custom_matches.append(m)
            elif m.status in ("UNRESOLVED", "SKIPPED"):
                unresolved_matches.append(m)
            else:
                personal_matches.append(m)

        # 1. Personal Information Card
        if personal_matches:
            self._add_section_card("PERSONAL INFORMATION", personal_matches)

        # 2. Education Card
        if education_matches:
            self._add_section_card("EDUCATION & ACADEMIC DETAILS", education_matches)

        # 3. Team Details Card
        if team_matches:
            self._add_section_card("TEAM DETAILS", team_matches)

        # 4. Custom Questions Card
        if custom_matches:
            self._add_section_card("CUSTOM QUESTIONS & ESSAYS", custom_matches)

        # 5. Declarations & Legal Checkboxes Card
        if legal_matches:
            self._add_legal_card("IMPORTANT DECLARATIONS & TERMS", legal_matches)

        # 6. Unresolved Fields Card
        if unresolved_matches:
            self._add_unresolved_card("FIELDS NOT FILLED / OPTIONAL", unresolved_matches)

        self.scroll_layout.addStretch()

    def _add_section_card(self, title: str, matches: List[FieldMatch]):
        card = CardFrame()
        card_layout = QVBoxLayout(card)
        card_layout.setContentsMargins(20, 18, 20, 18)
        card_layout.setSpacing(12)

        header = QLabel(title)
        header.setFont(QFont("-apple-system", 11, QFont.Bold))
        header.setStyleSheet(f"color: {COLOR_WHITE}; letter-spacing: 0.5px;")
        card_layout.addWidget(header)

        for m in matches:
            row = QHBoxLayout()
            label = QLabel(m.field.display_name)
            label.setFont(QFont("-apple-system", 10))
            label.setStyleSheet(f"color: {COLOR_TEXT_MUTED};")
            label.setFixedWidth(240)

            val_str = m.final_value or "—"
            val = QLabel(val_str)
            val.setFont(QFont("-apple-system", 10, QFont.Medium))
            val.setStyleSheet(f"color: {COLOR_WHITE};")
            val.setWordWrap(True)

            status_badge = BadgeLabel(m.status, "SUCCESS" if m.status == "FILLED" else "INFO")
            status_badge.setFixedWidth(80)

            row.addWidget(label)
            row.addWidget(val, stretch=1)
            row.addWidget(status_badge)
            card_layout.addLayout(row)

        self.scroll_layout.addWidget(card)

    def _add_legal_card(self, title: str, matches: List[FieldMatch]):
        card = CardFrame()
        card.setStyleSheet(f"""
            CardFrame {{
                background-color: #1c1c20;
                border: 1px solid {COLOR_WHITE};
                border-radius: 8px;
            }}
        """)
        card_layout = QVBoxLayout(card)
        card_layout.setContentsMargins(20, 18, 20, 18)
        card_layout.setSpacing(12)

        header = QLabel(title)
        header.setFont(QFont("-apple-system", 11, QFont.Bold))
        header.setStyleSheet(f"color: {COLOR_WHITE}; letter-spacing: 0.5px;")
        card_layout.addWidget(header)

        notice = QLabel("Terms of Service and legal declarations are never automatically accepted. Review each statement below:")
        notice.setFont(QFont("-apple-system", 10))
        notice.setStyleSheet(f"color: {COLOR_TEXT_MUTED};")
        card_layout.addWidget(notice)

        for m in matches:
            cb = QCheckBox(m.field.display_name)
            cb.setFont(QFont("-apple-system", 10))
            cb.setStyleSheet(f"color: {COLOR_WHITE};")
            # When user checks this in the review UI, mark match as filled
            cb.stateChanged.connect(lambda state, match=m: self._on_legal_toggle(state, match))
            card_layout.addWidget(cb)

        self.scroll_layout.addWidget(card)

    def _on_legal_toggle(self, state, match: FieldMatch):
        match.status = "FILLED" if state == Qt.Checked else "MANUAL_REQUIRED"
        match.user_override_value = "yes" if state == Qt.Checked else ""

    def _add_unresolved_card(self, title: str, matches: List[FieldMatch]):
        card = CardFrame()
        card_layout = QVBoxLayout(card)
        card_layout.setContentsMargins(20, 18, 20, 18)
        card_layout.setSpacing(12)

        header = QLabel(title)
        header.setFont(QFont("-apple-system", 11, QFont.Bold))
        header.setStyleSheet(f"color: {COLOR_TEXT_MUTED}; letter-spacing: 0.5px;")
        card_layout.addWidget(header)

        for m in matches:
            row = QHBoxLayout()
            label = QLabel(f"○ {m.field.display_name}")
            label.setFont(QFont("-apple-system", 10))
            label.setStyleSheet(f"color: {COLOR_TEXT_DIM};")

            type_lbl = QLabel(f"[{m.field.field_type.value}]")
            type_lbl.setFont(QFont("Consolas", 9))
            type_lbl.setStyleSheet(f"color: {COLOR_TEXT_DIM};")

            row.addWidget(label, stretch=1)
            row.addWidget(type_lbl)
            card_layout.addLayout(row)

        self.scroll_layout.addWidget(card)

    def _on_submit_clicked(self):
        """Require explicit confirmation dialog before final submission."""
        dialog = QMessageBox(self)
        dialog.setWindowTitle("Confirm Final Registration Submission")
        dialog.setText("Are you sure you want to submit this hackathon registration?")
        dialog.setInformativeText("The controlled browser will click the final registration button. This action cannot be undone.")
        dialog.setStandardButtons(QMessageBox.Yes | QMessageBox.Cancel)
        dialog.setDefaultButton(QMessageBox.Cancel)
        dialog.setStyleSheet(f"""
            QMessageBox {{
                background-color: {COLOR_BG_CARD};
                color: {COLOR_TEXT_WHITE};
            }}
            QPushButton {{
                background-color: {COLOR_WHITE};
                color: {COLOR_DARK};
                border-radius: 4px;
                padding: 6px 16px;
                font-weight: 600;
            }}
        """)

        reply = dialog.exec()
        if reply == QMessageBox.Yes:
            self.submit_confirmed.emit()
