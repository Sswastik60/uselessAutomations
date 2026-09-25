"""Apple-grade Mode Editor View matching the exact reference visual direction.

Features:
- AMOLED-black cinematic dark aesthetic
- Two-column layout: Mode identity + Action Sequence (Left), Live Preview + Quick Actions (Right)
- Right-aligned cosmic mountain banner with gradient fade-out
- Connected workflow pipeline rows with numbered steps, icons, descriptions, value chips, overflow menu, and drag handle
- Top bar with Back button, title, live search (Ctrl+K), Test Mode, and Save Changes
- Live Mode Preview that updates in real-time as fields change
- Advanced collapsible section keeping technical configuration out of the primary visual hierarchy
- High-fidelity typography (Segoe UI Variable), subtle depth, and smooth animations
"""

from datetime import datetime
from pathlib import Path
from typing import List, Optional

from PySide6.QtCore import QPoint, QRect, QRectF, Qt, Signal
from PySide6.QtGui import (
    QBrush,
    QColor,
    QFont,
    QKeyEvent,
    QLinearGradient,
    QPainter,
    QPainterPath,
    QPen,
    QPixmap,
    QRadialGradient,
)
from PySide6.QtWidgets import (
    QFrame,
    QHBoxLayout,
    QLabel,
    QLineEdit,
    QMessageBox,
    QPushButton,
    QScrollArea,
    QSizePolicy,
    QVBoxLayout,
    QWidget,
)

from app.models.action import ActionConfig
from app.models.mode import Mode
from app.ui.action_editor import ActionEditorDialog
from app.ui.smooth_scroll import install_smooth_scroll
from app.ui.widgets.action_row import ActionRowWidget
from app.ui.widgets.app_picker_dialog import AppPickerDialog


class ThemeOrbButton(QPushButton):
    """Spherical blue-purple glowing orb button for theme selection."""

    def __init__(self, parent=None):
        super().__init__(parent)
        self.setFixedSize(30, 30)
        self.setCursor(Qt.CursorShape.PointingHandCursor)
        self.setToolTip("Accent Theme: Cosmic Blue / Indigo")

    def paintEvent(self, event) -> None:
        painter = QPainter(self)
        painter.setRenderHint(QPainter.RenderHint.Antialiasing)

        rect = self.rect()
        w = rect.width()
        h = rect.height()
        r = min(w, h) / 2.0 - 2.0

        # Radial 3D sphere gradient
        grad = QRadialGradient(w * 0.38, h * 0.35, r)
        grad.setColorAt(0.0, QColor("#60a5fa"))
        grad.setColorAt(0.45, QColor("#3b82f6"))
        grad.setColorAt(0.80, QColor("#1d4ed8"))
        grad.setColorAt(1.0, QColor("#1e1b4b"))

        painter.setBrush(QBrush(grad))
        painter.setPen(QPen(QColor("#38bdf8"), 1))
        painter.drawEllipse(QPoint(int(w / 2), int(h / 2)), int(r), int(r))

        # Specular reflection highlight
        spec_grad = QRadialGradient(w * 0.35, h * 0.30, r * 0.5)
        spec_grad.setColorAt(0.0, QColor(255, 255, 255, 180))
        spec_grad.setColorAt(1.0, QColor(255, 255, 255, 0))
        painter.setBrush(QBrush(spec_grad))
        painter.setPen(Qt.PenStyle.NoPen)
        painter.drawEllipse(QPoint(int(w * 0.35), int(h * 0.30)), int(r * 0.35), int(r * 0.25))


class IdentityHotkeyWidget(QFrame):
    """Sleek dark pill widget for displaying and recording global hotkeys."""

    hotkey_changed = Signal(str)

    def __init__(self, parent=None):
        super().__init__(parent)
        self.is_recording = False
        self.current_hotkey = ""
        self.setFixedHeight(34)
        self.setCursor(Qt.CursorShape.PointingHandCursor)

        self.setStyleSheet(
            """
            IdentityHotkeyWidget {
                background-color: #0c0f18;
                border: 1px solid #1a2234;
                border-radius: 8px;
            }
            IdentityHotkeyWidget:hover {
                border-color: #2b3954;
                background-color: #101522;
            }
            """
        )

        layout = QHBoxLayout(self)
        layout.setContentsMargins(12, 0, 12, 0)
        layout.setSpacing(8)

        self.icon_lbl = QLabel("⌨")
        self.icon_lbl.setStyleSheet("font-size: 13px; color: #64748b; background: transparent;")

        self.text_lbl = QLabel("CTRL + ALT + C")
        self.text_lbl.setStyleSheet("font-size: 12px; font-weight: 600; color: #f8fafc; background: transparent;")

        layout.addWidget(self.icon_lbl)
        layout.addWidget(self.text_lbl, stretch=1)

    def mousePressEvent(self, event) -> None:
        if event.button() == Qt.MouseButton.LeftButton:
            self.start_recording()
        super().mousePressEvent(event)

    def start_recording(self) -> None:
        self.is_recording = True
        self.text_lbl.setText("Press shortcut keys...")
        self.text_lbl.setStyleSheet("font-size: 12px; font-weight: 600; color: #38bdf8; background: transparent;")
        self.setStyleSheet(
            """
            IdentityHotkeyWidget {
                background-color: #0c1424;
                border: 1px solid #0284c7;
                border-radius: 8px;
            }
            """
        )
        self.grabKeyboard()

    def keyPressEvent(self, event: QKeyEvent) -> None:
        if not self.is_recording:
            super().keyPressEvent(event)
            return

        key = event.key()
        if key in (Qt.Key.Key_Control, Qt.Key.Key_Shift, Qt.Key.Key_Alt, Qt.Key.Key_Meta):
            return  # Modifier only, wait for combo key

        if key == Qt.Key.Key_Escape:
            self.stop_recording()
            self._update_display()
            return

        parts = []
        mods = event.modifiers()
        if mods & Qt.KeyboardModifier.ControlModifier:
            parts.append("CTRL")
        if mods & Qt.KeyboardModifier.AltModifier:
            parts.append("ALT")
        if mods & Qt.KeyboardModifier.ShiftModifier:
            parts.append("SHIFT")
        if mods & Qt.KeyboardModifier.MetaModifier:
            parts.append("WIN")

        if Qt.Key.Key_A <= key <= Qt.Key.Key_Z:
            parts.append(chr(key))
        elif Qt.Key.Key_0 <= key <= Qt.Key.Key_9:
            parts.append(chr(key))
        elif Qt.Key.Key_F1 <= key <= Qt.Key.Key_F12:
            parts.append(f"F{key - Qt.Key.Key_F1 + 1}")
        elif key == Qt.Key.Key_Space:
            parts.append("SPACE")
        elif key in (Qt.Key.Key_Return, Qt.Key.Key_Enter):
            parts.append("ENTER")

        if parts:
            combo = " + ".join(parts)
            self.current_hotkey = combo.replace(" + ", "+")
            self.stop_recording()
            self._update_display()
            self.hotkey_changed.emit(self.current_hotkey)

    def stop_recording(self) -> None:
        self.is_recording = False
        self.releaseKeyboard()
        self.setStyleSheet(
            """
            IdentityHotkeyWidget {
                background-color: #0c0f18;
                border: 1px solid #1a2234;
                border-radius: 8px;
            }
            IdentityHotkeyWidget:hover {
                border-color: #2b3954;
                background-color: #101522;
            }
            """
        )

    def _update_display(self) -> None:
        if self.current_hotkey:
            display = self.current_hotkey.replace("+", " + ")
            self.text_lbl.setText(display)
            self.text_lbl.setStyleSheet("font-size: 12px; font-weight: 600; color: #f8fafc; background: transparent;")
        else:
            self.text_lbl.setText("Record Hotkey...")
            self.text_lbl.setStyleSheet("font-size: 12px; font-weight: 500; color: #64748b; background: transparent;")

    def text(self) -> str:
        return self.current_hotkey

    def setText(self, hotkey_str: str) -> None:
        self.current_hotkey = hotkey_str or ""
        self._update_display()


