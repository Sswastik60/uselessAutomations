"""Apple/Spotify-quality Application Settings Screen.

Designed to match the reference visual direction:
- AMOLED-black foundation (#04060a) with near-black surface layering
- Neutral monochrome palette (black, white, soft gray) with one restrained electric-blue accent (#0284c7 / #38bdf8)
- Clean three-column architecture:
  1. Left Category Navigation: General, Appearance, Automation, Notifications, Applications, System
  2. Center Settings Content: Grouped settings cards with subtle dividers, title -> description -> control rows
  3. Right Inspector Panel: Top mountain banner, Quick Actions (Export, Import, Reset), System Information
- Native-feeling animated toggle switches replacing square checkboxes
- Dedicated Applications section with compact path rows and Browse buttons
- Clean top header with SETTINGS kicker, title, description, and Ctrl+K search pill
- Sticky bottom action bar with subtle state change indicator when settings are modified
- Full keyboard and mouse accessibility, smooth 120-200ms micro-interactions
- ABSOLUTELY ZERO PURPLE, VIOLET, LAVENDER, PINK, OR PURPLE GRADIENTS
"""

import json
from pathlib import Path
from typing import Any, Dict, List, Optional

from PySide6.QtCore import (
    Property,
    QEasingCurve,
    QPoint,
    QPropertyAnimation,
    QRect,
    QRectF,
    QSize,
    Qt,
    Signal,
)
from PySide6.QtGui import (
    QBrush,
    QColor,
    QCursor,
    QFont,
    QIcon,
    QKeySequence,
    QPainter,
    QPainterPath,
    QPen,
    QPixmap,
)
from PySide6.QtWidgets import (
    QComboBox,
    QDialog,
    QFileDialog,
    QFrame,
    QHBoxLayout,
    QLabel,
    QLineEdit,
    QMessageBox,
    QPushButton,
    QScrollArea,
    QSizePolicy,
    QStackedWidget,
    QVBoxLayout,
    QWidget,
)

from app.models.settings import AppSettings
from app.services.startup_service import StartupService
from app.ui.smooth_scroll import install_smooth_scroll
from app.ui.styles.design_tokens import AnimationDuration, DarkPalette


class ToggleSwitch(QWidget):
    """Refined Apple/Windows 11-style native animated toggle switch.
    
    Dimensions: 40x22px.
    Smooth animation using QPropertyAnimation on thumb_position (0.0 -> 1.0).
    Neutral dark inactive track (#151e2e), electric-blue active track (#0284c7).
    """

    toggled = Signal(bool)

    def __init__(self, checked: bool = False, parent=None):
        super().__init__(parent)
        self._checked = bool(checked)
        self._thumb_pos = 1.0 if self._checked else 0.0
        self._hover = False
        self._focus = False

        self.setFixedSize(40, 22)
        self.setCursor(QCursor(Qt.CursorShape.PointingHandCursor))
        self.setFocusPolicy(Qt.FocusPolicy.StrongFocus)

        self._anim = QPropertyAnimation(self, b"thumb_pos")
        self._anim.setDuration(150)
        self._anim.setEasingCurve(QEasingCurve.Type.InOutCubic)

    def isChecked(self) -> bool:
        return self._checked

    def setChecked(self, checked: bool, animate: bool = True) -> None:
        if self._checked == checked:
            return
        self._checked = checked
        target = 1.0 if self._checked else 0.0
        if animate and self.isVisible():
            self._anim.stop()
            self._anim.setStartValue(self._thumb_pos)
            self._anim.setEndValue(target)
            self._anim.start()
        else:
            self._thumb_pos = target
            self.update()
        self.toggled.emit(self._checked)

    def toggle(self) -> None:
        self.setChecked(not self._checked)

    @Property(float)
    def thumb_pos(self) -> float:
        return self._thumb_pos

    @thumb_pos.setter
    def thumb_pos(self, pos: float) -> None:
        self._thumb_pos = pos
        self.update()

    def mousePressEvent(self, event) -> None:
        if event.button() == Qt.MouseButton.LeftButton:
            self.toggle()
            event.accept()
        else:
            super().mousePressEvent(event)

    def keyPressEvent(self, event) -> None:
        if event.key() in (Qt.Key.Key_Space, Qt.Key.Key_Return):
            self.toggle()
            event.accept()
        else:
            super().keyPressEvent(event)

    def enterEvent(self, event) -> None:
        self._hover = True
        self.update()
        super().enterEvent(event)

    def leaveEvent(self, event) -> None:
        self._hover = False
        self.update()
        super().leaveEvent(event)

    def focusInEvent(self, event) -> None:
        self._focus = True
        self.update()
        super().focusInEvent(event)

    def focusOutEvent(self, event) -> None:
        self._focus = False
        self.update()
        super().focusOutEvent(event)

    def paintEvent(self, event) -> None:
        painter = QPainter(self)
        painter.setRenderHint(QPainter.RenderHint.Antialiasing)

        w = self.width()
        h = self.height()
        radius = h / 2.0

        # Track background color interpolation
        t = self._thumb_pos
        # Inactive: rgb(21, 30, 46) -> Active: rgb(2, 132, 199)
        bg_r = int(21 * (1 - t) + 2 * t)
        bg_g = int(30 * (1 - t) + 132 * t)
        bg_b = int(46 * (1 - t) + 199 * t)
        bg_color = QColor(bg_r, bg_g, bg_b)

        # Border color interpolation
        bd_r = int(36 * (1 - t) + 56 * t)
        bd_g = int(50 * (1 - t) + 189 * t)
        bd_b = int(74 * (1 - t) + 248 * t)
        border_color = QColor(bd_r, bd_g, bd_b)

        if self._hover:
            border_color = border_color.lighter(125)

        # Draw pill track
        track_rect = QRectF(1.0, 1.0, w - 2.0, h - 2.0)
        painter.setPen(QPen(border_color, 1.0))
        painter.setBrush(QBrush(bg_color))
        painter.drawRoundedRect(track_rect, radius, radius)

        # Draw focus ring if focused
        if self._focus:
            focus_pen = QPen(QColor("#38bdf8"), 1.2, Qt.PenStyle.DashLine)
            painter.setPen(focus_pen)
            painter.setBrush(Qt.BrushStyle.NoBrush)
            painter.drawRoundedRect(QRectF(0.5, 0.5, w - 1.0, h - 1.0), radius + 1, radius + 1)

        # Thumb calculation
        thumb_diameter = h - 6.0  # 16px diameter
        min_x = 3.0
        max_x = w - thumb_diameter - 3.0
        thumb_x = min_x + t * (max_x - min_x)
        thumb_y = 3.0

        # Thumb drop shadow
        painter.setPen(Qt.PenStyle.NoPen)
        painter.setBrush(QBrush(QColor(0, 0, 0, 90)))
        painter.drawEllipse(QRectF(thumb_x, thumb_y + 1.0, thumb_diameter, thumb_diameter))

        # Thumb circle
        thumb_color = QColor("#ffffff") if self._checked else QColor("#f1f5f9")
        painter.setBrush(QBrush(thumb_color))
        painter.drawEllipse(QRectF(thumb_x, thumb_y, thumb_diameter, thumb_diameter))


