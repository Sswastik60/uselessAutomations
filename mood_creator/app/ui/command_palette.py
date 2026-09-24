"""Command Palette (Ctrl+K) for rapid keyboard-first search and action execution."""

import logging
from typing import Callable, List, Optional
from PySide6.QtCore import QEvent, Qt, Signal
from PySide6.QtGui import QKeyEvent
from PySide6.QtWidgets import (
    QDialog,
    QHBoxLayout,
    QLabel,
    QLineEdit,
    QListWidget,
    QListWidgetItem,
    QVBoxLayout,
    QWidget,
)

from app.models.mode import Mode
from app.ui.animation_manager import AnimationManager
from app.ui.styles.design_tokens import AnimationDuration, DarkPalette

logger = logging.getLogger(__name__)


class CommandItemWidget(QWidget):
    """Custom row widget for Command Palette items."""

    def __init__(self, title: str, subtitle: str = "", icon: str = "⚡", shortcut: str = "", parent=None):
        super().__init__(parent)
        layout = QHBoxLayout(self)
        layout.setContentsMargins(12, 8, 12, 8)
        layout.setSpacing(12)

        icon_lbl = QLabel(icon)
        icon_lbl.setStyleSheet("font-size: 18px; color: #38bdf8; background: transparent;")
        layout.addWidget(icon_lbl)

        text_layout = QVBoxLayout()
        text_layout.setSpacing(2)

        title_lbl = QLabel(title)
        title_lbl.setStyleSheet(f"font-size: 13px; font-weight: 700; color: {DarkPalette.TEXT_PRIMARY};")
        text_layout.addWidget(title_lbl)

        if subtitle:
            sub_lbl = QLabel(subtitle)
            sub_lbl.setStyleSheet(f"font-size: 11px; color: {DarkPalette.TEXT_MUTED};")
            text_layout.addWidget(sub_lbl)

        layout.addLayout(text_layout, stretch=1)

        if shortcut:
            sc_lbl = QLabel(shortcut)
            sc_lbl.setStyleSheet(
                """
                QLabel {
                    background-color: #121212;
                    border: 1px solid #262626;
                    border-radius: 5px;
                    color: #38bdf8;
                    font-size: 10px;
                    font-weight: 700;
                    font-family: 'Consolas', monospace;
                    padding: 2px 6px;
                }
                """
            )
            layout.addWidget(sc_lbl)