class ModeIdentityCard(QFrame):
    """Cinematic Mode identity container with right-aligned cosmic mountain wallpaper."""

    def __init__(self, parent=None):
        super().__init__(parent)
        self.setFixedHeight(144)
        self.setObjectName("ModeIdentityCard")

        # Load banner artwork
        self.banner_pixmap: Optional[QPixmap] = None
        app_dir = Path(__file__).resolve().parent.parent.parent
        img_path = app_dir / "assets" / "ui" / "banner_mountain.jpg"
        if not img_path.exists():
            img_path = app_dir / "assets" / "ui" / "mode_coding.jpg"
        if img_path.exists():
            self.banner_pixmap = QPixmap(str(img_path))

    def paintEvent(self, event) -> None:
        painter = QPainter(self)
        painter.setRenderHint(QPainter.RenderHint.Antialiasing)
        painter.setRenderHint(QPainter.RenderHint.SmoothPixmapTransform)

        rect = self.rect()
        w = rect.width()
        h = rect.height()

        path = QPainterPath()
        path.addRoundedRect(QRectF(rect), 16, 16)
        painter.setClipPath(path)

        # AMOLED-black base fill
        painter.fillPath(path, QBrush(QColor("#070a12")))

        # Right-aligned mountain artwork
        if self.banner_pixmap and not self.banner_pixmap.isNull():
            art_w = int(w * 0.48)
            art_rect = QRect(w - art_w, 0, art_w, h)
            scaled = self.banner_pixmap.scaled(
                art_rect.size(),
                Qt.AspectRatioMode.KeepAspectRatioByExpanding,
                Qt.TransformationMode.SmoothTransformation,
            )
            painter.drawPixmap(art_rect, scaled)

            # Smooth horizontal linear gradient fading to black leftwards
            fade_grad = QLinearGradient(w - art_w - 60, 0, w, 0)
            fade_grad.setColorAt(0.0, QColor(7, 10, 18, 255))
            fade_grad.setColorAt(0.35, QColor(7, 10, 18, 230))
            fade_grad.setColorAt(0.70, QColor(7, 10, 18, 100))
            fade_grad.setColorAt(1.0, QColor(7, 10, 18, 0))
            painter.fillRect(art_rect.adjusted(-65, 0, 0, 0), QBrush(fade_grad))

        # Subtle crisp border
        pen = QPen(QColor("#151c2c"), 1)
        painter.setPen(pen)
        painter.setBrush(Qt.BrushStyle.NoBrush)
        painter.drawRoundedRect(QRectF(rect).adjusted(0.5, 0.5, -0.5, -0.5), 16, 16)