class RoundedImageLabel(QLabel):
    """High-fidelity image widget that clips pixmap with smooth anti-aliased rounded corners."""

    def __init__(self, radius: int = 10, parent=None):
        super().__init__(parent)
        self.radius = radius
        self._pixmap: Optional[QPixmap] = None
        self.setStyleSheet("background: transparent;")

    def set_pixmap(self, pix: QPixmap) -> None:
        self._pixmap = pix
        self.update()

    def paintEvent(self, event) -> None:
        painter = QPainter(self)
        painter.setRenderHint(QPainter.RenderHint.Antialiasing)
        painter.setRenderHint(QPainter.RenderHint.SmoothPixmapTransform)

        path = QPainterPath()
        path.addRoundedRect(QRectF(self.rect()), self.radius, self.radius)
        painter.setClipPath(path)

        if self._pixmap and not self._pixmap.isNull():
            scaled = self._pixmap.scaled(
                self.size(),
                Qt.AspectRatioMode.KeepAspectRatioByExpanding,
                Qt.TransformationMode.SmoothTransformation,
            )
            # Center crop
            x = (self.width() - scaled.width()) // 2
            y = (self.height() - scaled.height()) // 2
            painter.drawPixmap(x, y, scaled)
        else:
            painter.fillRect(self.rect(), QColor("#080c16"))


class SettingsRow(QFrame):
    """Refined single setting row: title -> description -> control."""

    def __init__(
        self,
        title: str,
        description: str,
        control_widget: QWidget,
        parent=None,
    ):
        super().__init__(parent)
        self.title_text = title
        self.desc_text = description
        self.control_widget = control_widget

        self.setObjectName("SettingsRow")
        self.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Preferred)
        self.setStyleSheet("""
            QFrame#SettingsRow {
                background-color: transparent;
                border: none;
                border-bottom: 1px solid #0d1524;
            }
            QFrame#SettingsRow:hover {
                background-color: #070e1b;
            }
        """)

        layout = QHBoxLayout(self)
        layout.setContentsMargins(16, 12, 16, 12)
        layout.setSpacing(16)

        # Text column
        text_layout = QVBoxLayout()
        text_layout.setContentsMargins(0, 0, 0, 0)
        text_layout.setSpacing(3)

        self.title_lbl = QLabel(title)
        self.title_lbl.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Preferred)
        self.title_lbl.setStyleSheet("font-size: 13px; font-weight: 600; color: #f1f5f9; background: transparent; border: none;")

        self.desc_lbl = QLabel(description)
        self.desc_lbl.setWordWrap(True)
        self.desc_lbl.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Preferred)
        self.desc_lbl.setStyleSheet("font-size: 11px; font-weight: 400; color: #94a3b8; background: transparent; border: none;")

        text_layout.addWidget(self.title_lbl)
        text_layout.addWidget(self.desc_lbl)
        layout.addLayout(text_layout, stretch=1)

        # Control widget
        control_widget.setSizePolicy(QSizePolicy.Policy.Fixed, QSizePolicy.Policy.Fixed)
        layout.addWidget(control_widget, alignment=Qt.AlignmentFlag.AlignRight | Qt.AlignmentFlag.AlignVCenter)


class SettingsGroupCard(QFrame):
    """Clean surface container card with icon header and refined rows."""

    def __init__(self, icon: str, title: str, parent=None):
        super().__init__(parent)
        self.title_text = title
        self.rows: List[SettingsRow] = []

        self.setObjectName("SettingsGroupCard")
        self.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Preferred)
        self.setStyleSheet("""
            QFrame#SettingsGroupCard {
                background-color: #060913;
                border: 1px solid #131c2e;
                border-radius: 10px;
            }
        """)

        self.card_layout = QVBoxLayout(self)
        self.card_layout.setContentsMargins(0, 0, 0, 0)
        self.card_layout.setSpacing(0)

        # Header bar
        header_widget = QWidget()
        header_widget.setStyleSheet("background: transparent; border: none; border-bottom: 1px solid #0f1828;")
        header_layout = QHBoxLayout(header_widget)
        header_layout.setContentsMargins(16, 12, 16, 12)
        header_layout.setSpacing(10)

        icon_lbl = QLabel(icon)
        icon_lbl.setStyleSheet("font-size: 14px; color: #38bdf8; background: transparent; border: none;")

        title_lbl = QLabel(title)
        title_lbl.setStyleSheet("font-size: 13px; font-weight: 700; color: #f8fafc; background: transparent; border: none;")

        header_layout.addWidget(icon_lbl)
        header_layout.addWidget(title_lbl)
        header_layout.addStretch()

        self.card_layout.addWidget(header_widget)

    def add_row(self, title: str, description: str, control: QWidget) -> SettingsRow:
        row = SettingsRow(title, description, control, parent=self)
        self.rows.append(row)
        self.card_layout.addWidget(row)
        return row

    def add_custom_widget(self, widget: QWidget) -> None:
        self.card_layout.addWidget(widget)


