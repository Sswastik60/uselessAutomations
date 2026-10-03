"""Automation View - Real-time monitor of form detection, field matching, filling, and interventions."""

from typing import List, Optional
from PySide6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel, QTableWidget,
    QTableWidgetItem, QHeaderView, QLineEdit, QSplitter
)
from PySide6.QtCore import Qt, Signal
from PySide6.QtGui import QFont

from .components import (
    CardFrame, PrimaryButton, SecondaryButton, DangerButton,
    BadgeLabel, MonochromeProgressBar, COLOR_BG_CARD, COLOR_BG_SURFACE,
    COLOR_TEXT_WHITE, COLOR_TEXT_MUTED, COLOR_TEXT_DIM, COLOR_BORDER, COLOR_WHITE
)
from ..models.form_field import FieldMatch
from ..models.scan_result import AutomationStatus
from ..services.logger import LogEntry, get_logger


class AutomationView(QWidget):
    """Real-time monitoring panel displaying automation pipeline, progress, and manual interventions."""

    stop_requested = Signal()
    manual_continue_requested = Signal()
    custom_field_resolved = Signal(object, str)  # (FieldMatch, answer_text)
    skip_field_requested = Signal(object)        # (FieldMatch)

    def __init__(self, parent=None):
        super().__init__(parent)
        self.logger = get_logger()
        self.current_pending_match: Optional[FieldMatch] = None
        self._init_ui()
        self._connect_signals()

    def _init_ui(self):
        layout = QVBoxLayout(self)
        layout.setContentsMargins(32, 28, 32, 28)
        layout.setSpacing(18)

        # 1. Top Header Bar
        top_bar = QHBoxLayout()
        header_vbox = QVBoxLayout()
        header_vbox.setSpacing(4)

        title = QLabel("AUTOMATION MONITOR")
        title.setFont(QFont("-apple-system", 16, QFont.Bold))
        title.setStyleSheet(f"color: {COLOR_WHITE}; letter-spacing: -0.5px;")

        self.website_label = QLabel("Website: Waiting to connect...")
        self.website_label.setFont(QFont("-apple-system", 11))
        self.website_label.setStyleSheet(f"color: {COLOR_TEXT_MUTED};")

        header_vbox.addWidget(title)
        header_vbox.addWidget(self.website_label)
        top_bar.addLayout(header_vbox, stretch=1)

        self.status_badge = BadgeLabel("IDLE", "INFO")
        self.status_badge.setFixedHeight(30)
        top_bar.addWidget(self.status_badge)

        self.btn_stop = DangerButton("STOP AUTOMATION")
        self.btn_stop.setFixedHeight(38)
        top_bar.addWidget(self.btn_stop)

        layout.addLayout(top_bar)

        # 2. Pipeline Step Indicator
        pipeline_card = CardFrame()
        pipeline_layout = QHBoxLayout(pipeline_card)
        pipeline_layout.setContentsMargins(16, 12, 16, 12)
        pipeline_layout.setSpacing(10)

        self.step_connecting = BadgeLabel("1. CONNECTING", "INFO")
        self.step_scanning = BadgeLabel("2. SCANNING", "INFO")
        self.step_matching = BadgeLabel("3. MATCHING", "INFO")
        self.step_filling = BadgeLabel("4. FILLING", "INFO")
        self.step_review = BadgeLabel("5. REVIEW", "INFO")

        for step in (self.step_connecting, self.step_scanning, self.step_matching, self.step_filling, self.step_review):
            pipeline_layout.addWidget(step)

        layout.addWidget(pipeline_card)

        # 3. Progress Section
        progress_card = CardFrame()
        progress_layout = QVBoxLayout(progress_card)
        progress_layout.setContentsMargins(18, 14, 18, 14)
        progress_layout.setSpacing(10)

        prog_header = QHBoxLayout()
        self.progress_title = QLabel("FORM FILLING PROGRESS")
        self.progress_title.setFont(QFont("-apple-system", 10, QFont.DemiBold))
        self.progress_title.setStyleSheet(f"color: {COLOR_TEXT_MUTED};")

        self.progress_count_label = QLabel("0 / 0 fields populated")
        self.progress_count_label.setFont(QFont("-apple-system", 10, QFont.Bold))
        self.progress_count_label.setStyleSheet(f"color: {COLOR_WHITE};")

        prog_header.addWidget(self.progress_title)
        prog_header.addStretch()
        prog_header.addWidget(self.progress_count_label)
        progress_layout.addLayout(prog_header)

        self.progress_bar = MonochromeProgressBar()
        progress_layout.addWidget(self.progress_bar)
        layout.addWidget(progress_card)

        # 4. Human Intervention Alert Banner (Hidden by default)
        self.intervention_card = CardFrame()
        self.intervention_card.setStyleSheet(f"""
            CardFrame {{
                background-color: #27272A;
                border: 2px solid {COLOR_WHITE};
                border-radius: 8px;
            }}
        """)
        interv_layout = QVBoxLayout(self.intervention_card)
        interv_layout.setContentsMargins(20, 16, 20, 16)
        interv_layout.setSpacing(12)

        interv_title_row = QHBoxLayout()
        interv_badge = BadgeLabel("MANUAL ACTION REQUIRED", "SUCCESS")
        self.interv_desc = QLabel("Complete the verification in the browser, then click Continue.")
        self.interv_desc.setFont(QFont("-apple-system", 11, QFont.Bold))
        self.interv_desc.setStyleSheet(f"color: {COLOR_WHITE};")

        interv_title_row.addWidget(interv_badge)
        interv_title_row.addWidget(self.interv_desc, stretch=1)
        interv_layout.addLayout(interv_title_row)

        interv_btn_row = QHBoxLayout()
        interv_btn_row.addStretch()

        self.btn_interv_continue = PrimaryButton("CONTINUE")
        self.btn_interv_continue.setFixedHeight(36)

        self.btn_interv_stop = DangerButton("STOP")
        self.btn_interv_stop.setFixedHeight(36)

        interv_btn_row.addWidget(self.btn_interv_stop)
        interv_btn_row.addWidget(self.btn_interv_continue)
        interv_layout.addLayout(interv_btn_row)

        self.intervention_card.setVisible(False)
        layout.addWidget(self.intervention_card)

        # 5. Custom Question / Uncertain Field Card (Hidden by default)
        self.question_card = CardFrame()
        q_layout = QVBoxLayout(self.question_card)
        q_layout.setContentsMargins(20, 16, 20, 16)
        q_layout.setSpacing(10)

        q_badge = BadgeLabel("CUSTOM QUESTION DETECTED", "WARNING")
        q_layout.addWidget(q_badge)

        self.question_label = QLabel("Question Text")
        self.question_label.setFont(QFont("-apple-system", 12, QFont.Bold))
        self.question_label.setStyleSheet(f"color: {COLOR_WHITE};")
        q_layout.addWidget(self.question_label)

        self.question_input = QLineEdit()
        self.question_input.setPlaceholderText("Enter your answer...")
        self.question_input.setFixedHeight(38)
        q_layout.addWidget(self.question_input)

        q_btn_row = QHBoxLayout()
        q_btn_row.addStretch()

        self.btn_skip_question = SecondaryButton("Skip Question")
        self.btn_skip_question.setFixedHeight(34)

        self.btn_use_answer = PrimaryButton("Use Answer & Continue")
        self.btn_use_answer.setFixedHeight(34)

        q_btn_row.addWidget(self.btn_skip_question)
        q_btn_row.addWidget(self.btn_use_answer)
        q_layout.addLayout(q_btn_row)

        self.question_card.setVisible(False)
        layout.addWidget(self.question_card)

        # 6. Detected Fields Table
        fields_header = QLabel("DETECTED FORM FIELDS")
        fields_header.setFont(QFont("-apple-system", 10, QFont.DemiBold))
        fields_header.setStyleSheet(f"color: {COLOR_TEXT_MUTED}; letter-spacing: 0.5px;")
        layout.addWidget(fields_header)

        self.fields_table = QTableWidget()
        self.fields_table.setColumnCount(5)
        self.fields_table.setHorizontalHeaderLabels(["FIELD NAME", "TYPE", "MATCHED VALUE", "CONFIDENCE", "STATUS"])
        self.fields_table.horizontalHeader().setSectionResizeMode(0, QHeaderView.ResizeToContents)
        self.fields_table.horizontalHeader().setSectionResizeMode(1, QHeaderView.ResizeToContents)
        self.fields_table.horizontalHeader().setSectionResizeMode(2, QHeaderView.Stretch)
        self.fields_table.horizontalHeader().setSectionResizeMode(3, QHeaderView.ResizeToContents)
        self.fields_table.horizontalHeader().setSectionResizeMode(4, QHeaderView.ResizeToContents)
        self.fields_table.verticalHeader().setVisible(False)
        self.fields_table.setSelectionBehavior(QTableWidget.SelectRows)
        self.fields_table.setEditTriggers(QTableWidget.NoEditTriggers)

        layout.addWidget(self.fields_table, stretch=1)

    def _connect_signals(self):
        self.btn_stop.clicked.connect(self.stop_requested.emit)
        self.btn_interv_continue.clicked.connect(self._on_manual_continue)
        self.btn_interv_stop.clicked.connect(self.stop_requested.emit)
        self.btn_use_answer.clicked.connect(self._on_use_answer)
        self.btn_skip_question.clicked.connect(self._on_skip_question)

    def set_target_url(self, url: str, browser_name: str = "Chromium"):
        self.website_label.setText(f"Website: {url} • Engine: {browser_name}")
        self.fields_table.setRowCount(0)
        self.progress_bar.setValue(0)
        self.progress_count_label.setText("0 / 0 fields populated")
        self.intervention_card.setVisible(False)
        self.question_card.setVisible(False)

    def update_pipeline_status(self, status: AutomationStatus, message: str = ""):
        self.status_badge.set_level("INFO", status.value)

        # Reset all steps to muted
        for s in (self.step_connecting, self.step_scanning, self.step_matching, self.step_filling, self.step_review):
            s.set_level("INFO")

        if status == AutomationStatus.CONNECTING:
            self.step_connecting.set_level("SUCCESS")
        elif status == AutomationStatus.SCANNING:
            self.step_scanning.set_level("SUCCESS")
        elif status == AutomationStatus.MATCHING:
            self.step_matching.set_level("SUCCESS")
        elif status == AutomationStatus.FILLING:
            self.step_filling.set_level("SUCCESS")
        elif status == AutomationStatus.WAITING_REVIEW:
            self.step_review.set_level("SUCCESS")
        elif status == AutomationStatus.WAITING_MANUAL:
            self.status_badge.set_level("WARNING", "MANUAL REQUIRED")
        elif status == AutomationStatus.COMPLETED:
            self.status_badge.set_level("SUCCESS", "COMPLETED")
        elif status == AutomationStatus.ERROR:
            self.status_badge.set_level("ERROR", "ERROR")
        elif status == AutomationStatus.STOPPED:
            self.status_badge.set_level("WARNING", "STOPPED")

    def show_intervention(self, reason: str):
        self.interv_desc.setText(reason)
        self.intervention_card.setVisible(True)

    def hide_intervention(self):
        self.intervention_card.setVisible(False)

    def _on_manual_continue(self):
        self.intervention_card.setVisible(False)
        self.manual_continue_requested.emit()

    def show_custom_question(self, match: FieldMatch):
        self.current_pending_match = match
        self.question_label.setText(match.field.display_name)
        self.question_input.setText(match.matched_value or "")
        self.question_input.setFocus()
        self.question_card.setVisible(True)

    def _on_use_answer(self):
        answer = self.question_input.text().strip()
        if self.current_pending_match:
            match = self.current_pending_match
            self.current_pending_match = None
            self.question_card.setVisible(False)
            self.custom_field_resolved.emit(match, answer)

    def _on_skip_question(self):
        if self.current_pending_match:
            match = self.current_pending_match
            self.current_pending_match = None
            self.question_card.setVisible(False)
            self.skip_field_requested.emit(match)

    def update_progress(self, filled: int, total: int):
        self.progress_count_label.setText(f"{filled} / {total} fields populated")
        if total > 0:
            pct = int((filled / total) * 100)
            self.progress_bar.setValue(pct)

    def update_fields_list(self, matches: List[FieldMatch]):
        self.fields_table.setRowCount(0)
        for row, match in enumerate(matches):
            self.fields_table.insertRow(row)

            # Field Name
            name_item = QTableWidgetItem(match.field.display_name)
            name_item.setFont(QFont("-apple-system", 10, QFont.Medium))

            # Type
            type_item = QTableWidgetItem(match.field.field_type.value)
            type_item.setTextAlignment(Qt.AlignCenter)
            type_item.setFont(QFont("Consolas", 9))

            # Matched Value
            val_text = match.final_value or "—"
            val_item = QTableWidgetItem(val_text)
            val_item.setFont(QFont("-apple-system", 10))

            # Confidence
            conf_item = QTableWidgetItem(f"{match.confidence_percent}%")
            conf_item.setTextAlignment(Qt.AlignCenter)
            conf_item.setFont(QFont("Consolas", 10, QFont.Bold))

            # Status Badge
            status_item = QTableWidgetItem(match.status)
            status_item.setTextAlignment(Qt.AlignCenter)
            status_item.setFont(QFont("Consolas", 9, QFont.Bold))

            self.fields_table.setItem(row, 0, name_item)
            self.fields_table.setItem(row, 1, type_item)
            self.fields_table.setItem(row, 2, val_item)
            self.fields_table.setItem(row, 3, conf_item)
            self.fields_table.setItem(row, 4, status_item)

        self.fields_table.scrollToBottom()
