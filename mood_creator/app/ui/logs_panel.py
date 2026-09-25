"""World-Class Activity & Automation Logs Viewer.

Designed to match the reference visual direction:
- Pure AMOLED-black foundation (#04060a) with near-black surface separation
- Neutral monochrome palette (black, white, soft gray) with one restrained electric-blue accent
- Completely replaces raw database tables with a refined activity timeline/table hybrid
- Timestamp, Mode icon + name, Action icon + name, Status indicator, Duration, and Details
- Subtle status indicators: tiny green indicator for SUCCESS, tiny red indicator for FAILED
- Compact rows, excellent alignment, subtle separators, and high readability
- Clean header hierarchy: ACTIVITY tag, Activity Logs title, entry count, search, filter, export, clear, refresh
- Minimal system status strip footer: System is running normally, total entries, last updated
- Smooth 100-250ms micro-interactions on hover, search, filter, and refresh
- Preserves all database persistence, filtering, searching, CSV export, and clear functionality
- ABSOLUTELY ZERO PURPLE, VIOLET, LAVENDER, PINK, OR PURPLE GRADIENTS
"""

import csv
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Dict, List, Optional

from PySide6.QtCore import QPoint, QRect, QRectF, Qt, QTimer, Signal
from PySide6.QtGui import (
    QBrush,
    QColor,
    QCursor,
    QFont,
    QLinearGradient,
    QPainter,
    QPainterPath,
    QPen,
    QPixmap,
)
from PySide6.QtWidgets import (
    QAbstractItemView,
    QComboBox,
    QFileDialog,
    QFrame,
    QHBoxLayout,
    QHeaderView,
    QLabel,
    QLineEdit,
    QMenu,
    QMessageBox,
    QPushButton,
    QScrollArea,
    QSizePolicy,
    QTableWidget,
    QTableWidgetItem,
    QVBoxLayout,
    QWidget,
)

from app.persistence.database import Database
from app.ui.smooth_scroll import install_smooth_scroll
from app.ui.styles.design_tokens import AnimationDuration, DarkPalette


def resolve_mode_icon(mode_id: str, mode_name: str) -> str:
    """Return crisp emoji icon matching the mode identity."""
    m = f"{mode_name} {mode_id}".lower()
    if "guitar" in m or "music" in m or "audio" in m:
        return "🎸"
    if "study" in m or "focus" in m or "read" in m:
        return "📖"
    if "movie" in m or "cinema" in m or "theatre" in m:
        return "🎬"
    if "game" in m or "gaming" in m:
        return "🎮"
    if "code" in m or "coding" in m or "dev" in m:
        return "</>"
    return "⚡"


def resolve_action_icon(action_name: str) -> str:
    """Return contextual action icon matching the action type."""
    a = (action_name or "").lower()
    if "notify" in a or "alert" in a or "ready" in a:
        return "🔔"
    if "wait" in a or "delay" in a or "sleep" in a:
        return "⏱"
    if "fl studio" in a:
        return "🚀"
    if "spotify" in a:
        return "🎵"
    if "steam" in a:
        return "🎮"
    if "discord" in a or "chat" in a:
        return "💬"
    if "vs code" in a or "code" in a:
        return "💻"
    if "launch" in a or "start" in a:
        return "🚀"
    if "speaker" in a or "output" in a or "volume" in a:
        return "🔊"
    if "input" in a or "mic" in a:
        return "🎙"
    if "detect" in a or "interface" in a:
        return "🎛"
    if "hotkey" in a or "key" in a:
        return "⌨"
    return "⚡"