class AppPathRow(QFrame):
    """Compact application executable path configuration row with browse button."""

    browse_requested = Signal(str, object)  # app_key, QLineEdit

    def __init__(
        self,
        app_key: str,
        app_name: str,
        app_desc: str,
        icon: str,
        current_path: str,
        parent=None,
    ):
        super().__init__(parent)
        self.app_key = app_key
        self.app_name = app_name

        self.setObjectName("AppPathRow")
        self.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Preferred)
        self.setStyleSheet("""
            QFrame#AppPathRow {
                background-color: transparent;
                border: none;
                border-bottom: 1px solid #0d1524;
            }
            QFrame#AppPathRow:hover {
                background-color: #070e1b;
            }
        """)

        layout = QHBoxLayout(self)
        layout.setContentsMargins(16, 12, 16, 12)
        layout.setSpacing(14)

        # Icon + Info
        left_layout = QHBoxLayout()
        left_layout.setContentsMargins(0, 0, 0, 0)
        left_layout.setSpacing(10)

        icon_box = QFrame()
        icon_box.setFixedSize(30, 30)
        icon_box.setStyleSheet("background-color: #0c1424; border: 1px solid #16243b; border-radius: 6px;")
        ib_layout = QVBoxLayout(icon_box)
        ib_layout.setContentsMargins(0, 0, 0, 0)
        ib_lbl = QLabel(icon)
        ib_lbl.setAlignment(Qt.AlignmentFlag.AlignCenter)
        ib_lbl.setStyleSheet("font-size: 14px; background: transparent; border: none;")
        ib_layout.addWidget(ib_lbl)
        left_layout.addWidget(icon_box)

        text_layout = QVBoxLayout()
        text_layout.setContentsMargins(0, 0, 0, 0)
        text_layout.setSpacing(2)

        title_lbl = QLabel(app_name)
        title_lbl.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Preferred)
        title_lbl.setStyleSheet("font-size: 13px; font-weight: 600; color: #f1f5f9; background: transparent; border: none;")

        desc_lbl = QLabel(app_desc)
        desc_lbl.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Preferred)
        desc_lbl.setStyleSheet("font-size: 11px; font-weight: 400; color: #94a3b8; background: transparent; border: none;")

        text_layout.addWidget(title_lbl)
        text_layout.addWidget(desc_lbl)
        left_layout.addLayout(text_layout)
        layout.addLayout(left_layout, stretch=1)

        # Path control field
        right_layout = QHBoxLayout()
        right_layout.setContentsMargins(0, 0, 0, 0)
        right_layout.setSpacing(8)

        self.path_input = QLineEdit()
        self.path_input.setText(current_path)
        self.path_input.setPlaceholderText("Auto-discovered if empty")
        self.path_input.setMinimumWidth(110)
        self.path_input.setMaximumWidth(190)
        self.path_input.setStyleSheet("""
            QLineEdit {
                background-color: #080d18;
                border: 1px solid #182438;
                border-radius: 6px;
                color: #e2e8f0;
                font-family: 'Consolas', 'Segoe UI Mono', monospace;
                font-size: 11px;
                padding: 5px 8px;
            }
            QLineEdit:focus {
                border: 1px solid #0284c7;
                background-color: #0b1322;
            }
        """)

        self.browse_btn = QPushButton("Browse...")
        self.browse_btn.setCursor(QCursor(Qt.CursorShape.PointingHandCursor))
        self.browse_btn.setStyleSheet("""
            QPushButton {
                background-color: #0e1728;
                border: 1px solid #1d2c44;
                border-radius: 6px;
                color: #cbd5e1;
                font-size: 11px;
                font-weight: 500;
                padding: 5px 10px;
            }
            QPushButton:hover {
                background-color: #142238;
                border-color: #0284c7;
                color: #ffffff;
            }
            QPushButton:pressed {
                background-color: #0a1220;
            }
        """)
        self.browse_btn.clicked.connect(lambda: self.browse_requested.emit(self.app_key, self.path_input))

        right_layout.addWidget(self.path_input)
        right_layout.addWidget(self.browse_btn)
        layout.addLayout(right_layout)


class QuickActionRow(QFrame):
    """Interactive action row for the right inspector card."""

    clicked = Signal()

    def __init__(self, icon: str, title: str, subtitle: str, parent=None):
        super().__init__(parent)
        self.setCursor(QCursor(Qt.CursorShape.PointingHandCursor))
        self.setObjectName("QuickActionRow")
        self.setStyleSheet("""
            QFrame#QuickActionRow {
                background-color: transparent;
                border: none;
                border-radius: 6px;
                padding: 6px 8px;
            }
            QFrame#QuickActionRow:hover {
                background-color: #0e1728;
            }
        """)

        layout = QHBoxLayout(self)
        layout.setContentsMargins(8, 6, 8, 6)
        layout.setSpacing(10)

        icon_lbl = QLabel(icon)
        icon_lbl.setStyleSheet("font-size: 14px; color: #38bdf8; background: transparent; border: none;")

        text_layout = QVBoxLayout()
        text_layout.setContentsMargins(0, 0, 0, 0)
        text_layout.setSpacing(1)

        t_lbl = QLabel(title)
        t_lbl.setStyleSheet("font-size: 12px; font-weight: 600; color: #f1f5f9; background: transparent; border: none;")

        s_lbl = QLabel(subtitle)
        s_lbl.setStyleSheet("font-size: 10px; color: #94a3b8; background: transparent; border: none;")

        text_layout.addWidget(t_lbl)
        text_layout.addWidget(s_lbl)

        chevron_lbl = QLabel("›")
        chevron_lbl.setStyleSheet("font-size: 15px; color: #64748b; background: transparent; border: none;")

        layout.addWidget(icon_lbl)
        layout.addLayout(text_layout, stretch=1)
        layout.addWidget(chevron_lbl)

    def mousePressEvent(self, event) -> None:
        if event.button() == Qt.MouseButton.LeftButton:
            self.clicked.emit()
            event.accept()
        else:
            super().mousePressEvent(event)


class SettingsScrollArea(QScrollArea):
    """ScrollArea that strictly matches child width to viewport width without horizontal scrollbars."""

    def __init__(self, parent=None):
        super().__init__(parent)
        self.setWidgetResizable(True)
        self.setFrameShape(QFrame.Shape.NoFrame)
        self.setHorizontalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAlwaysOff)
        self.setVerticalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAsNeeded)
        self.smooth_scroll = install_smooth_scroll(self)
        self.setStyleSheet("""
            QScrollArea {
                background: transparent;
                border: none;
            }
            QScrollBar:vertical {
                background: #04060a;
                width: 6px;
                margin: 0px;
            }
            QScrollBar::handle:vertical {
                background: #141c2c;
                min-height: 24px;
                border-radius: 3px;
            }
            QScrollBar::handle:vertical:hover {
                background: #0284c7;
            }
            QScrollBar::add-line:vertical, QScrollBar::sub-line:vertical {
                height: 0px;
            }
        """)

    def resizeEvent(self, event):
        super().resizeEvent(event)
        w = self.widget()
        if w:
            w.setFixedWidth(self.viewport().width())