class LivePreviewCard(QFrame):
    """Dynamic preview card showing live mode look, banner, and quick play trigger."""

    play_clicked = Signal()

    def __init__(self, parent=None):
        super().__init__(parent)
        self.setObjectName("LivePreviewCard")
        self.setFixedHeight(240)
        self.setStyleSheet(
            """
            #LivePreviewCard {
                background-color: #080b15;
                border: 1px solid #1a2236;
                border-radius: 16px;
            }
            """
        )

        # Load banner artwork
        self.banner_pixmap: Optional[QPixmap] = None
        app_dir = Path(__file__).resolve().parent.parent.parent
        img_path = app_dir / "assets" / "ui" / "banner_mountain.jpg"
        if not img_path.exists():
            img_path = app_dir / "assets" / "ui" / "mode_coding.jpg"
        if img_path.exists():
            self.banner_pixmap = QPixmap(str(img_path))

        layout = QVBoxLayout(self)
        layout.setContentsMargins(16, 12, 16, 14)
        layout.setSpacing(6)

        # Top area: Ready badge at top right
        top_row = QHBoxLayout()
        top_row.setContentsMargins(0, 0, 0, 0)
        top_row.addStretch()

        self.ready_badge = QLabel("• Ready")
        self.ready_badge.setStyleSheet(
            """
            QLabel {
                color: #10b981;
                background-color: rgba(6, 78, 59, 0.85);
                border: 1px solid #059669;
                border-radius: 10px;
                font-size: 11px;
                font-weight: 600;
                padding: 2px 10px;
            }
            """
        )
        top_row.addWidget(self.ready_badge)
        layout.addLayout(top_row)

        # Spacer to push icon badge down to the banner seam
        layout.addSpacing(26)

        # Overlapping Icon Badge
        self.icon_badge = QLabel("</>")
        self.icon_badge.setFixedSize(46, 46)
        self.icon_badge.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.icon_badge.setStyleSheet(
            """
            QLabel {
                background-color: #0c1428;
                border: 1.5px solid #2563eb;
                border-radius: 12px;
                color: #38bdf8;
                font-size: 19px;
                font-weight: 700;
                font-family: 'Segoe UI Variable Display', 'Segoe UI Mono', monospace;
            }
            """
        )
        layout.addWidget(self.icon_badge)

        # Mode Title
        self.title_lbl = QLabel("Coding Mode")
        self.title_lbl.setStyleSheet(
            """
            font-size: 16px;
            font-weight: 700;
            color: #ffffff;
            background: transparent;
            font-family: 'Segoe UI Variable Display', 'Segoe UI', -apple-system, sans-serif;
            """
        )
        layout.addWidget(self.title_lbl)

        # Mode Description
        self.desc_lbl = QLabel("Launch editor, open terminal, and set up workspace.")
        self.desc_lbl.setWordWrap(True)
        self.desc_lbl.setStyleSheet("font-size: 11px; color: #94a3b8; background: transparent; line-height: 1.3;")
        layout.addWidget(self.desc_lbl)

        layout.addStretch()

        # Bottom Row: Hotkey Chip + Circular Play Button
        bot_row = QHBoxLayout()
        bot_row.setContentsMargins(0, 0, 0, 0)

        self.hotkey_chip = QLabel("⌨  CTRL + ALT + C")
        self.hotkey_chip.setStyleSheet(
            """
            QLabel {
                color: #cbd5e1;
                background-color: #0c111e;
                border: 1px solid #1c263c;
                border-radius: 6px;
                font-size: 10px;
                font-weight: 600;
                padding: 4px 8px;
            }
            """
        )

        self.play_btn = QPushButton("▶")
        self.play_btn.setFixedSize(38, 38)
        self.play_btn.setCursor(Qt.CursorShape.PointingHandCursor)
        self.play_btn.setToolTip("Test Mode Now")
        self.play_btn.setStyleSheet(
            """
            QPushButton {
                background-color: #0f1c38;
                border: 1.5px solid #2563eb;
                border-radius: 19px;
                color: #38bdf8;
                font-size: 14px;
                font-weight: bold;
            }
            QPushButton:hover {
                background-color: #1d4ed8;
                color: #ffffff;
            }
            """
        )
        self.play_btn.clicked.connect(self.play_clicked.emit)

        bot_row.addWidget(self.hotkey_chip)
        bot_row.addStretch()
        bot_row.addWidget(self.play_btn)
        layout.addLayout(bot_row)

    def paintEvent(self, event) -> None:
        painter = QPainter(self)
        painter.setRenderHint(QPainter.RenderHint.Antialiasing)
        painter.setRenderHint(QPainter.RenderHint.SmoothPixmapTransform)

        rect = self.rect()
        w = rect.width()

        path = QPainterPath()
        path.addRoundedRect(QRectF(rect), 16, 16)
        painter.setClipPath(path)

        # Base background fill
        painter.fillPath(path, QBrush(QColor("#080b15")))

        # Top banner background artwork
        if self.banner_pixmap and not self.banner_pixmap.isNull():
            banner_h = 96
            banner_rect = QRect(0, 0, w, banner_h)
            scaled = self.banner_pixmap.scaled(
                banner_rect.size(),
                Qt.AspectRatioMode.KeepAspectRatioByExpanding,
                Qt.TransformationMode.SmoothTransformation,
            )
            painter.drawPixmap(banner_rect, scaled)

            # Gradient overlay to blend bottom of banner into card
            fade = QLinearGradient(0, 0, 0, banner_h)
            fade.setColorAt(0.0, QColor(8, 11, 21, 30))
            fade.setColorAt(0.70, QColor(8, 11, 21, 140))
            fade.setColorAt(1.0, QColor(8, 11, 21, 255))
            painter.fillRect(banner_rect, QBrush(fade))

        # Border
        pen = QPen(QColor("#1a2236"), 1)
        painter.setPen(pen)
        painter.setBrush(Qt.BrushStyle.NoBrush)
        painter.drawRoundedRect(QRectF(rect).adjusted(0.5, 0.5, -0.5, -0.5), 16, 16)