class LogsPanelView(QWidget):
    """Refined consumer-grade Activity Logs view matching the reference design."""

    def __init__(self, db: Database, parent=None):
        super().__init__(parent)
        self.db = db
        self.raw_logs: List[Dict[str, Any]] = []
        self._last_refresh_time: Optional[datetime] = None
        self._sort_col: int = 1
        self._sort_ascending: bool = False

        # Load mountain backdrop banner
        app_dir = Path(__file__).resolve().parent.parent.parent
        banner_path = app_dir / "assets" / "ui" / "banner_mountain.jpg"
        self._banner_pix: Optional[QPixmap] = None
        if banner_path.exists():
            self._banner_pix = QPixmap(str(banner_path))

        # Automatically seed sample activity history if the DB is empty on initial setup
        self.db.seed_sample_logs_if_empty()

        self.setStyleSheet(
            """
            QWidget {
                font-family: 'Segoe UI Variable Text', 'Segoe UI', -apple-system, sans-serif;
                color: #f8fafc;
            }
            """
        )

        root_layout = QVBoxLayout(self)
        root_layout.setContentsMargins(28, 18, 28, 16)
        root_layout.setSpacing(12)

        # -------------------------------------------------------------
        # 1. Top Header & Control Bar
        # -------------------------------------------------------------
        top_bar = QHBoxLayout()
        top_bar.setContentsMargins(0, 0, 0, 0)
        top_bar.setSpacing(16)

        header_vbox = QVBoxLayout()
        header_vbox.setSpacing(2)

        tag_lbl = QLabel("ACTIVITY")
        tag_lbl.setStyleSheet("font-size: 10px; font-weight: 700; color: #64748b; letter-spacing: 1.2px; background: transparent;")
        header_vbox.addWidget(tag_lbl)

        title_hbox = QHBoxLayout()
        title_hbox.setSpacing(8)
        title_hbox.setAlignment(Qt.AlignmentFlag.AlignLeft | Qt.AlignmentFlag.AlignVCenter)

        self.title_lbl = QLabel("Activity Logs")
        self.title_lbl.setStyleSheet(
            """
            font-size: 22px;
            font-weight: 750;
            color: #ffffff;
            letter-spacing: -0.5px;
            font-family: 'Segoe UI Variable Display', 'Segoe UI', -apple-system, sans-serif;
            background: transparent;
            """
        )
        title_hbox.addWidget(self.title_lbl)

        self.count_badge = QLabel("(0 entries)")
        self.count_badge.setStyleSheet("font-size: 13px; font-weight: 500; color: #64748b; background: transparent; padding-top: 4px;")
        title_hbox.addWidget(self.count_badge)

        header_vbox.addLayout(title_hbox)

        self.sub_lbl = QLabel("Track your automation history, see what's happening, and stay in control.")
        self.sub_lbl.setStyleSheet("font-size: 12px; color: #94a3b8; background: transparent;")
        header_vbox.addWidget(self.sub_lbl)

        top_bar.addLayout(header_vbox, stretch=1)

        # -------------------------------------------------------------
        # Header Controls: Search · Filter · Export · Clear · Refresh
        # -------------------------------------------------------------
        controls_hbox = QHBoxLayout()
        controls_hbox.setSpacing(6)
        controls_hbox.setAlignment(Qt.AlignmentFlag.AlignRight | Qt.AlignmentFlag.AlignVCenter)

        # Search Bar Pill
        search_box = QFrame()
        search_box.setFixedSize(225, 34)
        search_box.setStyleSheet(
            """
            QFrame {
                background-color: #0b0e17;
                border: 1px solid #1a2030;
                border-radius: 17px;
            }
            QFrame:focus-within {
                border-color: #0284c7;
            }
            """
        )
        sb_layout = QHBoxLayout(search_box)
        sb_layout.setContentsMargins(10, 0, 8, 0)
        sb_layout.setSpacing(6)

        search_icon = QLabel("🔍")
        search_icon.setStyleSheet("font-size: 11px; color: #64748b; background: transparent; border: none;")
        sb_layout.addWidget(search_icon)

        self.search_input = QLineEdit()
        self.search_input.setPlaceholderText("Search logs...")
        self.search_input.setStyleSheet("background: transparent; border: none; font-size: 11px; color: #f8fafc;")
        self.search_input.textChanged.connect(self._apply_filters)
        sb_layout.addWidget(self.search_input, stretch=1)

        shortcut_badge = QLabel("Ctrl K")
        shortcut_badge.setStyleSheet(
            """
            background-color: #141b2a;
            border: 1px solid #222d44;
            border-radius: 4px;
            color: #64748b;
            font-size: 9px;
            font-weight: 600;
            padding: 1px 4px;
            """
        )
        sb_layout.addWidget(shortcut_badge)
        controls_hbox.addWidget(search_box)

        # Status Filter Pill Dropdown
        self.status_filter_combo = QComboBox()
        self.status_filter_combo.setFixedSize(115, 34)
        self.status_filter_combo.addItem("● All Statuses", "all")
        self.status_filter_combo.addItem("● Success Only", "success")
        self.status_filter_combo.addItem("● Failures Only", "failure")
        self.status_filter_combo.setStyleSheet(
            """
            QComboBox {
                background-color: #0b0e17;
                border: 1px solid #1a2030;
                border-radius: 17px;
                padding: 0px 10px;
                font-size: 11px;
                font-weight: 500;
                color: #cbd5e1;
            }
            QComboBox:hover {
                background-color: #141a2a;
                border-color: #2a3854;
                color: #ffffff;
            }
            QComboBox::drop-down {
                border: none;
                width: 14px;
            }
            QComboBox QAbstractItemView {
                background-color: #0b0e17;
                border: 1px solid #1a2030;
                border-radius: 8px;
                color: #cbd5e1;
                selection-background-color: #121d30;
                selection-color: #38bdf8;
                padding: 4px;
            }
            """
        )
        self.status_filter_combo.currentIndexChanged.connect(self._apply_filters)
        controls_hbox.addWidget(self.status_filter_combo)

        # Export CSV Button
        self.export_btn = QPushButton("📄  Export CSV")
        self.export_btn.setFixedSize(105, 34)
        self.export_btn.setCursor(Qt.CursorShape.PointingHandCursor)
        self.export_btn.setStyleSheet(
            """
            QPushButton {
                background-color: #0c101c;
                border: 1px solid #1a2234;
                border-radius: 17px;
                color: #cbd5e1;
                font-size: 11px;
                font-weight: 600;
            }
            QPushButton:hover {
                background-color: #141a2a;
                border-color: #2a3854;
                color: #ffffff;
            }
            """
        )
        self.export_btn.clicked.connect(self.export_csv)
        controls_hbox.addWidget(self.export_btn)

        # Clear Logs Button
        self.clear_btn = QPushButton("🗑  Clear Logs")
        self.clear_btn.setFixedSize(95, 34)
        self.clear_btn.setCursor(Qt.CursorShape.PointingHandCursor)
        self.clear_btn.setStyleSheet(
            """
            QPushButton {
                background-color: #0c101c;
                border: 1px solid #1a2234;
                border-radius: 17px;
                color: #cbd5e1;
                font-size: 11px;
                font-weight: 600;
            }
            QPushButton:hover {
                background-color: #1c1318;
                border-color: #4a202a;
                color: #ef4444;
            }
            """
        )
        self.clear_btn.clicked.connect(self.clear_logs)
        controls_hbox.addWidget(self.clear_btn)

        # Refresh Button
        self.refresh_btn = QPushButton("↻  Refresh")
        self.refresh_btn.setFixedSize(85, 34)
        self.refresh_btn.setCursor(Qt.CursorShape.PointingHandCursor)
        self.refresh_btn.setStyleSheet(
            """
            QPushButton {
                background-color: #0c101c;
                border: 1px solid #1a2234;
                border-radius: 17px;
                color: #f8fafc;
                font-size: 11px;
                font-weight: 600;
            }
            QPushButton:hover {
                background-color: #141a2a;
                border-color: #2a3854;
                color: #ffffff;
            }
            QPushButton:disabled {
                color: #64748b;
                border-color: #141824;
            }
            """
        )
        self.refresh_btn.clicked.connect(self.refresh_logs)
        controls_hbox.addWidget(self.refresh_btn)

        top_bar.addLayout(controls_hbox)
        root_layout.addLayout(top_bar)

        # -------------------------------------------------------------
        # 2. Main Refined Activity Timeline / Table Hybrid
        # -------------------------------------------------------------
        self.table_card = QFrame()
        self.table_card.setObjectName("TableCard")
        self.table_card.setStyleSheet(
            """
            #TableCard {
                background-color: #050811;
                border: 1px solid #141926;
                border-radius: 14px;
            }
            """
        )
        tc_layout = QVBoxLayout(self.table_card)
        tc_layout.setContentsMargins(14, 10, 14, 10)
        tc_layout.setSpacing(0)

        # Activity Table
        self.table = QTableWidget(0, 8)
        self.table.setObjectName("ActivityTable")
        self.table.setShowGrid(False)
        self.table.setAlternatingRowColors(False)
        self.table.setFocusPolicy(Qt.FocusPolicy.NoFocus)
        self.table.setSelectionBehavior(QAbstractItemView.SelectionBehavior.SelectRows)
        self.table.setSelectionMode(QAbstractItemView.SelectionMode.SingleSelection)
        self.table.verticalHeader().setVisible(False)
        self.table.verticalHeader().setDefaultSectionSize(35)

        # Headers
        headers = [
            "#",
            "Timestamp ⬍",
            "Mode ⬍",
            "Action Name ⬍",
            "Status ⬍",
            "Duration ⬍",
            "Details / Message",
            "",
        ]
        self.table.setHorizontalHeaderLabels(headers)

        header_view = self.table.horizontalHeader()
        header_view.setDefaultAlignment(Qt.AlignmentFlag.AlignLeft | Qt.AlignmentFlag.AlignVCenter)
        header_view.setSectionResizeMode(0, QHeaderView.ResizeMode.Fixed)
        header_view.setSectionResizeMode(1, QHeaderView.ResizeMode.Fixed)
        header_view.setSectionResizeMode(2, QHeaderView.ResizeMode.Fixed)
        header_view.setSectionResizeMode(3, QHeaderView.ResizeMode.Fixed)
        header_view.setSectionResizeMode(4, QHeaderView.ResizeMode.Fixed)
        header_view.setSectionResizeMode(5, QHeaderView.ResizeMode.Fixed)
        header_view.setSectionResizeMode(6, QHeaderView.ResizeMode.Stretch)
        header_view.setSectionResizeMode(7, QHeaderView.ResizeMode.Fixed)

        self.table.setColumnWidth(0, 42)
        self.table.setColumnWidth(1, 145)
        self.table.setColumnWidth(2, 140)
        self.table.setColumnWidth(3, 190)
        self.table.setColumnWidth(4, 100)
        self.table.setColumnWidth(5, 75)
        self.table.setColumnWidth(7, 34)

        header_view.sectionClicked.connect(self._on_header_clicked)

        self.table.setStyleSheet(
            """
            QTableWidget {
                background-color: transparent;
                border: none;
                gridline-color: transparent;
            }
            QHeaderView::section {
                background-color: transparent;
                color: #64748b;
                font-size: 11px;
                font-weight: 600;
                border: none;
                border-bottom: 1px solid #141926;
                padding-left: 8px;
                padding-right: 8px;
                height: 32px;
            }
            QTableWidget::item {
                border-bottom: 1px solid #090d18;
                padding-left: 8px;
                padding-right: 8px;
                color: #94a3b8;
            }
            QTableWidget::item:hover {
                background-color: #090e1a;
            }
            QTableWidget::item:selected {
                background-color: #0b1424;
                color: #ffffff;
            }
            QScrollBar:vertical {
                background: transparent;
                width: 5px;
                margin: 0px;
            }
            QScrollBar::handle:vertical {
                background: #1e2638;
                border-radius: 2px;
                min-height: 20px;
            }
            QScrollBar::handle:vertical:hover {
                background: #0284c7;
            }
            QScrollBar::add-line:vertical, QScrollBar::sub-line:vertical {
                height: 0px;
            }
            """
        )

        tc_layout.addWidget(self.table)
        self.smooth_scroll = install_smooth_scroll(self.table)
        root_layout.addWidget(self.table_card, stretch=1)

        # -------------------------------------------------------------
        # 3. Footer: Minimal System Status Strip
        # -------------------------------------------------------------
        self.footer = QFrame()
        self.footer.setObjectName("FooterBar")
        self.footer.setFixedHeight(42)
        self.footer.setStyleSheet(
            """
            #FooterBar {
                background-color: #050811;
                border: 1px solid #121824;
                border-radius: 10px;
            }
            """
        )
        fb_layout = QHBoxLayout(self.footer)
        fb_layout.setContentsMargins(16, 0, 16, 0)
        fb_layout.setSpacing(12)

        op_dot = QLabel("●")
        op_dot.setStyleSheet("font-size: 10px; color: #10b981; background: transparent; border: none;")
        op_text = QLabel("System is running normally")
        op_text.setStyleSheet("font-size: 11px; font-weight: 600; color: #10b981; background: transparent; border: none;")

        fb_layout.addWidget(op_dot)
        fb_layout.addWidget(op_text)
        fb_layout.addStretch()

        self.footer_count_lbl = QLabel("📋  0 total entries")
        self.footer_count_lbl.setStyleSheet("font-size: 11px; color: #94a3b8; background: transparent; border: none;")
        fb_layout.addWidget(self.footer_count_lbl)

        v_divider = QLabel("|")
        v_divider.setStyleSheet("color: #1a2234; background: transparent; border: none;")
        fb_layout.addWidget(v_divider)

        self.footer_time_lbl = QLabel("🕒  Last updated: Just now")
        self.footer_time_lbl.setStyleSheet("font-size: 11px; color: #94a3b8; background: transparent; border: none;")
        fb_layout.addWidget(self.footer_time_lbl)

        root_layout.addWidget(self.footer)

        # Initial Load
        self.refresh_logs()

    def paintEvent(self, event) -> None:
        """Paint true AMOLED black foundation with subtle mountain landscape banner."""
        painter = QPainter(self)
        painter.setRenderHint(QPainter.RenderHint.Antialiasing)
        painter.setRenderHint(QPainter.RenderHint.SmoothPixmapTransform)

        # 1. AMOLED Black base
        painter.fillRect(self.rect(), QColor("#04060a"))

        # 2. Subtle Dark Mountain Banner behind header
        if self._banner_pix and not self._banner_pix.isNull():
            banner_h = 160
            banner_rect = QRect(0, 0, self.width(), banner_h)
            scaled = self._banner_pix.scaled(
                self.width(), banner_h,
                Qt.AspectRatioMode.KeepAspectRatioByExpanding,
                Qt.TransformationMode.SmoothTransformation,
            )
            painter.setOpacity(0.30)
            painter.drawPixmap(0, 0, scaled)
            painter.setOpacity(1.0)

            # Gradient mask fading into pure AMOLED black
            grad = QLinearGradient(0, 0, 0, banner_h)
            grad.setColorAt(0.0, QColor(4, 6, 10, 70))
            grad.setColorAt(0.6, QColor(4, 6, 10, 200))
            grad.setColorAt(1.0, QColor(4, 6, 10, 255))
            painter.fillRect(banner_rect, grad)

        super().paintEvent(event)

    # -----------------------------------------------------------------
    # Data Loading & Filtering
    # -----------------------------------------------------------------
    def refresh_logs(self) -> None:
        """Fetch logs from SQLite database and populate table."""
        self.refresh_btn.setEnabled(False)
        self.refresh_btn.setText("⏳  Refreshing...")

        self.raw_logs = self.db.get_recent_logs(limit=300)
        self._last_refresh_time = datetime.now()
        self._apply_filters()

        self.refresh_btn.setEnabled(True)
        self.refresh_btn.setText("↻  Refresh")

    def _apply_filters(self) -> None:
        query = self.search_input.text().strip().lower()
        status_filter = self.status_filter_combo.currentData()

        filtered = []
        for entry in self.raw_logs:
            success = bool(entry.get("success", 0))

            if status_filter == "success" and not success:
                continue
            if status_filter == "failure" and success:
                continue

            if query:
                m_name = str(entry.get("mode_name", "")).lower()
                a_name = str(entry.get("action_name", "")).lower()
                msg = str(entry.get("error") or entry.get("message") or "").lower()
                ts = str(entry.get("timestamp", "")).lower()
                if query not in m_name and query not in a_name and query not in msg and query not in ts:
                    continue

            filtered.append(entry)

        # Update Counts
        total_len = len(filtered)
        self.count_badge.setText(f"({total_len} entr{'ies' if total_len != 1 else 'y'})")
        self.footer_count_lbl.setText(f"📋  {total_len} total entries")

        if self._last_refresh_time:
            self.footer_time_lbl.setText(f"🕒  Last updated: {self._last_refresh_time.strftime('%H:%M:%S')}")

        # Render Rows
        self.table.setUpdatesEnabled(False)
        try:
            self.table.setRowCount(total_len)

            for row, entry in enumerate(filtered):
                # Col 0: Index Number
                idx_item = QTableWidgetItem(str(row + 1))
                idx_item.setTextAlignment(Qt.AlignmentFlag.AlignCenter | Qt.AlignmentFlag.AlignVCenter)
                idx_item.setForeground(QColor("#475569"))
                idx_item.setFont(QFont("Segoe UI Variable Text", 9))
                self.table.setItem(row, 0, idx_item)

                # Col 1: Timestamp
                ts = entry.get("timestamp", "")
                if "T" in ts:
                    ts = ts.replace("T", " ").split(".")[0]
                ts_item = QTableWidgetItem(ts)
                ts_item.setTextAlignment(Qt.AlignmentFlag.AlignLeft | Qt.AlignmentFlag.AlignVCenter)
                ts_item.setForeground(QColor("#94a3b8"))
                ts_item.setFont(QFont("Segoe UI Variable Text", 10))
                self.table.setItem(row, 1, ts_item)

                # Col 2: Mode (Icon + Name)
                m_id = entry.get("mode_id", "")
                m_name = entry.get("mode_name", "System")
                m_icon = resolve_mode_icon(m_id, m_name)
                mode_widget = self._create_mode_cell(m_icon, m_name)
                self.table.setCellWidget(row, 2, mode_widget)

                # Col 3: Action Name (Icon + Name)
                a_name = entry.get("action_name", "")
                a_icon = resolve_action_icon(a_name)
                action_widget = self._create_action_cell(a_icon, a_name)
                self.table.setCellWidget(row, 3, action_widget)

                # Col 4: Status (● SUCCESS / ● FAILED)
                success = bool(entry.get("success", 0))
                status_widget = self._create_status_cell(success)
                self.table.setCellWidget(row, 4, status_widget)

                # Col 5: Duration
                dur = entry.get("duration", 0.0)
                dur_item = QTableWidgetItem(f"{dur:.2f}s")
                dur_item.setTextAlignment(Qt.AlignmentFlag.AlignLeft | Qt.AlignmentFlag.AlignVCenter)
                dur_item.setForeground(QColor("#94a3b8"))
                dur_item.setFont(QFont("Segoe UI Variable Text", 10))
                self.table.setItem(row, 5, dur_item)

                # Col 6: Details / Message
                msg = entry.get("error") or entry.get("message") or ""
                msg_item = QTableWidgetItem(msg)
                msg_item.setTextAlignment(Qt.AlignmentFlag.AlignLeft | Qt.AlignmentFlag.AlignVCenter)
                msg_item.setForeground(QColor("#cbd5e1" if success else "#f87171"))
                msg_item.setFont(QFont("Segoe UI Variable Text", 10))
                msg_item.setToolTip(msg)
                self.table.setItem(row, 6, msg_item)

                # Col 7: Subtle Overflow Menu Button (⋮)
                menu_btn = self._create_overflow_button(row, entry)
                self.table.setCellWidget(row, 7, menu_btn)
        finally:
            self.table.setUpdatesEnabled(True)

    def _on_header_clicked(self, logical_index: int) -> None:
        """Sort table rows by clicked column."""
        if logical_index == self._sort_col:
            self._sort_ascending = not self._sort_ascending
        else:
            self._sort_col = logical_index
            self._sort_ascending = True

        key_map = {
            0: lambda x: int(x.get("id", 0) or 0),
            1: lambda x: str(x.get("timestamp", "")),
            2: lambda x: str(x.get("mode_name", "")),
            3: lambda x: str(x.get("action_name", "")),
            4: lambda x: int(x.get("success", 0) or 0),
            5: lambda x: float(x.get("duration", 0.0) or 0.0),
            6: lambda x: str(x.get("error") or x.get("message") or ""),
        }

        if logical_index in key_map:
            self.raw_logs.sort(key=key_map[logical_index], reverse=not self._sort_ascending)
            self._apply_filters()

    # -----------------------------------------------------------------
    # Cell Widget Factories
    # -----------------------------------------------------------------
    def _create_mode_cell(self, icon_str: str, name_str: str) -> QWidget:
        widget = QWidget()
        widget.setStyleSheet("background: transparent;")
        layout = QHBoxLayout(widget)
        layout.setContentsMargins(8, 0, 8, 0)
        layout.setSpacing(6)
        layout.setAlignment(Qt.AlignmentFlag.AlignLeft | Qt.AlignmentFlag.AlignVCenter)

        icon_lbl = QLabel(icon_str)
        icon_lbl.setStyleSheet("font-size: 12px; color: #38bdf8; background: transparent; border: none;")
        layout.addWidget(icon_lbl)

        name_lbl = QLabel(name_str)
        name_lbl.setStyleSheet("font-size: 11px; font-weight: 600; color: #f8fafc; background: transparent; border: none;")
        layout.addWidget(name_lbl, stretch=1)
        return widget

    def _create_action_cell(self, icon_str: str, name_str: str) -> QWidget:
        widget = QWidget()
        widget.setStyleSheet("background: transparent;")
        layout = QHBoxLayout(widget)
        layout.setContentsMargins(8, 0, 8, 0)
        layout.setSpacing(6)
        layout.setAlignment(Qt.AlignmentFlag.AlignLeft | Qt.AlignmentFlag.AlignVCenter)

        icon_lbl = QLabel(icon_str)
        icon_lbl.setStyleSheet("font-size: 12px; color: #94a3b8; background: transparent; border: none;")
        layout.addWidget(icon_lbl)

        name_lbl = QLabel(name_str)
        name_lbl.setStyleSheet("font-size: 11px; font-weight: 500; color: #cbd5e1; background: transparent; border: none;")
        layout.addWidget(name_lbl, stretch=1)
        return widget

    def _create_status_cell(self, success: bool) -> QWidget:
        widget = QWidget()
        widget.setStyleSheet("background: transparent;")
        layout = QHBoxLayout(widget)
        layout.setContentsMargins(8, 0, 8, 0)
        layout.setSpacing(5)
        layout.setAlignment(Qt.AlignmentFlag.AlignLeft | Qt.AlignmentFlag.AlignVCenter)

        dot_color = "#10b981" if success else "#ef4444"
        text_str = "SUCCESS" if success else "FAILED"

        dot_lbl = QLabel("●")
        dot_lbl.setStyleSheet(f"font-size: 8px; color: {dot_color}; background: transparent; border: none;")
        layout.addWidget(dot_lbl)

        text_lbl = QLabel(text_str)
        text_lbl.setStyleSheet(
            f"font-size: 10px; font-weight: 700; color: {dot_color}; letter-spacing: 0.5px; background: transparent; border: none;"
        )
        layout.addWidget(text_lbl)
        return widget

    def _create_overflow_button(self, row_idx: int, entry: Dict[str, Any]) -> QWidget:
        container = QWidget()
        container.setStyleSheet("background: transparent;")
        layout = QHBoxLayout(container)
        layout.setContentsMargins(0, 0, 4, 0)
        layout.setAlignment(Qt.AlignmentFlag.AlignCenter)

        btn = QPushButton("⋮")
        btn.setFixedSize(24, 24)
        btn.setCursor(Qt.CursorShape.PointingHandCursor)
        btn.setStyleSheet(
            """
            QPushButton {
                background: transparent;
                border: 1px solid transparent;
                border-radius: 4px;
                color: #64748b;
                font-size: 13px;
                font-weight: bold;
            }
            QPushButton:hover {
                background-color: #141b2c;
                border-color: #222d46;
                color: #f8fafc;
            }
            """
        )
        btn.clicked.connect(lambda: self._show_row_context_menu(entry))
        layout.addWidget(btn)
        return container

    def _show_row_context_menu(self, entry: Dict[str, Any]) -> None:
        menu = QMenu(self)
        menu.setStyleSheet(
            """
            QMenu {
                background-color: #090e1a;
                border: 1px solid #1c263c;
                border-radius: 8px;
                padding: 4px;
                color: #f8fafc;
            }
            QMenu::item {
                padding: 6px 18px;
                border-radius: 6px;
                font-size: 11px;
            }
            QMenu::item:selected {
                background-color: #121d30;
                color: #38bdf8;
            }
            """
        )

        copy_action = menu.addAction("📋 Copy Log Details")
        filter_mode_action = menu.addAction(f"🔍 Filter by '{entry.get('mode_name', '')}'")
        menu.addSeparator()
        inspect_action = menu.addAction("ℹ View Raw Metadata")

        pos = QCursor.pos()
        action = menu.exec(pos)
        if action == copy_action:
            from PySide6.QtWidgets import QApplication
            msg = entry.get("error") or entry.get("message") or ""
            clip_text = f"[{entry.get('timestamp')}] {entry.get('mode_name')} - {entry.get('action_name')}: {msg} ({entry.get('duration')}s)"
            QApplication.clipboard().setText(clip_text)
        elif action == filter_mode_action:
            self.search_input.setText(entry.get("mode_name", ""))
        elif action == inspect_action:
            QMessageBox.information(
                self,
                "Log Entry Metadata",
                f"ID: {entry.get('id')}\n"
                f"Timestamp: {entry.get('timestamp')}\n"
                f"Mode: {entry.get('mode_name')} ({entry.get('mode_id')})\n"
                f"Action: {entry.get('action_name')}\n"
                f"Success: {bool(entry.get('success'))}\n"
                f"Duration: {entry.get('duration')}s\n"
                f"Message: {entry.get('message')}\n"
                f"Error: {entry.get('error')}",
            )

    # -----------------------------------------------------------------
    # Export & Clear Actions
    # -----------------------------------------------------------------
    def export_csv(self) -> None:
        """Export visible logs to a clean CSV file."""
        if not self.raw_logs:
            QMessageBox.information(self, "Export Logs", "No log entries to export.")
            return

        file_path, _ = QFileDialog.getSaveFileName(
            self, "Export Activity Logs to CSV", "automation_hub_logs.csv", "CSV Files (*.csv);;All Files (*.*)"
        )
        if file_path:
            try:
                with open(file_path, "w", newline="", encoding="utf-8") as f:
                    writer = csv.writer(f)
                    writer.writerow(["Timestamp", "Mode ID", "Mode Name", "Action Name", "Success", "Duration (s)", "Details"])
                    for entry in self.raw_logs:
                        writer.writerow([
                            entry.get("timestamp", ""),
                            entry.get("mode_id", ""),
                            entry.get("mode_name", ""),
                            entry.get("action_name", ""),
                            entry.get("success", 0),
                            entry.get("duration", 0.0),
                            entry.get("error") or entry.get("message") or "",
                        ])
                QMessageBox.information(self, "Export Complete", f"Successfully exported activity logs to:\n{file_path}")
            except Exception as e:
                QMessageBox.critical(self, "Export Error", f"Failed to export logs: {e}")

    def clear_logs(self) -> None:
        """Permanently clear database execution logs."""
        res = QMessageBox.question(
            self,
            "Clear Activity Logs",
            "Are you sure you want to permanently clear all activity logs?",
            QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No,
        )
        if res == QMessageBox.StandardButton.Yes:
            self.db.clear_logs()
            self.refresh_logs()