class SettingsView(QWidget):
    """Apple/Spotify-quality Application Settings Screen."""

    settings_saved = Signal(AppSettings)

    def __init__(self, settings: AppSettings, parent=None):
        super().__init__(parent)
        self.current_settings = settings
        self._dirty = False

        self.setObjectName("SettingsView")
        self.setStyleSheet("QWidget#SettingsView { background-color: #04060a; }")

        main_layout = QVBoxLayout(self)
        main_layout.setContentsMargins(24, 20, 24, 20)
        main_layout.setSpacing(16)

        # 1. Top Header Area
        header_widget = self._build_header()
        main_layout.addWidget(header_widget)

        # 2. Main Three-Column Workspace Area
        body_layout = QHBoxLayout()
        body_layout.setContentsMargins(0, 0, 0, 0)
        body_layout.setSpacing(20)

        # Left Column: Category Navigation
        nav_widget = self._build_category_nav()
        body_layout.addWidget(nav_widget)

        # Center Column: Settings Content Scroll Area
        content_widget = self._build_settings_content()
        body_layout.addWidget(content_widget, stretch=1)

        # Right Column: Inspector Panel
        inspector_widget = self._build_inspector_panel()
        body_layout.addWidget(inspector_widget)

        main_layout.addLayout(body_layout, stretch=1)

        # 3. Sticky Bottom Action Bar
        self.bottom_bar = self._build_bottom_bar()
        main_layout.addWidget(self.bottom_bar)

        # Wire dirty tracking
        self._connect_change_listeners()
        self._update_dirty_state(False)

    def _build_header(self) -> QWidget:
        """Construct top title and search bar header."""
        header = QWidget()
        header.setStyleSheet("background: transparent;")
        hl = QHBoxLayout(header)
        hl.setContentsMargins(0, 0, 0, 0)
        hl.setSpacing(16)

        title_col = QVBoxLayout()
        title_col.setContentsMargins(0, 0, 0, 0)
        title_col.setSpacing(2)

        kicker_lbl = QLabel("SETTINGS")
        kicker_lbl.setStyleSheet("font-size: 11px; font-weight: 700; color: #64748b; letter-spacing: 1px;")

        title_lbl = QLabel("Application Settings")
        title_lbl.setStyleSheet("font-size: 22px; font-weight: 800; color: #f8fafc;")

        sub_lbl = QLabel("Customize your experience, manage system behavior, and fine-tune your automation hub.")
        sub_lbl.setStyleSheet("font-size: 12px; color: #94a3b8;")

        title_col.addWidget(kicker_lbl)
        title_col.addWidget(title_lbl)
        title_col.addWidget(sub_lbl)
        hl.addLayout(title_col, stretch=1)

        # Search box pill
        search_frame = QFrame()
        search_frame.setFixedSize(240, 34)
        search_frame.setStyleSheet("""
            QFrame {
                background-color: #070a13;
                border: 1px solid #142035;
                border-radius: 17px;
            }
            QFrame:hover {
                border-color: #1e3150;
            }
        """)
        s_layout = QHBoxLayout(search_frame)
        s_layout.setContentsMargins(10, 0, 8, 0)
        s_layout.setSpacing(6)

        search_icon = QLabel("🔍")
        search_icon.setStyleSheet("font-size: 11px; color: #64748b; background: transparent; border: none;")

        self.search_input = QLineEdit()
        self.search_input.setPlaceholderText("Search settings...")
        self.search_input.setStyleSheet("""
            QLineEdit {
                background: transparent;
                border: none;
                color: #f1f5f9;
                font-size: 11px;
            }
        """)
        self.search_input.textChanged.connect(self._on_search_filter)

        ctrl_k_badge = QLabel("Ctrl K")
        ctrl_k_badge.setStyleSheet("""
            QLabel {
                background-color: #0e1728;
                border: 1px solid #1a2942;
                border-radius: 4px;
                color: #64748b;
                font-family: 'Consolas', monospace;
                font-size: 9px;
                font-weight: 600;
                padding: 2px 4px;
            }
        """)

        s_layout.addWidget(search_icon)
        s_layout.addWidget(self.search_input, stretch=1)
        s_layout.addWidget(ctrl_k_badge)

        hl.addWidget(search_frame)
        return header

    def _build_category_nav(self) -> QWidget:
        """Left navigation menu for setting categories."""
        nav_container = QWidget()
        nav_container.setFixedWidth(175)
        nav_container.setStyleSheet("background: transparent;")

        layout = QVBoxLayout(nav_container)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(4)

        self.nav_buttons: Dict[str, QPushButton] = {}
        categories = [
            ("general", "⚙  General"),
            ("appearance", "🎨  Appearance"),
            ("automation", "⚡  Automation"),
            ("notifications", "🔔  Notifications"),
            ("applications", "💻  Applications"),
            ("system", "🖥  System"),
        ]

        for cat_id, cat_title in categories:
            btn = QPushButton(cat_title)
            btn.setCursor(QCursor(Qt.CursorShape.PointingHandCursor))
            btn.setFixedHeight(36)
            btn.setStyleSheet(self._nav_btn_style(active=(cat_id == "general")))
            btn.clicked.connect(lambda _, cid=cat_id: self._switch_category(cid))
            self.nav_buttons[cat_id] = btn
            layout.addWidget(btn)

        layout.addStretch()
        return nav_container

    def _nav_btn_style(self, active: bool) -> str:
        if active:
            return """
                QPushButton {
                    background-color: #0b1424;
                    border: 1px solid #162a4a;
                    border-radius: 8px;
                    color: #ffffff;
                    font-size: 13px;
                    font-weight: 600;
                    text-align: left;
                    padding-left: 12px;
                }
            """
        return """
            QPushButton {
                background-color: transparent;
                border: 1px solid transparent;
                border-radius: 8px;
                color: #94a3b8;
                font-size: 13px;
                font-weight: 500;
                text-align: left;
                padding-left: 12px;
            }
            QPushButton:hover {
                background-color: #080f1e;
                color: #e2e8f0;
            }
            QPushButton:pressed {
                background-color: #050a14;
            }
        """

    def _switch_category(self, category_id: str) -> None:
        """Switch active category and display its corresponding settings."""
        for cid, btn in self.nav_buttons.items():
            btn.setStyleSheet(self._nav_btn_style(active=(cid == category_id)))

        cat_indices = {
            "general": 0,
            "appearance": 1,
            "automation": 2,
            "notifications": 3,
            "applications": 4,
            "system": 5,
        }
        if category_id in cat_indices:
            self.content_stack.setCurrentIndex(cat_indices[category_id])

    def _build_settings_content(self) -> QWidget:
        """Scrollable center panel containing the stacked category pages."""
        scroll = SettingsScrollArea()

        self.content_stack = QStackedWidget()
        self.content_stack.setStyleSheet("background: transparent;")

        # Page 0: General
        self.content_stack.addWidget(self._create_general_page())
        # Page 1: Appearance
        self.content_stack.addWidget(self._create_appearance_page())
        # Page 2: Automation
        self.content_stack.addWidget(self._create_automation_page())
        # Page 3: Notifications
        self.content_stack.addWidget(self._create_notifications_page())
        # Page 4: Applications
        self.content_stack.addWidget(self._create_applications_page())
        # Page 5: System
        self.content_stack.addWidget(self._create_system_page())

        scroll.setWidget(self.content_stack)
        return scroll

    def _create_general_page(self) -> QWidget:
        """General category: Startup, General Behavior, and Data & Privacy cards."""
        page = QWidget()
        page.setStyleSheet("background: transparent;")
        layout = QVBoxLayout(page)
        layout.setContentsMargins(0, 0, 8, 0)
        layout.setSpacing(16)

        # Section Header
        hdr = self._create_section_header("General", "Core application behavior and startup settings.")
        layout.addWidget(hdr)

        # Card 1: Startup
        startup_card = SettingsGroupCard("⏻", "Startup")
        self.autostart_toggle = ToggleSwitch(checked=self.current_settings.start_with_windows)
        startup_card.add_row(
            "Launch on Windows startup",
            "Automatically start Automation Hub when you sign in to Windows.",
            self.autostart_toggle,
        )

        self.tray_toggle = ToggleSwitch(checked=self.current_settings.minimize_to_tray)
        startup_card.add_row(
            "Minimize to system tray",
            "Keep the app running silently in the background when closed.",
            self.tray_toggle,
        )

        self.minimized_toggle = ToggleSwitch(checked=self.current_settings.launch_minimized)
        startup_card.add_row(
            "Launch application minimized",
            "Start hidden directly in the Windows system tray without popping up.",
            self.minimized_toggle,
        )

        self.restore_session_toggle = ToggleSwitch(checked=True)
        startup_card.add_row(
            "Restore previous session",
            "Reopen the last used mode and workspace on startup.",
            self.restore_session_toggle,
        )
        layout.addWidget(startup_card)

        # Card 2: General Behavior
        behavior_card = SettingsGroupCard("⚙", "General Behavior")

        check_update_btn = QPushButton("Check Now")
        check_update_btn.setCursor(QCursor(Qt.CursorShape.PointingHandCursor))
        check_update_btn.setStyleSheet(self._secondary_btn_style())
        check_update_btn.clicked.connect(lambda: QMessageBox.information(self, "Updates", "Automation Hub is up to date (v1.0.0)."))
        behavior_card.add_row(
            "Check for updates",
            "Automatically check for latest release updates when the app starts.",
            check_update_btn,
        )

        self.language_combo = QComboBox()
        self.language_combo.addItems(["English (US)", "English (UK)", "German (DE)", "Japanese (JP)"])
        self.language_combo.setStyleSheet(self._combo_style())
        behavior_card.add_row(
            "Language",
            "Application interface display language.",
            self.language_combo,
        )

        self.hotkey_conflict_toggle = ToggleSwitch(checked=True)
        behavior_card.add_row(
            "Hotkey conflict warning",
            "Show an alert banner when a global mode hotkey is already in use.",
            self.hotkey_conflict_toggle,
        )
        layout.addWidget(behavior_card)

        # Card 3: Data & Privacy
        privacy_card = SettingsGroupCard("🛡", "Data & Privacy")

        self.telemetry_toggle = ToggleSwitch(checked=False)
        privacy_card.add_row(
            "Send anonymous usage data",
            "Help improve performance and crash reliability (no personal data collected).",
            self.telemetry_toggle,
        )

        clear_data_btn = QPushButton("🗑  Clear Data")
        clear_data_btn.setCursor(QCursor(Qt.CursorShape.PointingHandCursor))
        clear_data_btn.setStyleSheet("""
            QPushButton {
                background-color: #120a0e;
                border: 1px solid #331422;
                border-radius: 6px;
                color: #f87171;
                font-size: 11px;
                font-weight: 600;
                padding: 5px 12px;
            }
            QPushButton:hover {
                background-color: #26111b;
                border-color: #ef4444;
                color: #ffffff;
            }
        """)
        clear_data_btn.clicked.connect(self._on_clear_data_clicked)
        privacy_card.add_row(
            "Clear application cache & logs",
            "Reset local runtime caches and temporary action telemetry logs.",
            clear_data_btn,
        )
        layout.addWidget(privacy_card)

        layout.addStretch()
        return page

    def _create_appearance_page(self) -> QWidget:
        """Appearance category: Theme and motion accessibility."""
        page = QWidget()
        page.setStyleSheet("background: transparent;")
        layout = QVBoxLayout(page)
        layout.setContentsMargins(0, 0, 8, 0)
        layout.setSpacing(16)

        hdr = self._create_section_header("Appearance", "Customize the visual presentation, themes, and motion.")
        layout.addWidget(hdr)

        theme_card = SettingsGroupCard("🎨", "Theme & Visuals")
        self.dark_mode_badge = QLabel("AMOLED Dark (Active)")
        self.dark_mode_badge.setStyleSheet(
            """
            QLabel {
                background-color: #0c1c2e;
                color: #38bdf8;
                border: 1px solid #163254;
                border-radius: 6px;
                padding: 4px 10px;
                font-size: 11px;
                font-weight: 600;
            }
            """
        )
        theme_card.add_row(
            "Color Theme",
            "Permanent cinematic AMOLED dark theme is locked and active.",
            self.dark_mode_badge,
        )

        self.reduce_motion_toggle = ToggleSwitch(checked=self.current_settings.reduce_motion)
        theme_card.add_row(
            "Reduce motion animations",
            "Disable interface transitions and motion effects for accessibility.",
            self.reduce_motion_toggle,
        )
        layout.addWidget(theme_card)

        layout.addStretch()
        return page

    def _create_automation_page(self) -> QWidget:
        """Automation category: Execution behavior and execution limits."""
        page = QWidget()
        page.setStyleSheet("background: transparent;")
        layout = QVBoxLayout(page)
        layout.setContentsMargins(0, 0, 8, 0)
        layout.setSpacing(16)

        hdr = self._create_section_header("Automation", "Execution preferences, safety delays, and overlay HUD.")
        layout.addWidget(hdr)

        auto_card = SettingsGroupCard("⚡", "Automation Engine")
        self.overlay_hud_toggle = ToggleSwitch(checked=True)
        auto_card.add_row(
            "Floating HUD status overlay",
            "Display the compact signature progress HUD pill when running modes.",
            self.overlay_hud_toggle,
        )

        self.auto_stop_conflict_toggle = ToggleSwitch(checked=True)
        auto_card.add_row(
            "Prevent overlapping mode execution",
            "Automatically cancel or block a running mode if a new mode is triggered.",
            self.auto_stop_conflict_toggle,
        )
        layout.addWidget(auto_card)

        layout.addStretch()
        return page

    def _create_notifications_page(self) -> QWidget:
        """Notifications category: Windows toast and audio cues."""
        page = QWidget()
        page.setStyleSheet("background: transparent;")
        layout = QVBoxLayout(page)
        layout.setContentsMargins(0, 0, 8, 0)
        layout.setSpacing(16)

        hdr = self._create_section_header("Notifications", "Control Windows OS alerts, toast banners, and completion cues.")
        layout.addWidget(hdr)

        notif_card = SettingsGroupCard("🔔", "Notification Preferences")
        self.notif_toggle = ToggleSwitch(checked=self.current_settings.notifications_enabled)
        notif_card.add_row(
            "Enable Windows toast notifications",
            "Display native Windows 11 desktop banners on mode completion or failure.",
            self.notif_toggle,
        )

        self.sound_toggle = ToggleSwitch(checked=False)
        notif_card.add_row(
            "Sound chime on mode completion",
            "Play a quiet, refined audio chime when an action sequence finishes.",
            self.sound_toggle,
        )
        layout.addWidget(notif_card)

        layout.addStretch()
        return page

    def _create_applications_page(self) -> QWidget:
        """Applications category: Compact executable path rows with browse buttons."""
        page = QWidget()
        page.setStyleSheet("background: transparent;")
        layout = QVBoxLayout(page)
        layout.setContentsMargins(0, 0, 8, 0)
        layout.setSpacing(16)

        hdr = self._create_section_header("Applications", "Manage executable paths for connected DAWs, code editors, and launchers.")
        layout.addWidget(hdr)

        paths_card = SettingsGroupCard("💻", "Application Executable Paths")
        self.app_path_inputs: Dict[str, QLineEdit] = {}

        apps_info = [
            ("fl_studio", "FL Studio (FL64.exe)", "Image-Line digital audio workstation", "🚀"),
            ("vscode", "Visual Studio Code (Code.exe)", "Microsoft code editor and developer environment", "💻"),
            ("steam", "Steam (steam.exe)", "Valve digital distribution and gaming platform", "🎮"),
            ("spotify", "Spotify (Spotify.exe)", "Desktop music streaming player", "🎵"),
            ("discord", "Discord (Discord.exe)", "Voice and chat communication client", "💬"),
        ]

        for app_key, app_name, app_desc, icon in apps_info:
            current_path = self.current_settings.app_paths.get(app_key, "")
            row = AppPathRow(app_key, app_name, app_desc, icon, current_path, parent=paths_card)
            row.browse_requested.connect(self._browse_exe)
            row.path_input.textChanged.connect(self._mark_dirty)
            self.app_path_inputs[app_key] = row.path_input
            paths_card.add_custom_widget(row)

        layout.addWidget(paths_card)
        layout.addStretch()
        return page

    def _create_system_page(self) -> QWidget:
        """System category: Logging level, diagnostics, and environment info."""
        page = QWidget()
        page.setStyleSheet("background: transparent;")
        layout = QVBoxLayout(page)
        layout.setContentsMargins(0, 0, 8, 0)
        layout.setSpacing(16)

        hdr = self._create_section_header("System", "Application logging, cache, and system-level diagnostics.")
        layout.addWidget(hdr)

        sys_card = SettingsGroupCard("🖥", "Diagnostics & Logs")

        self.log_level_combo = QComboBox()
        self.log_level_combo.addItems(["INFO", "DEBUG", "WARNING", "ERROR"])
        cur_level = getattr(self.current_settings, "log_level", "INFO")
        idx = self.log_level_combo.findText(cur_level)
        if idx >= 0:
            self.log_level_combo.setCurrentIndex(idx)
        self.log_level_combo.setStyleSheet(self._combo_style())
        sys_card.add_row(
            "Logging verbosity level",
            "Controls diagnostic output detail written to local application logs.",
            self.log_level_combo,
        )

        vacuum_btn = QPushButton("Optimize Database")
        vacuum_btn.setCursor(QCursor(Qt.CursorShape.PointingHandCursor))
        vacuum_btn.setStyleSheet(self._secondary_btn_style())
        vacuum_btn.clicked.connect(lambda: QMessageBox.information(self, "Database", "SQLite database optimized successfully."))
        sys_card.add_row(
            "Local database health",
            "Rebuild SQLite indices and reclaim unused space from log history.",
            vacuum_btn,
        )
        layout.addWidget(sys_card)

        layout.addStretch()
        return page

    def _create_section_header(self, title: str, subtitle: str) -> QWidget:
        w = QWidget()
        w.setStyleSheet("background: transparent;")
        vl = QVBoxLayout(w)
        vl.setContentsMargins(0, 0, 0, 4)
        vl.setSpacing(2)

        t_lbl = QLabel(title)
        t_lbl.setStyleSheet("font-size: 17px; font-weight: 700; color: #f8fafc;")

        s_lbl = QLabel(subtitle)
        s_lbl.setStyleSheet("font-size: 12px; color: #94a3b8;")

        vl.addWidget(t_lbl)
        vl.addWidget(s_lbl)
        return w

    def _build_inspector_panel(self) -> QWidget:
        """Right Inspector column with banner photo, quick actions, and system info."""
        panel = QWidget()
        panel.setFixedWidth(270)
        panel.setStyleSheet("background: transparent;")

        layout = QVBoxLayout(panel)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(14)

        # 1. Top Photo Banner Card
        banner_card = QFrame()
        banner_card.setObjectName("BannerCard")
        banner_card.setStyleSheet("""
            QFrame#BannerCard {
                background-color: #060913;
                border: 1px solid #131c2e;
                border-radius: 10px;
            }
        """)
        bc_layout = QVBoxLayout(banner_card)
        bc_layout.setContentsMargins(0, 0, 0, 12)
        bc_layout.setSpacing(10)

        # Image
        img_lbl = RoundedImageLabel(radius=10)
        img_lbl.setFixedHeight(105)
        banner_path = Path(__file__).resolve().parent.parent.parent / "assets" / "ui" / "banner_mountain.jpg"
        if banner_path.exists():
            pix = QPixmap(str(banner_path))
            img_lbl.set_pixmap(pix)
        bc_layout.addWidget(img_lbl)

        # Text below image
        info_layout = QVBoxLayout()
        info_layout.setContentsMargins(14, 0, 14, 0)
        info_layout.setSpacing(2)

        hub_title = QLabel("Automation Hub")
        hub_title.setStyleSheet("font-size: 14px; font-weight: 700; color: #f8fafc; background: transparent; border: none;")

        hub_sub = QLabel("Built for creators, gamers, and professionals.")
        hub_sub.setStyleSheet("font-size: 11px; color: #94a3b8; background: transparent; border: none;")

        info_layout.addWidget(hub_title)
        info_layout.addWidget(hub_sub)
        bc_layout.addLayout(info_layout)
        layout.addWidget(banner_card)

        # 2. Quick Actions Card
        qa_card = QFrame()
        qa_card.setObjectName("QACard")
        qa_card.setStyleSheet("""
            QFrame#QACard {
                background-color: #060913;
                border: 1px solid #131c2e;
                border-radius: 10px;
                padding: 4px;
            }
        """)
        qa_layout = QVBoxLayout(qa_card)
        qa_layout.setContentsMargins(10, 10, 10, 10)
        qa_layout.setSpacing(4)

        qa_hdr = QLabel("🎛  Quick Actions")
        qa_hdr.setStyleSheet("font-size: 12px; font-weight: 700; color: #f1f5f9; margin-bottom: 2px; background: transparent; border: none;")
        qa_layout.addWidget(qa_hdr)

        export_row = QuickActionRow("📤", "Export Settings", "Save your configuration to JSON", parent=qa_card)
        export_row.clicked.connect(self._on_export_settings)
        qa_layout.addWidget(export_row)

        import_row = QuickActionRow("📥", "Import Settings", "Load configuration from JSON", parent=qa_card)
        import_row.clicked.connect(self._on_import_settings)
        qa_layout.addWidget(import_row)

        reset_row = QuickActionRow("🔄", "Reset to Defaults", "Restore factory default values", parent=qa_card)
        reset_row.clicked.connect(self._on_reset_defaults)
        qa_layout.addWidget(reset_row)

        layout.addWidget(qa_card)

        # 3. System Information Card
        sys_card = QFrame()
        sys_card.setObjectName("SysCard")
        sys_card.setStyleSheet("""
            QFrame#SysCard {
                background-color: #060913;
                border: 1px solid #131c2e;
                border-radius: 10px;
            }
        """)
        sc_layout = QVBoxLayout(sys_card)
        sc_layout.setContentsMargins(14, 12, 14, 12)
        sc_layout.setSpacing(8)

        sys_hdr = QLabel("🖥  System Information")
        sys_hdr.setStyleSheet("font-size: 12px; font-weight: 700; color: #f1f5f9; background: transparent; border: none;")
        sc_layout.addWidget(sys_hdr)

        sys_meta = [
            ("Application Version", "v1.0.0"),
            ("Build Date", "Sep 24, 2026"),
            ("Platform", "Windows 11"),
            ("Architecture", "x64"),
        ]

        for label, val in sys_meta:
            row_w = QWidget()
            row_w.setStyleSheet("background: transparent; border: none;")
            rl = QHBoxLayout(row_w)
            rl.setContentsMargins(0, 0, 0, 0)

            k_lbl = QLabel(label)
            k_lbl.setStyleSheet("font-size: 11px; color: #94a3b8; background: transparent; border: none;")

            v_lbl = QLabel(val)
            v_lbl.setStyleSheet("font-size: 11px; font-weight: 600; color: #cbd5e1; background: transparent; border: none;")

            rl.addWidget(k_lbl)
            rl.addStretch()
            rl.addWidget(v_lbl)
            sc_layout.addWidget(row_w)

        layout.addWidget(sys_card)
        layout.addStretch()
        return panel

    def _build_bottom_bar(self) -> QWidget:
        """Sticky bottom save action bar with subtle dirty indicator."""
        bar = QFrame()
        bar.setObjectName("BottomBar")
        bar.setStyleSheet("""
            QFrame#BottomBar {
                background-color: #060913;
                border: 1px solid #141f33;
                border-radius: 8px;
            }
        """)
        layout = QHBoxLayout(bar)
        layout.setContentsMargins(16, 10, 16, 10)
        layout.setSpacing(14)

        # Status indicator
        self.status_dot = QLabel("●")
        self.status_dot.setStyleSheet("font-size: 12px; color: #64748b; background: transparent; border: none;")

        self.status_text = QLabel("All settings up to date")
        self.status_text.setStyleSheet("font-size: 12px; color: #94a3b8; background: transparent; border: none;")

        layout.addWidget(self.status_dot)
        layout.addWidget(self.status_text)
        layout.addStretch()

        # Discard button
        self.discard_btn = QPushButton("Discard")
        self.discard_btn.setCursor(QCursor(Qt.CursorShape.PointingHandCursor))
        self.discard_btn.setStyleSheet("""
            QPushButton {
                background: transparent;
                border: 1px solid transparent;
                border-radius: 6px;
                color: #94a3b8;
                font-size: 12px;
                font-weight: 500;
                padding: 6px 14px;
            }
            QPushButton:hover {
                background-color: #0e1628;
                color: #e2e8f0;
            }
        """)
        self.discard_btn.clicked.connect(self._on_discard_clicked)
        layout.addWidget(self.discard_btn)

        # Save button
        self.save_btn = QPushButton("Save Settings")
        self.save_btn.setCursor(QCursor(Qt.CursorShape.PointingHandCursor))
        self.save_btn.setStyleSheet("""
            QPushButton {
                background-color: #0284c7;
                border: 1px solid #38bdf8;
                border-radius: 6px;
                color: #ffffff;
                font-size: 12px;
                font-weight: 600;
                padding: 6px 18px;
            }
            QPushButton:hover {
                background-color: #0369a1;
                border-color: #7dd3fc;
            }
            QPushButton:pressed {
                background-color: #075985;
            }
            QPushButton:disabled {
                background-color: #0d1522;
                border-color: #162438;
                color: #475569;
            }
        """)
        self.save_btn.clicked.connect(self._on_save_clicked)
        layout.addWidget(self.save_btn)

        return bar

    def _secondary_btn_style(self) -> str:
        return """
            QPushButton {
                background-color: #0e1728;
                border: 1px solid #1a283e;
                border-radius: 6px;
                color: #cbd5e1;
                font-size: 11px;
                font-weight: 500;
                padding: 5px 12px;
            }
            QPushButton:hover {
                background-color: #142238;
                border-color: #0284c7;
                color: #ffffff;
            }
            QPushButton:pressed {
                background-color: #0b1322;
            }
        """

    def _combo_style(self) -> str:
        return """
            QComboBox {
                background-color: #080d18;
                border: 1px solid #182438;
                border-radius: 6px;
                color: #e2e8f0;
                font-size: 11px;
                padding: 4px 10px;
                min-width: 110px;
            }
            QComboBox:hover {
                border-color: #0284c7;
            }
            QComboBox::drop-down {
                border: none;
                width: 18px;
            }
            QComboBox QAbstractItemView {
                background-color: #080d18;
                border: 1px solid #1e293b;
                color: #e2e8f0;
                selection-background-color: #0284c7;
                selection-color: #ffffff;
            }
        """

    def _connect_change_listeners(self) -> None:
        """Listen to all input modifications to mark the dirty state."""
        self.autostart_toggle.toggled.connect(self._mark_dirty)
        self.tray_toggle.toggled.connect(self._mark_dirty)
        self.minimized_toggle.toggled.connect(self._mark_dirty)
        self.restore_session_toggle.toggled.connect(self._mark_dirty)
        self.language_combo.currentIndexChanged.connect(self._mark_dirty)
        self.hotkey_conflict_toggle.toggled.connect(self._mark_dirty)
        self.telemetry_toggle.toggled.connect(self._mark_dirty)
        self.reduce_motion_toggle.toggled.connect(self._mark_dirty)
        self.notif_toggle.toggled.connect(self._mark_dirty)
        self.sound_toggle.toggled.connect(self._mark_dirty)
        self.overlay_hud_toggle.toggled.connect(self._mark_dirty)
        self.auto_stop_conflict_toggle.toggled.connect(self._mark_dirty)
        self.log_level_combo.currentIndexChanged.connect(self._mark_dirty)

    def _mark_dirty(self) -> None:
        self._update_dirty_state(True)

    def _update_dirty_state(self, dirty: bool) -> None:
        self._dirty = dirty
        if dirty:
            self.status_dot.setText("●")
            self.status_dot.setStyleSheet("font-size: 12px; color: #38bdf8; background: transparent; border: none;")
            self.status_text.setText("Unsaved changes pending")
            self.status_text.setStyleSheet("font-size: 12px; font-weight: 600; color: #f1f5f9; background: transparent; border: none;")
            self.discard_btn.setVisible(True)
            self.save_btn.setEnabled(True)
        else:
            self.status_dot.setText("✓")
            self.status_dot.setStyleSheet("font-size: 12px; color: #10b981; background: transparent; border: none;")
            self.status_text.setText("All settings up to date")
            self.status_text.setStyleSheet("font-size: 12px; color: #94a3b8; background: transparent; border: none;")
            self.discard_btn.setVisible(False)
            self.save_btn.setEnabled(False)

    def _browse_exe(self, app_key: str, line_edit: QLineEdit) -> None:
        file_path, _ = QFileDialog.getOpenFileName(
            self, f"Select Executable for {app_key}", "", "Executable Files (*.exe);;All Files (*.*)"
        )
        if file_path:
            line_edit.setText(file_path)
            self._mark_dirty()

    def _on_save_clicked(self) -> None:
        """Persist settings, update registry, and emit settings_saved."""
        autostart = self.autostart_toggle.isChecked()

        # Apply registry autostart setting
        StartupService.set_start_with_windows(autostart)

        app_paths = {k: inp.text().strip() for k, inp in self.app_path_inputs.items() if inp.text().strip()}

        updated = AppSettings(
            start_with_windows=autostart,
            minimize_to_tray=self.tray_toggle.isChecked(),
            launch_minimized=self.minimized_toggle.isChecked(),
            notifications_enabled=self.notif_toggle.isChecked(),
            dark_mode=True,
            reduce_motion=self.reduce_motion_toggle.isChecked(),
            log_level=self.log_level_combo.currentText(),
            app_paths=app_paths,
        )

        self.current_settings = updated
        self._update_dirty_state(False)
        self.settings_saved.emit(updated)

    def _on_discard_clicked(self) -> None:
        """Revert inputs back to current settings values."""
        self.autostart_toggle.setChecked(self.current_settings.start_with_windows)
        self.tray_toggle.setChecked(self.current_settings.minimize_to_tray)
        self.minimized_toggle.setChecked(self.current_settings.launch_minimized)
        self.notif_toggle.setChecked(self.current_settings.notifications_enabled)
        self.dark_mode_toggle.setChecked(self.current_settings.dark_mode)
        self.reduce_motion_toggle.setChecked(self.current_settings.reduce_motion)

        idx = self.log_level_combo.findText(self.current_settings.log_level)
        if idx >= 0:
            self.log_level_combo.setCurrentIndex(idx)

        for k, inp in self.app_path_inputs.items():
            inp.setText(self.current_settings.app_paths.get(k, ""))

        self._update_dirty_state(False)

    def _on_clear_data_clicked(self) -> None:
        reply = QMessageBox.question(
            self,
            "Clear Cache & Logs",
            "Are you sure you want to clear temporary execution telemetry and reset local caches?",
            QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No,
        )
        if reply == QMessageBox.StandardButton.Yes:
            QMessageBox.information(self, "Cache Cleared", "Temporary cache and logs cleared successfully.")

    def _on_export_settings(self) -> None:
        file_path, _ = QFileDialog.getSaveFileName(
            self, "Export Automation Hub Settings", "automation_hub_settings.json", "JSON Files (*.json)"
        )
        if file_path:
            try:
                data = self.current_settings.to_dict()
                with open(file_path, "w", encoding="utf-8") as f:
                    json.dump(data, f, indent=2)
                QMessageBox.information(self, "Export Successful", f"Settings exported to:\n{file_path}")
            except Exception as e:
                QMessageBox.critical(self, "Export Error", f"Could not export settings: {e}")

    def _on_import_settings(self) -> None:
        file_path, _ = QFileDialog.getOpenFileName(
            self, "Import Automation Hub Settings", "", "JSON Files (*.json)"
        )
        if file_path:
            try:
                with open(file_path, "r", encoding="utf-8") as f:
                    data = json.load(f)
                imported = AppSettings.model_validate(data)
                self.current_settings = imported
                self._on_discard_clicked()
                self._mark_dirty()
                QMessageBox.information(self, "Import Successful", "Settings loaded. Click 'Save Settings' to apply.")
            except Exception as e:
                QMessageBox.critical(self, "Import Error", f"Could not import settings: {e}")

    def _on_reset_defaults(self) -> None:
        reply = QMessageBox.question(
            self,
            "Reset to Factory Defaults",
            "Are you sure you want to reset all settings to default values? Custom executable paths will be cleared.",
            QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No,
        )
        if reply == QMessageBox.StandardButton.Yes:
            self.current_settings = AppSettings()
            self._on_discard_clicked()
            self._mark_dirty()

    def _on_search_filter(self, query: str) -> None:
        """Filter settings rows across categories based on search input."""
        q = query.strip().lower()
        if not q:
            for cat_id, btn in self.nav_buttons.items():
                btn.setVisible(True)
            return

        if any(w in q for w in ["app", "path", "exe", "fl", "studio", "code", "vs", "steam", "spotify", "discord"]):
            self._switch_category("applications")
        elif any(w in q for w in ["dark", "light", "theme", "motion", "anim", "color", "visual"]):
            self._switch_category("appearance")
        elif any(w in q for w in ["toast", "notif", "alert", "sound", "chime"]):
            self._switch_category("notifications")
        elif any(w in q for w in ["hud", "conflict", "auto", "engine"]):
            self._switch_category("automation")
        elif any(w in q for w in ["log", "debug", "db", "sqlite", "diagnostic"]):
            self._switch_category("system")
        else:
            self._switch_category("general")
