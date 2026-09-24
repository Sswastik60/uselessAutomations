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
from app.ui.widgets.mode_card import ModeCard
from app.ui.widgets.status_indicator import StatusIndicator


class DashboardView(QWidget):
    """Main Dashboard view displaying user Modes in a responsive card grid."""

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

        main_layout = QVBoxLayout(self)
        main_layout.setContentsMargins(24, 24, 24, 24)
        main_layout.setSpacing(20)

        # Header Row
        header_layout = QHBoxLayout()
        title_lbl = QLabel("Automation Modes")
        title_lbl.setStyleSheet("font-size: 24px; font-weight: 800; color: #f8fafc; letter-spacing: -0.5px;")

        self.count_lbl = QLabel("(0 Modes)")
        self.count_lbl.setStyleSheet("font-size: 14px; color: #94a3b8; margin-top: 6px; font-weight: 500;")

        # Search Bar
        self.search_input = QLineEdit()
        self.search_input.setPlaceholderText("🔍  Search modes or hotkeys...")
        self.search_input.setClearButtonEnabled(True)
        self.search_input.setFixedWidth(220)
        self.search_input.textChanged.connect(self._filter_modes)

        # Import & New Mode Buttons
        self.import_mode_btn = QPushButton("📥  Import JSON")
        self.import_mode_btn.setProperty("class", "SecondaryButton")
        self.import_mode_btn.clicked.connect(self._on_import_clicked)

        self.new_mode_btn = QPushButton("+  New Mode")
        self.new_mode_btn.setProperty("class", "PrimaryButton")
        self.new_mode_btn.clicked.connect(self.create_mode_requested.emit)

        header_layout.addWidget(title_lbl)
        header_layout.addWidget(self.count_lbl)
        header_layout.addStretch()
        header_layout.addWidget(self.search_input)
        header_layout.addWidget(self.import_mode_btn)
        header_layout.addWidget(self.new_mode_btn)

        main_layout.addLayout(header_layout)

        # Scrollable Grid of Mode Cards
        scroll = QScrollArea()
        scroll.setWidgetResizable(True)
        scroll.setStyleSheet("QScrollArea { border: none; background: transparent; }")

        self.grid_container = QWidget()
        self.grid_layout = QGridLayout(self.grid_container)
        self.grid_layout.setContentsMargins(0, 0, 0, 0)
        self.grid_layout.setSpacing(16)
        scroll.setWidget(self.grid_container)

        main_layout.addWidget(scroll, stretch=1)

        # Bottom System Hardware Status Bar
        status_bar = QFrame()
        status_bar.setStyleSheet("""
            QFrame {
                background-color: #111827;
                border: 1px solid #1f2937;
                border-radius: 12px;
                padding: 10px 18px;
            }
        """)
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
        self._render_modes(self.all_modes)

    def _filter_modes(self, query: str) -> None:
        """Filter modes by search query."""
        q = query.strip().lower()
        if not q:
            self._render_modes(self.all_modes)
            return

        filtered = [
            m for m in self.all_modes
            if q in m.name.lower()
            or q in m.description.lower()
            or (m.hotkey and q in m.hotkey.lower())
            or q in m.id.lower()
        ]
        self._render_modes(filtered)

    def _render_modes(self, modes: List[Mode]) -> None:
        # Clear existing grid widgets
        while self.grid_layout.count():
            item = self.grid_layout.takeAt(0)
            if item.widget():
                item.widget().deleteLater()

        self.count_lbl.setText(f"({len(modes)} Mode{'s' if len(modes) != 1 else ''})")

        if not modes:
            empty_container = QWidget()
            empty_layout = QVBoxLayout(empty_container)
            empty_layout.setAlignment(Qt.AlignmentFlag.AlignCenter)
            empty_layout.setSpacing(12)

            empty_lbl = QLabel("No automation modes found.")
            empty_lbl.setStyleSheet("color: #94a3b8; font-size: 16px; font-weight: 600;")
            empty_sub = QLabel("Click '+ New Mode' to create your first recipe or 'Import JSON' to load one.")
            empty_sub.setStyleSheet("color: #64748b; font-size: 13px;")

            empty_layout.addWidget(empty_lbl)
            empty_layout.addWidget(empty_sub)

            self.grid_layout.addWidget(empty_container, 0, 0, 1, 3)
            return

        columns = 3
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