class ModeEditorView(QWidget):
    """World-class Mode Editor designed to match the attached reference aesthetic."""

    save_requested = Signal(Mode)
    delete_requested = Signal(str)  # mode_id
    export_requested = Signal(str)  # mode_id
    test_requested = Signal(str)    # mode_id
    cancelled = Signal()

    ICON_PRESETS = [
        ("</>", "Code / Development"),
        ("Σ", "Terminal / Math"),
        ("💻", "Computer / Workstation"),
        ("🖥️", "Desktop Setup"),
        ("🎛️", "Production / Synth"),
    ]

    def __init__(self, parent=None):
        super().__init__(parent)
        self.current_mode_id: Optional[str] = None
        self.actions_list: List[ActionConfig] = []
        self.current_icon = "</>"
        self.selected_preset_btn: Optional[QPushButton] = None

        self.setObjectName("ModeEditorView")
        self.setAttribute(Qt.WidgetAttribute.WA_StyledBackground, True)
        self.setAutoFillBackground(True)
        self.setStyleSheet(
            """
            QWidget#ModeEditorView {
                background-color: #030305;
                font-family: 'Segoe UI Variable Text', 'Segoe UI', -apple-system, sans-serif;
                color: #f8fafc;
            }
            """
        )

        root_layout = QVBoxLayout(self)
        root_layout.setContentsMargins(24, 18, 24, 18)
        root_layout.setSpacing(14)

        # -------------------------------------------------------------
        # 1. Top Navigation & Action Bar
        # -------------------------------------------------------------
        top_bar = QHBoxLayout()
        top_bar.setContentsMargins(0, 0, 0, 0)
        top_bar.setSpacing(14)

        # Left: Back button + Mode Header Title & Subtitle
        header_left = QVBoxLayout()
        header_left.setSpacing(3)

        self.back_btn = QPushButton("← Back to Modes")
        self.back_btn.setCursor(Qt.CursorShape.PointingHandCursor)
        self.back_btn.setStyleSheet(
            """
            QPushButton {
                background-color: transparent;
                border: 1px solid #1a2234;
                border-radius: 12px;
                color: #94a3b8;
                font-size: 11px;
                font-weight: 500;
                padding: 3px 10px;
                max-width: 120px;
            }
            QPushButton:hover {
                background-color: #121724;
                border-color: #2b3952;
                color: #f8fafc;
            }
            """
        )
        self.back_btn.clicked.connect(self.cancelled.emit)
        header_left.addWidget(self.back_btn)

        self.header_title = QLabel("Edit Mode: Coding Mode")
        self.header_title.setStyleSheet(
            """
            font-size: 22px;
            font-weight: 750;
            color: #ffffff;
            letter-spacing: -0.5px;
            font-family: 'Segoe UI Variable Display', 'Segoe UI', -apple-system, sans-serif;
            background: transparent;
            """
        )
        header_left.addWidget(self.header_title)

        self.header_sub = QLabel("Launch editor, open terminal, and set up workspace.")
        self.header_sub.setStyleSheet("font-size: 12px; color: #94a3b8; background: transparent;")
        header_left.addWidget(self.header_sub)

        top_bar.addLayout(header_left, stretch=1)

        # Right: Search Box + Test Mode Button + Save Changes Button
        search_box = QFrame()
        search_box.setFixedSize(260, 36)
        search_box.setStyleSheet(
            """
            QFrame {
                background-color: #0b0e17;
                border: 1px solid #1a2030;
                border-radius: 18px;
            }
            QFrame:focus-within {
                border-color: #0284c7;
            }
            """
        )
        sb_layout = QHBoxLayout(search_box)
        sb_layout.setContentsMargins(12, 0, 10, 0)
        sb_layout.setSpacing(8)

        search_icon = QLabel("🔍")
        search_icon.setStyleSheet("font-size: 11px; color: #64748b; background: transparent;")
        sb_layout.addWidget(search_icon)

        self.search_input = QLineEdit()
        self.search_input.setPlaceholderText("Search actions, apps, or settings...")
        self.search_input.setStyleSheet("background: transparent; border: none; font-size: 11px; color: #f8fafc;")
        self.search_input.textChanged.connect(self._on_search_changed)
        sb_layout.addWidget(self.search_input, stretch=1)

        shortcut_badge = QLabel("Ctrl K")
        shortcut_badge.setStyleSheet(
            """
            background-color: #141b2a;
            border: 1px solid #222d44;
            border-radius: 4px;
            color: #64748b;
            font-size: 10px;
            font-weight: 600;
            padding: 1px 4px;
            """
        )
        sb_layout.addWidget(shortcut_badge)
        top_bar.addWidget(search_box)

        # Test Mode Button
        self.test_btn = QPushButton("▶  Test Mode")
        self.test_btn.setFixedSize(110, 36)
        self.test_btn.setCursor(Qt.CursorShape.PointingHandCursor)
        self.test_btn.setStyleSheet(
            """
            QPushButton {
                background-color: #0e1320;
                border: 1px solid #1e283e;
                border-radius: 18px;
                color: #f8fafc;
                font-size: 12px;
                font-weight: 600;
            }
            QPushButton:hover {
                background-color: #162035;
                border-color: #2e3e60;
            }
            """
        )
        self.test_btn.clicked.connect(self._on_test_clicked)
        top_bar.addWidget(self.test_btn)

        # Save Changes Button
        self.save_btn = QPushButton("💾  Save Changes")
        self.save_btn.setFixedSize(134, 36)
        self.save_btn.setCursor(Qt.CursorShape.PointingHandCursor)
        self.save_btn.setStyleSheet(
            """
            QPushButton {
                background: qlineargradient(x1:0, y1:0, x2:1, y2:0, stop:0 #0070f3, stop:1 #00b4d8);
                border: 1px solid #38bdf8;
                border-radius: 18px;
                color: #ffffff;
                font-size: 12px;
                font-weight: 700;
            }
            QPushButton:hover {
                background: qlineargradient(x1:0, y1:0, x2:1, y2:0, stop:0 #0060df, stop:1 #009ec0);
            }
            QPushButton:pressed {
                background: #0050bc;
            }
            """
        )
        self.save_btn.clicked.connect(self._on_save_clicked)
        top_bar.addWidget(self.save_btn)

        root_layout.addLayout(top_bar)

        # -------------------------------------------------------------
        # 2. Cinematic Mode Identity Card
        # -------------------------------------------------------------
        self.identity_card = ModeIdentityCard()
        card_layout = QHBoxLayout(self.identity_card)
        card_layout.setContentsMargins(20, 16, 20, 16)
        card_layout.setSpacing(18)

        # Left: Glowing Icon Badge
        self.id_icon_badge = QLabel(self.current_icon)
        self.id_icon_badge.setFixedSize(68, 68)
        self.id_icon_badge.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.id_icon_badge.setStyleSheet(
            """
            QLabel {
                background-color: #0b1222;
                border: 1.5px solid #2563eb;
                border-radius: 16px;
                color: #38bdf8;
                font-size: 26px;
                font-weight: 750;
                font-family: 'Segoe UI Variable Display', 'Segoe UI Mono', monospace;
            }
            """
        )
        card_layout.addWidget(self.id_icon_badge)

        # Middle: Mode Name & Description inputs
        form_box = QVBoxLayout()
        form_box.setSpacing(8)

        # Mode Name Field
        name_vbox = QVBoxLayout()
        name_vbox.setSpacing(2)
        name_lbl = QLabel("Mode Name")
        name_lbl.setStyleSheet("font-size: 11px; font-weight: 600; color: #64748b; background: transparent;")
        self.name_input = QLineEdit()
        self.name_input.setPlaceholderText("Coding Mode")
        self.name_input.setStyleSheet(
            """
            QLineEdit {
                background-color: rgba(13, 17, 28, 0.85);
                border: 1px solid #1e2638;
                border-radius: 8px;
                color: #ffffff;
                font-size: 13px;
                font-weight: 600;
                padding: 6px 12px;
            }
            QLineEdit:focus {
                border-color: #0284c7;
                background-color: rgba(16, 22, 36, 0.98);
            }
            """
        )
        self.name_input.textChanged.connect(self._on_name_changed)
        name_vbox.addWidget(name_lbl)
        name_vbox.addWidget(self.name_input)
        form_box.addLayout(name_vbox)

        # Description Field
        desc_vbox = QVBoxLayout()
        desc_vbox.setSpacing(2)
        desc_lbl = QLabel("Description")
        desc_lbl.setStyleSheet("font-size: 11px; font-weight: 600; color: #64748b; background: transparent;")
        self.desc_input = QLineEdit()
        self.desc_input.setPlaceholderText("Launch editor, open terminal, and set up workspace.")
        self.desc_input.setStyleSheet(
            """
            QLineEdit {
                background-color: rgba(13, 17, 28, 0.85);
                border: 1px solid #1e2638;
                border-radius: 8px;
                color: #94a3b8;
                font-size: 12px;
                padding: 6px 12px;
            }
            QLineEdit:focus {
                border-color: #0284c7;
                color: #ffffff;
                background-color: rgba(16, 22, 36, 0.98);
            }
            """
        )
        self.desc_input.textChanged.connect(self._on_desc_changed)
        desc_vbox.addWidget(desc_lbl)
        desc_vbox.addWidget(self.desc_input)
        form_box.addLayout(desc_vbox)

        card_layout.addLayout(form_box, stretch=1)

        # Right: Global Hotkey + Icon & Theme Selector
        right_controls = QVBoxLayout()
        right_controls.setSpacing(8)

        # Global Hotkey
        hotkey_box = QVBoxLayout()
        hotkey_box.setSpacing(2)
        hotkey_lbl = QLabel("Global Hotkey")
        hotkey_lbl.setStyleSheet("font-size: 11px; font-weight: 600; color: #cbd5e1; background: transparent;")
        self.hotkey_widget = IdentityHotkeyWidget()
        self.hotkey_widget.setFixedWidth(200)
        self.hotkey_widget.hotkey_changed.connect(self._on_hotkey_changed)
        hotkey_box.addWidget(hotkey_lbl)
        hotkey_box.addWidget(self.hotkey_widget)
        right_controls.addLayout(hotkey_box)

        # Icon & Theme Row
        theme_box = QVBoxLayout()
        theme_box.setSpacing(2)
        theme_lbl = QLabel("Icon & Theme")
        theme_lbl.setStyleSheet("font-size: 11px; font-weight: 600; color: #cbd5e1; background: transparent;")

        theme_row = QHBoxLayout()
        theme_row.setSpacing(5)

        self.preset_btns = []
        for icon_symbol, tooltip in self.ICON_PRESETS:
            btn = QPushButton(icon_symbol)
            btn.setFixedSize(30, 30)
            btn.setCursor(Qt.CursorShape.PointingHandCursor)
            btn.setToolTip(tooltip)
            btn.clicked.connect(lambda _, ic=icon_symbol, b=btn: self._select_icon_preset(ic, b))
            theme_row.addWidget(btn)
            self.preset_btns.append(btn)

        # Theme Orb Selector
        self.theme_orb = ThemeOrbButton()
        theme_row.addWidget(self.theme_orb)

        theme_box.addWidget(theme_lbl)
        theme_box.addLayout(theme_row)
        right_controls.addLayout(theme_box)

        card_layout.addLayout(right_controls)
        root_layout.addWidget(self.identity_card)

        # -------------------------------------------------------------
        # 3. Two-Column Main Workspace
        # -------------------------------------------------------------
        workspace_layout = QHBoxLayout()
        workspace_layout.setContentsMargins(0, 0, 0, 0)
        workspace_layout.setSpacing(20)

        # -------------------------------------------------------------
        # Left / Main Column: Action Sequence (Workflow)
        # -------------------------------------------------------------
        left_col = QVBoxLayout()
        left_col.setSpacing(10)

        # Section Header
        act_header = QHBoxLayout()
        act_header_text = QVBoxLayout()
        act_header_text.setSpacing(1)

        act_title = QLabel("Action Sequence")
        act_title.setStyleSheet(
            """
            font-size: 16px;
            font-weight: 700;
            color: #f8fafc;
            background: transparent;
            font-family: 'Segoe UI Variable Display', 'Segoe UI', -apple-system, sans-serif;
            """
        )
        self.act_sub = QLabel("Define the steps your mode will execute, in order.")
        self.act_sub.setStyleSheet("font-size: 12px; color: #64748b; background: transparent;")

        act_header_text.addWidget(act_title)
        act_header_text.addWidget(self.act_sub)
        act_header.addLayout(act_header_text, stretch=1)

        # + Add Action Button
        self.add_act_btn = QPushButton("+  Add Action")
        self.add_act_btn.setFixedSize(116, 30)
        self.add_act_btn.setCursor(Qt.CursorShape.PointingHandCursor)
        self.add_act_btn.setStyleSheet(
            """
            QPushButton {
                background-color: #0e1526;
                border: 1px solid #1e2e4a;
                border-radius: 15px;
                color: #38bdf8;
                font-size: 12px;
                font-weight: 600;
            }
            QPushButton:hover {
                background-color: #142038;
                border-color: #0284c7;
            }
            """
        )
        self.add_act_btn.clicked.connect(self._on_add_action)
        act_header.addWidget(self.add_act_btn)
        left_col.addLayout(act_header)

        # Actions Scroll Container
        self.scroll = QScrollArea()
        self.scroll.setWidgetResizable(True)
        self.scroll.setHorizontalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAlwaysOff)
        self.smooth_scroll = install_smooth_scroll(self.scroll)
        self.scroll.setStyleSheet(
            """
            QScrollArea {
                border: none;
                background: transparent;
            }
            QScrollBar:vertical {
                background: transparent;
                width: 6px;
                margin: 0px;
            }
            QScrollBar::handle:vertical {
                background: #1e2638;
                border-radius: 3px;
                min-height: 24px;
            }
            QScrollBar::handle:vertical:hover {
                background: #38bdf8;
            }
            QScrollBar::add-line:vertical, QScrollBar::sub-line:vertical {
                height: 0px;
            }
            """
        )

        self.actions_container = QWidget()
        self.actions_container.setStyleSheet("background: transparent;")
        self.actions_container.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Preferred)
        self.actions_layout = QVBoxLayout(self.actions_container)
        self.actions_layout.setContentsMargins(0, 0, 0, 0)
        self.actions_layout.setSpacing(4)
        self.actions_layout.setAlignment(Qt.AlignmentFlag.AlignTop)
        self.scroll.setWidget(self.actions_container)

        left_col.addWidget(self.scroll, stretch=1)

        # Bottom Bar: Status Footer Card
        self.status_footer = QFrame()
        self.status_footer.setFixedHeight(48)
        self.status_footer.setStyleSheet(
            """
            QFrame {
                background-color: #070a13;
                border: 1px solid #141926;
                border-radius: 10px;
            }
            """
        )
        sf_layout = QHBoxLayout(self.status_footer)
        sf_layout.setContentsMargins(14, 0, 16, 0)
        sf_layout.setSpacing(16)

        # Hotkey Chip
        self.footer_hotkey_box = QFrame()
        self.footer_hotkey_box.setStyleSheet(
            """
            QFrame {
                background-color: #0c101c;
                border: 1px solid #1a2234;
                border-radius: 6px;
            }
            """
        )
        fh_layout = QHBoxLayout(self.footer_hotkey_box)
        fh_layout.setContentsMargins(8, 2, 8, 2)
        fh_layout.setSpacing(8)

        fh_icon = QLabel("⌨")
        fh_icon.setStyleSheet("font-size: 12px; color: #64748b; background: transparent;")

        fh_text_vbox = QVBoxLayout()
        fh_text_vbox.setSpacing(0)
        self.footer_hotkey_lbl = QLabel("CTRL + ALT + C")
        self.footer_hotkey_lbl.setStyleSheet("font-size: 11px; font-weight: 600; color: #f8fafc; background: transparent;")
        fh_sub = QLabel("Global Hotkey")
        fh_sub.setStyleSheet("font-size: 9px; color: #64748b; background: transparent;")
        fh_text_vbox.addWidget(self.footer_hotkey_lbl)
        fh_text_vbox.addWidget(fh_sub)

        fh_layout.addWidget(fh_icon)
        fh_layout.addLayout(fh_text_vbox)
        sf_layout.addWidget(self.footer_hotkey_box)

        # Vertical Divider Line
        v_sep = QFrame()
        v_sep.setFrameShape(QFrame.Shape.VLine)
        v_sep.setStyleSheet("color: #1a2234; background-color: #1a2234; max-width: 1px; max-height: 24px;")
        sf_layout.addWidget(v_sep)

        # Status text
        status_box = QHBoxLayout()
        status_box.setSpacing(8)

        dot = QLabel("●")
        dot.setStyleSheet("font-size: 10px; color: #10b981; background: transparent;")

        status_text_box = QVBoxLayout()
        status_text_box.setSpacing(1)
        st_ready = QLabel("Mode is ready")
        st_ready.setStyleSheet("font-size: 11px; font-weight: 600; color: #10b981; background: transparent;")
        self.st_updated = QLabel(f"Last updated: Today, {datetime.now().strftime('%I:%M %p')}")
        self.st_updated.setStyleSheet("font-size: 10px; color: #64748b; background: transparent;")
        status_text_box.addWidget(st_ready)
        status_text_box.addWidget(self.st_updated)

        status_box.addWidget(dot)
        status_box.addLayout(status_text_box)
        sf_layout.addLayout(status_box)

        sf_layout.addStretch()

        left_col.addWidget(self.status_footer)
        workspace_layout.addLayout(left_col, stretch=1)

        # -------------------------------------------------------------
        # Right Column: Mode Preview & Quick Actions (~300px width)
        # -------------------------------------------------------------
        right_col = QVBoxLayout()
        right_col.setSpacing(12)
        right_col_widget = QWidget()
        right_col_widget.setFixedWidth(300)
        right_col_widget.setLayout(right_col)

        # Section Header
        prev_header_text = QVBoxLayout()
        prev_header_text.setSpacing(1)
        prev_title = QLabel("Mode Preview")
        prev_title.setStyleSheet(
            """
            font-size: 16px;
            font-weight: 700;
            color: #f8fafc;
            background: transparent;
            font-family: 'Segoe UI Variable Display', 'Segoe UI', -apple-system, sans-serif;
            """
        )
        prev_sub = QLabel("Here's how your mode will look and work.")
        prev_sub.setStyleSheet("font-size: 12px; color: #64748b; background: transparent;")
        prev_header_text.addWidget(prev_title)
        prev_header_text.addWidget(prev_sub)
        right_col.addLayout(prev_header_text)

        # Live Mode Preview Card
        self.preview_card = LivePreviewCard()
        self.preview_card.play_clicked.connect(self._on_test_clicked)
        right_col.addWidget(self.preview_card)

        # Quick Actions Header
        qa_lbl = QLabel("Quick Actions")
        qa_lbl.setStyleSheet("font-size: 13px; font-weight: 600; color: #cbd5e1; margin-top: 4px; background: transparent;")
        right_col.addWidget(qa_lbl)

        # Two Side-by-Side Quick Action Buttons
        qa_row = QHBoxLayout()
        qa_row.setSpacing(8)

        self.qa_test_btn = QPushButton("▶  Test Mode")
        self.qa_test_btn.setFixedHeight(34)
        self.qa_test_btn.setCursor(Qt.CursorShape.PointingHandCursor)
        self.qa_test_btn.setStyleSheet(
            """
            QPushButton {
                background-color: #0c111e;
                border: 1px solid #1c263c;
                border-radius: 8px;
                color: #f8fafc;
                font-size: 11px;
                font-weight: 600;
            }
            QPushButton:hover {
                background-color: #141d32;
                border-color: #2b3a5a;
            }
            """
        )
        self.qa_test_btn.clicked.connect(self._on_test_clicked)

        self.qa_export_btn = QPushButton("⤓  Export JSON")
        self.qa_export_btn.setFixedHeight(34)
        self.qa_export_btn.setCursor(Qt.CursorShape.PointingHandCursor)
        self.qa_export_btn.setStyleSheet(
            """
            QPushButton {
                background-color: #0c111e;
                border: 1px solid #1c263c;
                border-radius: 8px;
                color: #f8fafc;
                font-size: 11px;
                font-weight: 600;
            }
            QPushButton:hover {
                background-color: #141d32;
                border-color: #2b3a5a;
            }
            """
        )
        self.qa_export_btn.clicked.connect(self._on_export_clicked)

        qa_row.addWidget(self.qa_test_btn)
        qa_row.addWidget(self.qa_export_btn)
        right_col.addLayout(qa_row)

        # Advanced Collapsible Section
        self.advanced_container = QFrame()
        self.advanced_container.setStyleSheet(
            """
            QFrame {
                background-color: #080b14;
                border: 1px solid #161c2b;
                border-radius: 10px;
            }
            """
        )
        adv_layout = QVBoxLayout(self.advanced_container)
        adv_layout.setContentsMargins(12, 8, 12, 8)
        adv_layout.setSpacing(6)

        # Advanced Header Button (accordion toggle)
        self.adv_toggle_btn = QPushButton("⚙  Advanced                                     ›")
        self.adv_toggle_btn.setCursor(Qt.CursorShape.PointingHandCursor)
        self.adv_toggle_btn.setStyleSheet(
            """
            QPushButton {
                background: transparent;
                border: none;
                color: #94a3b8;
                font-size: 12px;
                font-weight: 600;
                text-align: left;
            }
            QPushButton:hover {
                color: #f8fafc;
            }
            """
        )
        self.adv_toggle_btn.clicked.connect(self._toggle_advanced)
        adv_layout.addWidget(self.adv_toggle_btn)

        # Advanced Content (initially hidden)
        self.adv_body = QWidget()
        self.adv_body.setVisible(False)
        adv_body_layout = QVBoxLayout(self.adv_body)
        adv_body_layout.setContentsMargins(0, 6, 0, 0)
        adv_body_layout.setSpacing(8)

        # Mode ID
        id_lbl = QLabel("Mode Identifier (Internal ID)")
        id_lbl.setStyleSheet("font-size: 10px; font-weight: 600; color: #64748b; background: transparent;")
        self.id_input = QLineEdit()
        self.id_input.setPlaceholderText("coding_mode")
        self.id_input.setStyleSheet(
            """
            QLineEdit {
                background-color: #0c101c;
                border: 1px solid #1a2234;
                border-radius: 6px;
                color: #94a3b8;
                font-size: 11px;
                padding: 5px 8px;
            }
            QLineEdit:disabled {
                color: #475569;
            }
            """
        )
        adv_body_layout.addWidget(id_lbl)
        adv_body_layout.addWidget(self.id_input)

        # Batch Add App Shortcuts button
        self.batch_apps_btn = QPushButton("📱  Batch Add App Shortcuts...")
        self.batch_apps_btn.setFixedHeight(28)
        self.batch_apps_btn.setCursor(Qt.CursorShape.PointingHandCursor)
        self.batch_apps_btn.setStyleSheet(
            """
            QPushButton {
                background-color: #0e1526;
                border: 1px solid #1e2c45;
                border-radius: 6px;
                color: #38bdf8;
                font-size: 11px;
                font-weight: 500;
            }
            QPushButton:hover {
                background-color: #141f35;
                border-color: #0284c7;
            }
            """
        )
        self.batch_apps_btn.clicked.connect(self._on_batch_add_apps)
        adv_body_layout.addWidget(self.batch_apps_btn)

        adv_layout.addWidget(self.adv_body)
        right_col.addWidget(self.advanced_container)

        # Delete Mode Link Button
        self.del_btn = QPushButton("🗑  Delete Mode")
        self.del_btn.setCursor(Qt.CursorShape.PointingHandCursor)
        self.del_btn.setStyleSheet(
            """
            QPushButton {
                background: transparent;
                border: none;
                color: #ef4444;
                font-size: 12px;
                font-weight: 500;
                text-align: left;
                padding: 4px 2px;
            }
            QPushButton:hover {
                color: #f87171;
            }
            """
        )
        self.del_btn.clicked.connect(self._on_delete_clicked)
        right_col.addWidget(self.del_btn)

        right_col.addStretch()
        workspace_layout.addWidget(right_col_widget)

        root_layout.addLayout(workspace_layout, stretch=1)

        # Initialize preset button styling
        self._select_icon_preset("</>", self.preset_btns[0])

    # -----------------------------------------------------------------
    # State & Load Methods
    # -----------------------------------------------------------------
    def load_mode(self, mode: Optional[Mode] = None) -> None:
        """Load mode into the redesigned editor."""
        if mode:
            self.current_mode_id = mode.id
            self.header_title.setText(f"Edit Mode: {mode.name}")
            self.header_sub.setText(mode.description or "Launch editor, open terminal, and set up workspace.")
            self.id_input.setText(mode.id)
            self.id_input.setEnabled(False)
            self.name_input.setText(mode.name)
            self.desc_input.setText(mode.description)

            # Actions
            self.actions_list = [ActionConfig.model_validate(a.model_dump()) for a in mode.actions]
            self.del_btn.setVisible(True)
            self.qa_export_btn.setVisible(True)

            # Resolve App Icon or fallback to preset icon
            from app.services.icon_service import IconService
            app_pix = IconService.get_instance().get_mode_app_icon(mode, size=48)
            if app_pix and not app_pix.isNull():
                self.current_icon = mode.icon if (mode.icon and mode.icon.startswith("app:")) else f"app:{mode.name.lower()}"
                self._set_pixmap_icon_display(app_pix)
            else:
                mode_icon = mode.icon or "</>"
                self.current_icon = mode_icon
                self._update_icon_display(mode_icon)

            # Hotkey
            hotkey_str = mode.hotkey or ""
            self.hotkey_widget.setText(hotkey_str)
            self._update_hotkey_display(hotkey_str)
        else:
            self.current_mode_id = None
            self.header_title.setText("Create New Mode")
            self.header_sub.setText("Define mode name, trigger hotkey, and automation workflow.")
            self.id_input.setText("")
            self.id_input.setEnabled(True)
            self.name_input.setText("")
            self.desc_input.setText("")
            self.current_icon = "</>"
            self._update_icon_display("</>")
            self.hotkey_widget.setText("")
            self._update_hotkey_display("")
            self.actions_list = []
            self.del_btn.setVisible(False)
            self.qa_export_btn.setVisible(False)

        self.st_updated.setText(f"Last updated: Today, {datetime.now().strftime('%I:%M %p')}")
        self.refresh_actions_list()

    def refresh_actions_list(self) -> None:
        """Render action workflow sequence rows with live search filtering."""
        while self.actions_layout.count():
            item = self.actions_layout.takeAt(0)
            if item.widget():
                item.widget().deleteLater()

        query = self.search_input.text().strip().lower()

        # Filter items
        filtered_actions = []
        for idx, act in enumerate(self.actions_list):
            if not query:
                filtered_actions.append((idx, act))
            else:
                text_corpus = f"{act.type} {act.name or ''} {str(act.params)}".lower()
                if query in text_corpus:
                    filtered_actions.append((idx, act))

        count = len(filtered_actions)
        total = len(self.actions_list)
        if query:
            self.act_sub.setText(f"Showing {count} of {total} steps matching '{query}'")
        else:
            self.act_sub.setText("Define the steps your mode will execute, in order.")

        if not filtered_actions:
            empty_lbl = QLabel(
                "No actions in sequence. Click '+  Add Action' or '📱 Batch Add App Shortcuts...' to build workflow."
                if not query else f"No steps match '{query}'."
            )
            empty_lbl.setStyleSheet(
                """
                color: #64748b;
                padding: 32px;
                font-style: italic;
                font-size: 13px;
                background-color: #070912;
                border: 1px dashed #1a2234;
                border-radius: 12px;
                """
            )
            empty_lbl.setAlignment(Qt.AlignmentFlag.AlignCenter)
            self.actions_layout.addWidget(empty_lbl)
            return

        total_visible = len(filtered_actions)
        for v_idx, (real_idx, act) in enumerate(filtered_actions):
            row = ActionRowWidget(
                index=real_idx,
                action_config=act,
                is_first=(v_idx == 0),
                is_last=(v_idx == total_visible - 1),
            )
            row.edit_clicked.connect(self._on_edit_action)
            row.move_up_clicked.connect(self._on_move_up)
            row.move_down_clicked.connect(self._on_move_down)
            row.duplicate_clicked.connect(self._on_duplicate_action)
            row.delete_clicked.connect(self._on_delete_action)

            self.actions_layout.addWidget(row)

    # -----------------------------------------------------------------
    # Live Preview Syncing Handlers
    # -----------------------------------------------------------------
    def _on_name_changed(self, text: str) -> None:
        display = text.strip() or "Mode Name"
        self.header_title.setText(f"Edit Mode: {display}")
        self.preview_card.title_lbl.setText(display)

    def _on_desc_changed(self, text: str) -> None:
        display = text.strip() or "Short description of what this mode automates"
        self.header_sub.setText(display)
        self.preview_card.desc_lbl.setText(display)

    def _on_hotkey_changed(self, hotkey_str: str) -> None:
        self._update_hotkey_display(hotkey_str)

    def _update_hotkey_display(self, hotkey_str: str) -> None:
        val = hotkey_str.replace("+", " + ") if hotkey_str else "None"
        self.preview_card.hotkey_chip.setText(f"⌨  {val}")
        self.footer_hotkey_lbl.setText(val)

    def _select_icon_preset(self, icon_symbol: str, target_btn: QPushButton) -> None:
        self.current_icon = icon_symbol
        self._update_icon_display(icon_symbol)

        for b in self.preset_btns:
            if b == target_btn:
                b.setStyleSheet(
                    """
                    QPushButton {
                        background-color: #12213d;
                        border: 1.5px solid #38bdf8;
                        border-radius: 6px;
                        color: #ffffff;
                        font-weight: bold;
                        font-size: 13px;
                    }
                    """
                )
            else:
                b.setStyleSheet(
                    """
                    QPushButton {
                        background-color: #0c101c;
                        border: 1px solid #1a2234;
                        border-radius: 6px;
                        color: #94a3b8;
                        font-size: 12px;
                    }
                    QPushButton:hover {
                        background-color: #141c2e;
                        border-color: #2b3952;
                        color: #f8fafc;
                    }
                    """
                )

    def _update_icon_display(self, icon_str: str) -> None:
        self.id_icon_badge.setPixmap(QPixmap())
        self.id_icon_badge.setText(icon_str)
        self.preview_card.icon_badge.setPixmap(QPixmap())
        self.preview_card.icon_badge.setText(icon_str)

    def _set_pixmap_icon_display(self, pix: QPixmap) -> None:
        """Render high-res application icon on the Mode Identity badge and Live Preview card."""
        id_pix = pix.scaled(44, 44, Qt.AspectRatioMode.KeepAspectRatio, Qt.TransformationMode.SmoothTransformation)
        self.id_icon_badge.setPixmap(id_pix)
        self.id_icon_badge.setText("")

        prev_pix = pix.scaled(30, 30, Qt.AspectRatioMode.KeepAspectRatio, Qt.TransformationMode.SmoothTransformation)
        self.preview_card.icon_badge.setPixmap(prev_pix)
        self.preview_card.icon_badge.setText("")

    def _auto_detect_app_icon(self) -> None:
        """Scan actions for launched applications (e.g. Valorant, Mem Reduct) and automatically update mode icon."""
        from app.services.icon_service import IconService
        for act in self.actions_list:
            if act.type == "process.launch":
                app_target = act.params.get("application", "")
                if app_target:
                    pix = IconService.get_instance().get_app_icon_pixmap(str(app_target), size=48)
                    if pix and not pix.isNull():
                        self.current_icon = f"app:{app_target}"
                        self._set_pixmap_icon_display(pix)
                        return

    def _toggle_advanced(self) -> None:
        is_visible = self.adv_body.isVisible()
        self.adv_body.setVisible(not is_visible)
        if not is_visible:
            self.adv_toggle_btn.setText("⚙  Advanced                                     ⌄")
        else:
            self.adv_toggle_btn.setText("⚙  Advanced                                     ›")

    def _on_search_changed(self, text: str) -> None:
        self.refresh_actions_list()

    # -----------------------------------------------------------------
    # Action Sequence Workflow Handlers
    # -----------------------------------------------------------------
    def _on_batch_add_apps(self) -> None:
        dlg = AppPickerDialog(current_mode_name=self.name_input.text(), parent=self)
        if dlg.exec() == AppPickerDialog.Accepted:
            new_actions = dlg.get_action_configs()
            self.actions_list.extend(new_actions)
            self._auto_detect_app_icon()
            self.refresh_actions_list()

    def _on_add_action(self) -> None:
        dlg = ActionEditorDialog(parent=self)
        if dlg.exec() == ActionEditorDialog.Accepted:
            cfg = dlg.get_action_config()
            self.actions_list.append(cfg)
            self._auto_detect_app_icon()
            self.refresh_actions_list()

    def _on_edit_action(self, idx: int) -> None:
        if 0 <= idx < len(self.actions_list):
            dlg = ActionEditorDialog(action_config=self.actions_list[idx], parent=self)
            if dlg.exec() == ActionEditorDialog.Accepted:
                self.actions_list[idx] = dlg.get_action_config()
                self._auto_detect_app_icon()
                self.refresh_actions_list()

    def _on_move_up(self, idx: int) -> None:
        if idx > 0:
            self.actions_list[idx], self.actions_list[idx - 1] = self.actions_list[idx - 1], self.actions_list[idx]
            self.refresh_actions_list()

    def _on_move_down(self, idx: int) -> None:
        if idx < len(self.actions_list) - 1:
            self.actions_list[idx], self.actions_list[idx + 1] = self.actions_list[idx + 1], self.actions_list[idx]
            self.refresh_actions_list()

    def _on_duplicate_action(self, idx: int) -> None:
        if 0 <= idx < len(self.actions_list):
            dup = ActionConfig.model_validate(self.actions_list[idx].model_dump())
            self.actions_list.insert(idx + 1, dup)
            self.refresh_actions_list()

    def _on_delete_action(self, idx: int) -> None:
        if 0 <= idx < len(self.actions_list):
            del self.actions_list[idx]
            self.refresh_actions_list()

    # -----------------------------------------------------------------
    # Primary CTA Handlers: Save, Test, Export, Delete
    # -----------------------------------------------------------------
    def _on_save_clicked(self) -> None:
        mode_id = self.id_input.text().strip()
        name = self.name_input.text().strip()

        if not mode_id and not self.current_mode_id:
            mode_id = name.lower().replace(" ", "_").replace("-", "_")
            mode_id = "".join(c for c in mode_id if c.isalnum() or c == "_")

        if not mode_id:
            mode_id = self.current_mode_id or ""

        if not mode_id or not name:
            QMessageBox.warning(self, "Validation Error", "Display Name is required to save the Mode.")
            return

        # Auto-resolve app icon if not explicitly set to a custom symbol
        icon_to_save = self.current_icon or "</>"
        if icon_to_save in ("</>", "⚡") or not icon_to_save:
            for act in self.actions_list:
                if act.type == "process.launch" and act.params.get("application"):
                    icon_to_save = f"app:{act.params.get('application')}"
                    break

        mode = Mode(
            schema_version=1,
            id=mode_id,
            name=name,
            description=self.desc_input.text().strip(),
            icon=icon_to_save,
            hotkey=self.hotkey_widget.text() or None,
            enabled=True,
            actions=self.actions_list,
        )

        self.st_updated.setText(f"Last updated: Today, {datetime.now().strftime('%I:%M %p')}")
        self.save_requested.emit(mode)

    def _on_test_clicked(self) -> None:
        if self.current_mode_id:
            self.test_requested.emit(self.current_mode_id)
        else:
            QMessageBox.information(
                self, "Save Mode First", "Please save this new Mode before executing a live test run."
            )

    def _on_export_clicked(self) -> None:
        if self.current_mode_id:
            self.export_requested.emit(self.current_mode_id)
        else:
            QMessageBox.information(self, "Save Required", "Save the mode before exporting.")

    def _on_delete_clicked(self) -> None:
        if self.current_mode_id:
            res = QMessageBox.question(
                self,
                "Confirm Delete",
                f"Are you sure you want to delete mode '{self.name_input.text()}'?",
                QMessageBox.Yes | QMessageBox.No,
            )
            if res == QMessageBox.Yes:
                self.delete_requested.emit(self.current_mode_id)
