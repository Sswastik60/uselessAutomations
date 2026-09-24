"""Polished Main Dashboard View displaying user Modes in a responsive grid."""

from datetime import datetime
from typing import List, Optional
from PySide6.QtCore import Qt, Signal
from PySide6.QtWidgets import (
    QFileDialog,
    QFrame,
    QGridLayout,
    QHBoxLayout,
    QLabel,
    QLineEdit,
    QPushButton,
    QScrollArea,
    QVBoxLayout,
    QWidget,
)

from app.models.mode import Mode
from app.ui.animation_manager import AnimationManager
from app.ui.styles.design_tokens import AnimationDuration, DarkPalette
from app.ui.widgets.mode_card import ModeCard
from app.ui.widgets.status_indicator import StatusIndicator


class DashboardView(QWidget):
    """Main Dashboard view prioritizing Modes over configuration."""

    run_mode_requested = Signal(str)        # mode_id
    edit_mode_requested = Signal(str)       # mode_id
    create_mode_requested = Signal()
    import_mode_requested = Signal(str)     # path
    export_mode_requested = Signal(str)     # mode_id
    duplicate_mode_requested = Signal(str)  # mode_id
    delete_mode_requested = Signal(str)     # mode_id

    def __init__(self, parent=None):
        super().__init__(parent)
        self.all_modes: List[Mode] = []
        self._current_filtered_modes: List[Mode] = []

        main_layout = QVBoxLayout(self)
        main_layout.setContentsMargins(24, 24, 24, 24)
        main_layout.setSpacing(20)

        # 1. Greeting & Title Header Row
        header_layout = QHBoxLayout()
        
        title_box = QVBoxLayout()
        title_box.setSpacing(2)

        # Dynamic greeting based on time of day
        hour = datetime.now().hour
        greeting = "Good morning" if hour < 12 else ("Good afternoon" if hour < 18 else "Good evening")

        self.greeting_lbl = QLabel(f"{greeting}")
        self.greeting_lbl.setStyleSheet(f"font-size: 13px; font-weight: 600; color: {DarkPalette.TEXT_MUTED}; text-transform: uppercase; letter-spacing: 0.8px;")
        title_box.addWidget(self.greeting_lbl)

        self.title_lbl = QLabel("What are you doing today?")
        self.title_lbl.setStyleSheet(f"font-size: 24px; font-weight: 800; color: {DarkPalette.TEXT_PRIMARY}; letter-spacing: -0.5px;")
        title_box.addWidget(self.title_lbl)

        header_layout.addLayout(title_box)
        header_layout.addStretch()

        # Search Bar
        self.search_input = QLineEdit()
        self.search_input.setPlaceholderText("🔍  Search modes or hotkeys... (Ctrl+K)")
        self.search_input.setClearButtonEnabled(True)
        self.search_input.setFixedWidth(240)
        self.search_input.textChanged.connect(self._filter_modes)
        header_layout.addWidget(self.search_input)

        # Import & New Mode Buttons
        self.import_mode_btn = QPushButton("📥  Import JSON")
        self.import_mode_btn.setProperty("class", "SecondaryButton")
        self.import_mode_btn.clicked.connect(self._on_import_clicked)

        self.new_mode_btn = QPushButton("+  New Mode")
        self.new_mode_btn.setProperty("class", "PrimaryButton")
        self.new_mode_btn.clicked.connect(self.create_mode_requested.emit)

        header_layout.addWidget(self.import_mode_btn)
        header_layout.addWidget(self.new_mode_btn)

        main_layout.addLayout(header_layout)

        # 2. Scrollable Responsive Grid of Mode Cards
        scroll = QScrollArea()
        scroll.setWidgetResizable(True)
        scroll.setStyleSheet("QScrollArea { border: none; background: transparent; }")

        self.grid_container = QWidget()
        self.grid_layout = QGridLayout(self.grid_container)
        self.grid_layout.setContentsMargins(0, 0, 0, 0)
        self.grid_layout.setSpacing(18)
        scroll.setWidget(self.grid_container)

        main_layout.addWidget(scroll, stretch=1)

        # 3. Bottom System Hardware Status Bar
        status_bar = QFrame()
        status_bar.setStyleSheet(
            """
            QFrame {
                background-color: #080808;
                border: 1px solid #181818;
                border-radius: 12px;
                padding: 10px 18px;
            }
            """
        )
        sb_layout = QHBoxLayout(status_bar)
        sb_layout.setContentsMargins(12, 8, 12, 8)
        sb_layout.setSpacing(24)

        self.audio_status = StatusIndicator("Audio: Scanning...", active=True)
        self.midi_status = StatusIndicator("MIDI: Scanning...", active=True)
        self.mode_status_lbl = QLabel("Active Mode: <b>None</b>")
        self.mode_status_lbl.setStyleSheet("color: #94a3b8; font-size: 12px;")

        sb_layout.addWidget(self.audio_status)
        sb_layout.addWidget(self.midi_status)
        sb_layout.addStretch()
        sb_layout.addWidget(self.mode_status_lbl)

        main_layout.addWidget(status_bar)

    def update_modes(self, modes: List[Mode]) -> None:
        """Refresh mode cards grid."""
        self.all_modes = modes
        self._filter_modes(self.search_input.text())

    def _filter_modes(self, query: str) -> None:
        """Filter modes by search query."""
        q = query.strip().lower()
        if not q:
            self._current_filtered_modes = self.all_modes
        else:
            self._current_filtered_modes = [
                m for m in self.all_modes
                if q in m.name.lower()
                or q in m.description.lower()
                or (m.hotkey and q in m.hotkey.lower())
                or q in m.id.lower()
            ]
        self._render_modes(self._current_filtered_modes)

    def resizeEvent(self, event) -> None:
        """Recalculate grid columns responsively on window resize."""
        super().resizeEvent(event)
        if hasattr(self, "_current_filtered_modes") and self._current_filtered_modes:
            self._render_modes(self._current_filtered_modes)

    def _render_modes(self, modes: List[Mode]) -> None:
        # Clear existing grid widgets
        while self.grid_layout.count():
            item = self.grid_layout.takeAt(0)
            if item.widget():
                item.widget().deleteLater()

        if not modes:
            empty_card = QFrame()
            empty_card.setStyleSheet(
                """
                QFrame {
                    background-color: #080808;
                    border: 1px dashed #262626;
                    border-radius: 14px;
                    padding: 40px;
                }
                """
            )
            empty_layout = QVBoxLayout(empty_card)
            empty_layout.setAlignment(Qt.AlignmentFlag.AlignCenter)
            empty_layout.setSpacing(12)

            icon_lbl = QLabel("⚡")
            icon_lbl.setStyleSheet("font-size: 36px; color: #38bdf8;")
            empty_lbl = QLabel("No Modes Configured")
            empty_lbl.setStyleSheet("color: #f8fafc; font-size: 18px; font-weight: 700;")
            empty_sub = QLabel("Create your first Mode and turn a multi-step computer setup into one button.")
            empty_sub.setStyleSheet("color: #94a3b8; font-size: 13px;")

            create_btn = QPushButton("+ Create Mode")
            create_btn.setProperty("class", "PrimaryButton")
            create_btn.setFixedWidth(160)
            create_btn.clicked.connect(self.create_mode_requested.emit)

            empty_layout.addWidget(icon_lbl, alignment=Qt.AlignmentFlag.AlignCenter)
            empty_layout.addWidget(empty_lbl, alignment=Qt.AlignmentFlag.AlignCenter)
            empty_layout.addWidget(empty_sub, alignment=Qt.AlignmentFlag.AlignCenter)
            empty_layout.addWidget(create_btn, alignment=Qt.AlignmentFlag.AlignCenter)

            self.grid_layout.addWidget(empty_card, 0, 0, 1, 3)
            return

        # Calculate responsive columns (minimum card width 290px)
        w = self.width() - 48
        columns = max(1, min(4, w // 300))

        for idx, mode in enumerate(modes):
            card = ModeCard(mode)
            card.run_requested.connect(self.run_mode_requested.emit)
            card.edit_requested.connect(self.edit_mode_requested.emit)
            card.export_requested.connect(self.export_mode_requested.emit)
            card.duplicate_requested.connect(self.duplicate_mode_requested.emit)
            card.delete_requested.connect(self.delete_mode_requested.emit)

            row = idx // columns
            col = idx % columns
            self.grid_layout.addWidget(card, row, col)

    def _on_import_clicked(self) -> None:
        file_path, _ = QFileDialog.getOpenFileName(
            self, "Import Automation Mode JSON", "", "JSON Files (*.json);;All Files (*.*)"
        )
        if file_path:
            self.import_mode_requested.emit(file_path)

    def update_system_status(self, audio_info: str, midi_info: str, running_mode: Optional[str] = None) -> None:
        """Update bottom system hardware status bar."""
        self.audio_status.set_active(True, f"Audio: {audio_info}")
        self.midi_status.set_active(True, f"MIDI: {midi_info}")
        if running_mode:
            self.mode_status_lbl.setText(f"Active Mode: <b style='color: #10b981;'>{running_mode}</b>")
        else:
            self.mode_status_lbl.setText("Active Mode: <b>None</b>")