class CommandPaletteDialog(QDialog):
    """Keyboard-first search & execution command palette modal dialog."""

    command_triggered = Signal(str, object)  # action_type, payload

    def __init__(self, modes: List[Mode], parent: Optional[QWidget] = None):
        super().__init__(parent)
        self.modes = modes
        self.setWindowTitle("Command Palette (Ctrl+K)")
        self.setFixedSize(620, 420)
        self.setWindowFlags(Qt.WindowType.FramelessWindowHint | Qt.WindowType.Dialog)
        self.setAttribute(Qt.WidgetAttribute.WA_TranslucentBackground)

        main_layout = QVBoxLayout(self)
        main_layout.setContentsMargins(0, 0, 0, 0)

        # Card container
        self.card = QWidget(self)
        self.card.setStyleSheet(
            """
            QWidget {
                background-color: #080808;
                border: 1px solid #1e293b;
                border-radius: 14px;
            }
            """
        )
        card_layout = QVBoxLayout(self.card)
        card_layout.setContentsMargins(16, 16, 16, 16)
        card_layout.setSpacing(12)

        # Search Input
        self.search_input = QLineEdit()
        self.search_input.setPlaceholderText("🔍  Search modes, navigation, actions... (Esc to close)")
        self.search_input.setStyleSheet(
            """
            QLineEdit {
                background-color: #000000;
                border: 1px solid #38bdf8;
                border-radius: 8px;
                padding: 10px 14px;
                font-size: 14px;
                color: #f8fafc;
            }
            """
        )
        self.search_input.textChanged.connect(self._on_search_changed)
        self.search_input.installEventFilter(self)
        card_layout.addWidget(self.search_input)

        # Results List
        self.list_widget = QListWidget()
        self.list_widget.setStyleSheet(
            """
            QListWidget {
                background-color: #050505;
                border: 1px solid #141414;
                border-radius: 8px;
                outline: none;
            }
            QListWidget::item {
                border-bottom: 1px solid #0d0d0d;
                border-radius: 6px;
                margin: 2px 4px;
            }
            QListWidget::item:selected, QListWidget::item:hover {
                background-color: #0f172a;
            }
            """
        )
        self.list_widget.itemActivated.connect(self._on_item_activated)
        card_layout.addWidget(self.list_widget, stretch=1)

        main_layout.addWidget(self.card)

        # Initial populate
        self._populate_items("")

    def showEvent(self, event) -> None:
        super().showEvent(event)
        self.search_input.setFocus()
        self.search_input.selectAll()
        AnimationManager.fade_in(self, duration=AnimationDuration.FAST)

    def eventFilter(self, obj, event) -> bool:
        if obj == self.search_input and event.type() == QEvent.Type.KeyPress:
            key = event.key()
            if key in (Qt.Key.Key_Down, Qt.Key.Key_Up):
                self.list_widget.keyPressEvent(event)
                return True
            elif key in (Qt.Key.Key_Return, Qt.Key.Key_Enter):
                current_item = self.list_widget.currentItem()
                if current_item:
                    self._on_item_activated(current_item)
                    return True
            elif key == Qt.Key.Key_Escape:
                self.reject()
                return True
        return super().eventFilter(obj, event)

    def _populate_items(self, query: str) -> None:
        self.list_widget.clear()
        q = query.lower().strip()

        items_data = []

        # 1. Modes
        for mode in self.modes:
            if not q or q in mode.name.lower() or q in mode.description.lower() or q in (mode.hotkey or "").lower():
                items_data.append({
                    "title": f"Run {mode.name}",
                    "subtitle": mode.description or "Execute automation sequence",
                    "icon": mode.icon or "⚡",
                    "shortcut": mode.hotkey or "",
                    "type": "run_mode",
                    "payload": mode,
                })

        # 2. Navigation
        nav_options = [
            ("Go to Dashboard", "View modes and quick controls", "⌂", "nav_dashboard"),
            ("Go to Modes Editor", "Create or edit modes", "⚡", "nav_modes"),
            ("Go to Connected Devices", "Inspect audio & MIDI devices", "🎧", "nav_devices"),
            ("Go to Activity Logs", "Inspect automation execution logs", "📜", "nav_logs"),
            ("Go to Settings", "Configure hub preferences", "⚙", "nav_settings"),
            ("Create New Mode", "Design a custom automation recipe", "➕", "create_mode"),
        ]
        for name, sub, icon, action_type in nav_options:
            if not q or q in name.lower() or q in sub.lower():
                items_data.append({
                    "title": name,
                    "subtitle": sub,
                    "icon": icon,
                    "shortcut": "",
                    "type": action_type,
                    "payload": None,
                })

        for data in items_data:
            item = QListWidgetItem(self.list_widget)
            item.setData(Qt.ItemDataRole.UserRole, data)
            widget = CommandItemWidget(
                title=data["title"],
                subtitle=data["subtitle"],
                icon=data["icon"],
                shortcut=data["shortcut"],
            )
            item.setSizeHint(widget.sizeHint())
            self.list_widget.setItemWidget(item, widget)

        if self.list_widget.count() > 0:
            self.list_widget.setCurrentRow(0)

    def _on_search_changed(self, text: str) -> None:
        self._populate_items(text)

    def _on_item_activated(self, item: QListWidgetItem) -> None:
        data = item.data(Qt.ItemDataRole.UserRole)
        if data:
            self.command_triggered.emit(data["type"], data["payload"])
            self.accept()
