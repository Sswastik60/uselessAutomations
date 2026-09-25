"""Apple-grade Action Sequence row widget matching the reference visual direction."""

from pathlib import Path
from typing import Optional
from PySide6.QtCore import QPoint, QRectF, Qt, Signal
from PySide6.QtGui import QBrush, QColor, QCursor, QFont, QPainter, QPainterPath, QPen, QPixmap
from PySide6.QtWidgets import (
    QFrame,
    QHBoxLayout,
    QLabel,
    QMenu,
    QPushButton,
    QSizePolicy,
    QVBoxLayout,
    QWidget,
)

from app.models.action import ActionConfig


class ActionRowWidget(QWidget):
    """Elegant workflow step row with connected pipeline line, icons, and configured values."""

    edit_clicked = Signal(int)
    move_up_clicked = Signal(int)
    move_down_clicked = Signal(int)
    duplicate_clicked = Signal(int)
    delete_clicked = Signal(int)

    CATEGORY_THEMES = {
        "process": {"color": "#38bdf8", "bg": "#0c1728", "border": "#1b3252", "icon": "</>"},
        "keyboard": {"color": "#f59e0b", "bg": "#201708", "border": "#3d2b0e", "icon": "⌨"},
        "file": {"color": "#60a5fa", "bg": "#0b172a", "border": "#1b3356", "icon": "📁"},
        "folder": {"color": "#60a5fa", "bg": "#0b172a", "border": "#1b3356", "icon": "📁"},
        "notification": {"color": "#22d3ee", "bg": "#081a24", "border": "#143a4e", "icon": "🔔"},
        "audio": {"color": "#34d399", "bg": "#061813", "border": "#11382c", "icon": "🎧"},
        "window": {"color": "#38bdf8", "bg": "#0a1526", "border": "#172d4c", "icon": "🗔"},
        "wait": {"color": "#94a3b8", "bg": "#101520", "border": "#212b3e", "icon": "⏱"},
        "condition": {"color": "#facc15", "bg": "#1f1a08", "border": "#3e3410", "icon": "⚡"},
        "midi": {"color": "#a3e635", "bg": "#131e06", "border": "#2c420e", "icon": "🎹"},
    }

    def __init__(
        self,
        index: int,
        action_config: ActionConfig,
        is_first: bool = False,
        is_last: bool = False,
        parent=None,
    ):
        super().__init__(parent)
        self.index = index
        self.action_config = action_config
        self.is_first = is_first
        self.is_last = is_last
        self.setFixedHeight(64)

        # Parse category & theme
        category = action_config.type.split(".")[0].lower() if "." in action_config.type else "custom"
        self.theme = self.CATEGORY_THEMES.get(category, {
            "color": "#38bdf8",
            "bg": "#0c1728",
            "border": "#1b3252",
            "icon": "⚡",
        })

        # Main horizontal layout
        layout = QHBoxLayout(self)
        layout.setContentsMargins(0, 2, 0, 2)
        layout.setSpacing(0)

        # 1. Step Connector Column (width 50)
        self.step_col = QWidget()
        self.step_col.setFixedWidth(50)
        self.step_col.paintEvent = self._paint_step_col
        layout.addWidget(self.step_col)

        # 2. Main Action Card Frame
        self.card = QFrame()
        self.card.setObjectName("ActionCard")
        self.card.setStyleSheet(
            """
            #ActionCard {
                background-color: #080b14;
                border: 1px solid #161c2b;
                border-radius: 12px;
            }
            #ActionCard:hover {
                background-color: #0c101c;
                border: 1px solid #243048;
            }
            """
        )

        card_layout = QHBoxLayout(self.card)
        card_layout.setContentsMargins(12, 6, 12, 6)
        card_layout.setSpacing(10)

        # Action Type Icon Badge (Real App Icon or Category Emoji)
        self.app_pixmap = self._resolve_app_pixmap(size=24)
        self.icon_badge = QLabel()
        self.icon_badge.setFixedSize(36, 36)
        self.icon_badge.setAlignment(Qt.AlignmentFlag.AlignCenter)
        if self.app_pixmap and not self.app_pixmap.isNull():
            self.icon_badge.setPixmap(self.app_pixmap)
            self.icon_badge.setStyleSheet(
                """
                QLabel {
                    background-color: #0c1426;
                    border: 1px solid #1e293b;
                    border-radius: 8px;
                    padding: 2px;
                }
                """
            )
        else:
            self.icon_badge.setText(self._resolve_icon())
            self.icon_badge.setStyleSheet(
                f"""
                QLabel {{
                    background-color: {self.theme['bg']};
                    border: 1px solid {self.theme['border']};
                    border-radius: 8px;
                    color: {self.theme['color']};
                    font-size: 14px;
                    font-weight: 700;
                    font-family: 'Segoe UI Variable Display', 'Segoe UI Mono', monospace;
                }}
                """
            )
        card_layout.addWidget(self.icon_badge)

        # Action Title & Subtitle block
        titles_box = QVBoxLayout()
        titles_box.setSpacing(1)
        titles_box.setAlignment(Qt.AlignmentFlag.AlignVCenter)

        cat_title = self._resolve_category_title()
        self.title_lbl = QLabel(cat_title)
        self.title_lbl.setStyleSheet(
            """
            font-size: 13px;
            font-weight: 600;
            color: #f8fafc;
            background: transparent;
            font-family: 'Segoe UI Variable Display', 'Segoe UI', -apple-system, sans-serif;
            """
        )

        sub_title = self._resolve_subtitle()
        self.sub_lbl = QLabel(sub_title)
        self.sub_lbl.setStyleSheet("font-size: 11px; color: #64748b; background: transparent;")

        titles_box.addWidget(self.title_lbl)
        titles_box.addWidget(self.sub_lbl)
        card_layout.addLayout(titles_box)

        # Short Description block
        desc_str = self._resolve_description()
        self.desc_lbl = QLabel(desc_str)
        self.desc_lbl.setStyleSheet("font-size: 12px; color: #94a3b8; background: transparent;")
        self.desc_lbl.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Preferred)
        card_layout.addWidget(self.desc_lbl, stretch=1)

        # Configured Value Chip (Clean display with full path in tooltip)
        val_str = self._resolve_value_chip()
        chip_icon_str = self._resolve_chip_icon()
        if val_str:
            self.val_chip = QFrame()
            self.val_chip.setFixedHeight(28)
            self.val_chip.setMaximumWidth(175)
            self.val_chip.setStyleSheet(
                """
                QFrame {
                    background-color: #0e1424;
                    border: 1px solid #1a2336;
                    border-radius: 6px;
                }
                """
            )
            chip_raw_target = str(self.action_config.params.get("application", "") or self.action_config.params.get("path", "") or val_str)
            self.val_chip.setToolTip(chip_raw_target)

            chip_layout = QHBoxLayout(self.val_chip)
            chip_layout.setContentsMargins(7, 2, 7, 2)
            chip_layout.setSpacing(5)

            if self.app_pixmap and not self.app_pixmap.isNull():
                thumb_pix = self.app_pixmap.scaled(14, 14, Qt.AspectRatioMode.KeepAspectRatio, Qt.TransformationMode.SmoothTransformation)
                chip_icon = QLabel()
                chip_icon.setPixmap(thumb_pix)
                chip_icon.setStyleSheet("background: transparent;")
                chip_layout.addWidget(chip_icon)
            elif chip_icon_str:
                chip_icon = QLabel(chip_icon_str)
                chip_icon.setStyleSheet(f"font-size: 11px; color: {self.theme['color']}; background: transparent;")
                chip_layout.addWidget(chip_icon)

            chip_lbl = QLabel(val_str)
            chip_lbl.setStyleSheet("font-size: 11px; font-weight: 500; color: #e2e8f0; background: transparent;")
            chip_layout.addWidget(chip_lbl)

            card_layout.addWidget(self.val_chip)

        # Dedicated Reorder & Action Controls Box (Never squished or wrapped)
        controls_container = QWidget()
        controls_container.setFixedHeight(28)
        controls_layout = QHBoxLayout(controls_container)
        controls_layout.setContentsMargins(0, 0, 0, 0)
        controls_layout.setSpacing(3)

        # Move Up Button (▲)
        self.up_btn = QPushButton("▲")
        self.up_btn.setFixedSize(22, 24)
        self.up_btn.setCursor(Qt.CursorShape.PointingHandCursor)
        self.up_btn.setToolTip("Move Step Up")
        self.up_btn.setEnabled(not self.is_first)
        self.up_btn.setStyleSheet(
            """
            QPushButton {
                background-color: #0c1220;
                border: 1px solid #1a253a;
                border-radius: 5px;
                color: #94a3b8;
                font-size: 10px;
                font-weight: bold;
                padding: 0px;
            }
            QPushButton:hover {
                background-color: #16243e;
                border-color: #2563eb;
                color: #38bdf8;
            }
            QPushButton:disabled {
                background-color: transparent;
                border-color: transparent;
                color: #222d42;
            }
            """
        )
        self.up_btn.clicked.connect(lambda: self.move_up_clicked.emit(self.index))
        controls_layout.addWidget(self.up_btn)

        # Move Down Button (▼)
        self.down_btn = QPushButton("▼")
        self.down_btn.setFixedSize(22, 24)
        self.down_btn.setCursor(Qt.CursorShape.PointingHandCursor)
        self.down_btn.setToolTip("Move Step Down")
        self.down_btn.setEnabled(not self.is_last)
        self.down_btn.setStyleSheet(
            """
            QPushButton {
                background-color: #0c1220;
                border: 1px solid #1a253a;
                border-radius: 5px;
                color: #94a3b8;
                font-size: 10px;
                font-weight: bold;
                padding: 0px;
            }
            QPushButton:hover {
                background-color: #16243e;
                border-color: #2563eb;
                color: #38bdf8;
            }
            QPushButton:disabled {
                background-color: transparent;
                border-color: transparent;
                color: #222d42;
            }
            """
        )
        self.down_btn.clicked.connect(lambda: self.move_down_clicked.emit(self.index))
        controls_layout.addWidget(self.down_btn)

        # Overflow Menu Button (⋮)
        self.menu_btn = QPushButton("⋮")
        self.menu_btn.setFixedSize(24, 24)
        self.menu_btn.setCursor(Qt.CursorShape.PointingHandCursor)
        self.menu_btn.setToolTip("Step Options")
        self.menu_btn.setStyleSheet(
            """
            QPushButton {
                background-color: transparent;
                border: 1px solid transparent;
                border-radius: 5px;
                color: #64748b;
                font-size: 15px;
                font-weight: bold;
                padding: 0px;
            }
            QPushButton:hover {
                background-color: #151c2e;
                border-color: #222d46;
                color: #f8fafc;
            }
            """
        )
        self.menu_btn.clicked.connect(self._show_context_menu)
        controls_layout.addWidget(self.menu_btn)

        # Drag Handle Icon (⠿)
        self.drag_btn = QPushButton("⠿")
        self.drag_btn.setFixedSize(18, 24)
        self.drag_btn.setCursor(Qt.CursorShape.SizeAllCursor)
        self.drag_btn.setToolTip("Reorder Step")
        self.drag_btn.setStyleSheet(
            """
            QPushButton {
                background-color: transparent;
                border: none;
                color: #475569;
                font-size: 12px;
                font-weight: bold;
                padding: 0px;
            }
            QPushButton:hover {
                color: #94a3b8;
            }
            """
        )
        self.drag_btn.clicked.connect(self._show_context_menu)
        controls_layout.addWidget(self.drag_btn)

        card_layout.addWidget(controls_container)

        layout.addWidget(self.card, stretch=1)

    def _paint_step_col(self, event) -> None:
        """Draw workflow connecting lines, node badge and connector chevron."""
        painter = QPainter(self.step_col)
        painter.setRenderHint(QPainter.RenderHint.Antialiasing)

        w = self.step_col.width()
        h = self.step_col.height()
        cx = 20
        cy = h // 2

        # 1. Vertical workflow connecting line
        pen = QPen(QColor("#1b2336"), 2)
        painter.setPen(pen)

        if not self.is_first:
            painter.drawLine(cx, 0, cx, cy - 13)
        if not self.is_last:
            painter.drawLine(cx, cy + 13, cx, h)

        # 2. Numbered Step Badge Pill
        badge_w = 30
        badge_h = 22
        badge_rect = QRectF(cx - badge_w / 2, cy - badge_h / 2, badge_w, badge_h)

        path = QPainterPath()
        path.addRoundedRect(badge_rect, 6, 6)
        painter.fillPath(path, QBrush(QColor("#0a0e19")))
        painter.setPen(QPen(QColor("#1e273c"), 1))
        painter.drawPath(path)

        # Draw Step Number: '01', '02', etc.
        font = QFont("Segoe UI Variable Text", 9, QFont.Weight.Bold)
        painter.setFont(font)
        painter.setPen(QColor("#94a3b8"))
        step_str = f"{self.index + 1:02d}"
        painter.drawText(badge_rect, Qt.AlignmentFlag.AlignCenter, step_str)

        # 3. Connector chevron pointing into card
        painter.setPen(QColor("#2563eb"))
        chevron_rect = QRectF(w - 12, cy - 6, 10, 12)
        font_ch = QFont("Segoe UI", 7, QFont.Weight.Bold)
        painter.setFont(font_ch)
        painter.drawText(chevron_rect, Qt.AlignmentFlag.AlignCenter, "▶")

    def _resolve_icon(self) -> str:
        t = self.action_config.type.lower()
        app = str(self.action_config.params.get("application", "")).lower()
        name = str(self.action_config.name or "").lower()
        if "vscode" in app or "code" in app or "visual studio code" in name:
            return "</>"
        if "terminal" in app or "wt" in app or "cmd" in app or "terminal" in name:
            return "Σ"
        if "steam" in app or "game" in app:
            return "🎮"
        if "discord" in app:
            return "💬"
        if "keyboard" in t:
            return "⌨"
        if "folder" in t or "dir" in t:
            return "📁"
        if "file" in t:
            return "📄"
        if "notification" in t:
            return "🔔"
        if "audio" in t:
            return "🎧"
        if "window" in t:
            return "🗔"
        if "wait" in t:
            return "⏱"
        return self.theme.get("icon", "⚡")

    def _resolve_chip_icon(self) -> str:
        t = self.action_config.type.lower()
        if "keyboard" in t:
            return ""  # Shortcut chip is clean text
        return self._resolve_icon()

    def _resolve_category_title(self) -> str:
        t = self.action_config.type.lower()
        if "process.launch" in t:
            return "Launch Application"
        if "process.terminate" in t:
            return "Close Application"
        if "keyboard.shortcut" in t:
            return "Send Keyboard Shortcut"
        if "keyboard.type" in t:
            return "Type Keyboard Text"
        if "folder.open" in t:
            return "Open Folder"
        if "file.open" in t:
            return "Open File"
        if "notification" in t:
            return "Show Notification"
        if "audio.set_volume" in t:
            return "Set System Volume"
        if "audio.set_output" in t:
            return "Change Audio Output"
        if "window.focus" in t:
            return "Focus Window"
        if "wait.delay" in t:
            return "Wait Delay"
        if "condition" in t:
            return "Condition Check"
        return self.action_config.get_display_name()

    def _resolve_app_pixmap(self, size: int = 24) -> Optional[QPixmap]:
        from app.services.icon_service import IconService
        t = self.action_config.type.lower()
        app = self.action_config.params.get("application")
        if app:
            pix = IconService.get_instance().get_app_icon_pixmap(str(app), size=size)
            if pix and not pix.isNull():
                return pix
        name = str(self.action_config.name or "")
        if name and "process" in t:
            pix = IconService.get_instance().get_app_icon_pixmap(name, size=size)
            if pix and not pix.isNull():
                return pix
        return None

    def _resolve_subtitle(self) -> str:
        if self.action_config.name:
            return self.action_config.name
        app = self.action_config.params.get("application")
        if app:
            from app.services.icon_service import IconService
            clean = IconService.get_instance().clean_app_name(str(app))
            if clean:
                return clean
            return str(app).title()
        keys = self.action_config.params.get("keys")
        if keys:
            return str(keys)
        path = self.action_config.params.get("path")
        if path:
            return Path(path).name or str(path)
        title = self.action_config.params.get("title")
        if title:
            return str(title)
        return self.action_config.type

    def _resolve_description(self) -> str:
        t = self.action_config.type.lower()
        app = str(self.action_config.params.get("application", "")).lower()
        name = str(self.action_config.name or "").lower()

        if "process.launch" in t:
            sub = self._resolve_subtitle()
            if "vscode" in app or "code" in app or "visual studio code" in name:
                return "Opens VS Code if not already running."
            if "terminal" in app or "wt" in app or "terminal" in name:
                return "Opens Windows Terminal and focuses it."
            if "steam" in app:
                return "Launches Steam client and loads gaming profile."
            if "discord" in app:
                return "Connects to Discord and activates voice room."
            return f"Opens {sub} if not already running."

        if "keyboard.shortcut" in t:
            keys = self.action_config.params.get("keys", "")
            if "`" in keys:
                return "Opens a new terminal tab."
            return f"Sends '{keys}' keystroke to the active window."

        if "folder.open" in t:
            return "Opens your development workspace."

        if "file.open" in t:
            return "Opens specified document or project file."

        if "notification" in t:
            return "Lets you know the mode is ready."

        if "audio.set_output" in t:
            dev = self.action_config.params.get("device", "Audio Device")
            return f"Switches default audio stream to {dev}."

        if "audio.set_volume" in t:
            vol = self.action_config.params.get("volume", 50)
            return f"Adjusts system audio output volume to {vol}%."

        if "wait.delay" in t:
            sec = self.action_config.params.get("seconds", 1)
            return f"Pauses execution flow for {sec}s."

        return f"Executes automation step."

    def _resolve_value_chip(self) -> str:
        app = self.action_config.params.get("application")
        if app:
            from app.services.icon_service import IconService
            clean = IconService.get_instance().clean_app_name(str(app))
            if clean:
                return clean
            return str(app)

        keys = self.action_config.params.get("keys")
        if keys:
            return str(keys)

        path = self.action_config.params.get("path")
        if path:
            return Path(path).name or str(path)

        title = self.action_config.params.get("title")
        if title:
            clean = title.replace("💻", "").replace("🎮", "").strip()
            return clean or str(title)

        dev = self.action_config.params.get("device")
        if dev:
            return str(dev)

        vol = self.action_config.params.get("volume")
        if vol is not None:
            return f"{vol}%"

        sec = self.action_config.params.get("seconds")
        if sec is not None:
            return f"{sec}s"

        return ""

    def _show_context_menu(self) -> None:
        menu = QMenu(self)
        menu.setStyleSheet(
            """
            QMenu {
                background-color: #0d121f;
                color: #f8fafc;
                border: 1px solid #1e283e;
                border-radius: 8px;
                padding: 4px;
            }
            QMenu::item {
                padding: 6px 18px;
                border-radius: 6px;
                font-size: 12px;
            }
            QMenu::item:selected {
                background-color: #1d283f;
                color: #38bdf8;
            }
            """
        )

        act_edit = menu.addAction("✎ Edit Parameters")
        act_dup = menu.addAction("❐ Duplicate Step")
        menu.addSeparator()
        act_up = menu.addAction("▲ Move Up")
        act_up.setEnabled(not self.is_first)
        act_down = menu.addAction("▼ Move Down")
        act_down.setEnabled(not self.is_last)
        menu.addSeparator()
        act_del = menu.addAction("✕ Delete Step")

        action = menu.exec(QCursor.pos())
        if action == act_edit:
            self.edit_clicked.emit(self.index)
        elif action == act_dup:
            self.duplicate_clicked.emit(self.index)
        elif action == act_up:
            self.move_up_clicked.emit(self.index)
        elif action == act_down:
            self.move_down_clicked.emit(self.index)
        elif action == act_del:
            self.delete_clicked.emit(self.index)
