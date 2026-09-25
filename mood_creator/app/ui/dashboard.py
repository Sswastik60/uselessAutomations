"""World-Class Main Dashboard View matching the exact reference UI design.

Features:
- Panoramic twilight dune hero header with personalized greeting ("Good evening, Swastik 👋")
- Pill-shaped command palette search bar with ⌘K badge
- 6-card Modes section (Guitar, Gaming, Coding, Music Production, Study, Movie) with artwork
- Bottom 'Less setup. More doing.' mountain banner and 4-tile Quick Actions panel
- Right column with Connected Devices, Recent Activity, and Live Execution HUD
"""

from datetime import datetime
from pathlib import Path
from typing import Dict, List, Optional
from PySide6.QtCore import QPoint, QRect, QRectF, Qt, Signal
from PySide6.QtGui import (
    QBrush,
    QColor,
    QFont,
    QLinearGradient,
    QPainter,
    QPainterPath,
    QPen,
    QPixmap,
)
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
from app.ui.smooth_scroll import install_smooth_scroll
from app.ui.styles.design_tokens import AnimationDuration, DarkPalette
from app.ui.widgets.mode_card import ModeCard


class HeroBannerWidget(QFrame):
    """Panoramic hero banner painting hero_dunes.jpg with an atmospheric gradient overlay."""

    search_submitted = Signal(str)
    command_palette_requested = Signal()

    def __init__(self, parent=None):
        super().__init__(parent)
        self.setFixedHeight(175)
        self.setObjectName("HeroBannerWidget")
        
        # Load dune artwork
        self.dunes_pixmap: Optional[QPixmap] = None
        app_dir = Path(__file__).resolve().parent.parent.parent
        img_path = app_dir / "assets" / "ui" / "hero_dunes.jpg"
        if img_path.exists():
            self.dunes_pixmap = QPixmap(str(img_path))

        layout = QVBoxLayout(self)
        layout.setContentsMargins(28, 20, 28, 16)
        layout.setSpacing(6)

        # Dynamic greeting based on time of day
        hour = datetime.now().hour
        greeting = "Good morning" if hour < 12 else ("Good afternoon" if hour < 18 else "Good evening")

        self.greeting_lbl = QLabel(f"{greeting},")
        self.greeting_lbl.setStyleSheet("font-size: 13px; font-weight: 500; color: #94a3b8; background: transparent;")
        layout.addWidget(self.greeting_lbl)

        self.name_lbl = QLabel("Swastik 👋")
        self.name_lbl.setStyleSheet("font-size: 26px; font-weight: 800; color: #ffffff; background: transparent; letter-spacing: -0.5px;")
        layout.addWidget(self.name_lbl)

        self.sub_lbl = QLabel("What would you like to do today?")
        self.sub_lbl.setStyleSheet("font-size: 13px; color: #64748b; background: transparent; margin-bottom: 4px;")
        layout.addWidget(self.sub_lbl)

        # Search Bar with ⌘K badge
        search_box = QFrame()
        search_box.setFixedHeight(42)
        search_box.setStyleSheet(
            """
            QFrame {
                background-color: rgba(10, 12, 18, 0.85);
                border: 1px solid rgba(34, 40, 58, 0.9);
                border-radius: 21px;
            }
            QFrame:hover {
                border-color: rgba(56, 189, 248, 0.6);
            }
            """
        )
        sb_layout = QHBoxLayout(search_box)
        sb_layout.setContentsMargins(14, 0, 14, 0)
        sb_layout.setSpacing(10)

        search_icon = QLabel("🔍")
        search_icon.setStyleSheet("color: #64748b; font-size: 13px; background: transparent;")
        sb_layout.addWidget(search_icon)

        self.search_input = QLineEdit()
        self.search_input.setPlaceholderText("Search modes, actions, or type a command...")
        self.search_input.setStyleSheet(
            """
            QLineEdit {
                background: transparent;
                border: none;
                color: #f8fafc;
                font-size: 12px;
            }
            QLineEdit::placeholder {
                color: #475569;
            }
            """
        )
        sb_layout.addWidget(self.search_input, stretch=1)

        self.badge_btn = QPushButton("Ctrl K")
        self.badge_btn.setFixedSize(44, 22)
        self.badge_btn.setCursor(Qt.CursorShape.PointingHandCursor)
        self.badge_btn.setStyleSheet(
            """
            QPushButton {
                background-color: #1a2030;
                color: #94a3b8;
                border: 1px solid #28334a;
                border-radius: 5px;
                font-size: 10px;
                font-weight: 700;
            }
            QPushButton:hover {
                background-color: #242d44;
                color: #ffffff;
            }
            """
        )
        self.badge_btn.clicked.connect(self.command_palette_requested.emit)
        sb_layout.addWidget(self.badge_btn)

        layout.addWidget(search_box)

    def paintEvent(self, event) -> None:
        painter = QPainter(self)
        painter.setRenderHint(QPainter.RenderHint.Antialiasing)
        painter.setRenderHint(QPainter.RenderHint.SmoothPixmapTransform)

        rect = self.rect()
        w = rect.width()
        h = rect.height()

        # Rounded container
        path = QPainterPath()
        path.addRoundedRect(QRectF(rect), 16, 16)
        painter.setClipPath(path)

        # Base background
        painter.fillPath(path, QBrush(QColor("#040508")))

        # Draw dunes in top right half with fade
        if self.dunes_pixmap and not self.dunes_pixmap.isNull():
            dune_w = int(w * 0.75)
            dune_rect = QRect(w - dune_w, 0, dune_w, h)
            scaled = self.dunes_pixmap.scaled(
                dune_w, h,
                Qt.AspectRatioMode.KeepAspectRatioByExpanding,
                Qt.TransformationMode.SmoothTransformation,
            )
            painter.drawPixmap(dune_rect, scaled)

            # Gradient mask: solid black on left fading to transparent on right
            grad = QLinearGradient(0, 0, w, 0)
            grad.setColorAt(0.0, QColor(4, 5, 8, 255))
            grad.setColorAt(0.35, QColor(4, 5, 8, 240))
            grad.setColorAt(0.70, QColor(4, 5, 8, 120))
            grad.setColorAt(1.0, QColor(4, 5, 8, 40))

            painter.fillRect(rect, QBrush(grad))

            # Bottom gradient fade into main window base
            b_grad = QLinearGradient(0, h - 40, 0, h)
            b_grad.setColorAt(0.0, QColor(4, 5, 8, 0))
            b_grad.setColorAt(1.0, QColor(4, 5, 8, 240))
            painter.fillRect(rect, QBrush(b_grad))


class MountainBannerWidget(QFrame):
    """'Less setup. More doing.' aesthetic mountain card."""

    def __init__(self, parent=None):
        super().__init__(parent)
        self.setFixedHeight(138)
        self.setFixedWidth(270)
        self.setObjectName("MountainBannerWidget")

        self.mountain_pix: Optional[QPixmap] = None
        app_dir = Path(__file__).resolve().parent.parent.parent
        img_path = app_dir / "assets" / "ui" / "banner_mountain.jpg"
        if img_path.exists():
            self.mountain_pix = QPixmap(str(img_path))

        layout = QVBoxLayout(self)
        layout.setContentsMargins(20, 20, 20, 20)
        layout.setAlignment(Qt.AlignmentFlag.AlignLeft | Qt.AlignmentFlag.AlignTop)

        lbl1 = QLabel("Less setup.")
        lbl1.setStyleSheet("font-size: 16px; font-weight: 700; color: #ffffff; background: transparent;")
        lbl2 = QLabel("More doing.")
        lbl2.setStyleSheet("font-size: 16px; font-weight: 700; color: #ffffff; background: transparent;")
        
        layout.addWidget(lbl1)
        layout.addWidget(lbl2)
        layout.addStretch()

    def paintEvent(self, event) -> None:
        painter = QPainter(self)
        painter.setRenderHint(QPainter.RenderHint.Antialiasing)
        painter.setRenderHint(QPainter.RenderHint.SmoothPixmapTransform)

        rect = self.rect()
        path = QPainterPath()
        path.addRoundedRect(QRectF(rect), 14, 14)
        painter.setClipPath(path)

        painter.fillPath(path, QBrush(QColor("#08090e")))

        if self.mountain_pix and not self.mountain_pix.isNull():
            scaled = self.mountain_pix.scaled(
                rect.size(),
                Qt.AspectRatioMode.KeepAspectRatioByExpanding,
                Qt.TransformationMode.SmoothTransformation,
            )
            painter.drawPixmap(rect, scaled)

            # Dark gradient overlay for text readability
            grad = QLinearGradient(0, 0, rect.width(), rect.height())
            grad.setColorAt(0.0, QColor(5, 6, 10, 220))
            grad.setColorAt(0.6, QColor(5, 6, 10, 140))
            grad.setColorAt(1.0, QColor(5, 6, 10, 60))
            painter.fillRect(rect, QBrush(grad))

        # Border
        painter.setClipping(False)
        painter.setPen(QPen(QColor("#161824"), 1.0))
        painter.drawRoundedRect(QRectF(0.5, 0.5, rect.width() - 1, rect.height() - 1), 14, 14)


class QuickActionTile(QPushButton):
    """Single Quick Action tile matching the mockup."""

    def __init__(self, icon_str: str, title: str, subtitle: str, parent=None):
        super().__init__(parent)
        self.setFixedHeight(88)
        self.setCursor(Qt.CursorShape.PointingHandCursor)
        self.setStyleSheet(
            """
            QPushButton {
                background-color: #0b0d14;
                border: 1px solid #181c28;
                border-radius: 12px;
                padding: 10px;
                text-align: center;
            }
            QPushButton:hover {
                background-color: #101420;
                border-color: #28334a;
            }
            """
        )

        layout = QVBoxLayout(self)
        layout.setContentsMargins(6, 6, 6, 6)
        layout.setSpacing(3)
        layout.setAlignment(Qt.AlignmentFlag.AlignCenter)

        icon_lbl = QLabel(icon_str)
        icon_lbl.setStyleSheet("font-size: 16px; color: #f8fafc; background: transparent;")
        icon_lbl.setAlignment(Qt.AlignmentFlag.AlignCenter)

        title_lbl = QLabel(title)
        title_lbl.setStyleSheet("font-size: 11px; font-weight: 600; color: #f8fafc; background: transparent;")
        title_lbl.setAlignment(Qt.AlignmentFlag.AlignCenter)

        sub_lbl = QLabel(subtitle)
        sub_lbl.setStyleSheet("font-size: 9px; color: #64748b; background: transparent;")
        sub_lbl.setAlignment(Qt.AlignmentFlag.AlignCenter)

        layout.addWidget(icon_lbl)
        layout.addWidget(title_lbl)
        layout.addWidget(sub_lbl)


class QuickActionsWidget(QFrame):
    """⚡ Quick Actions row with 4 action tiles."""

    create_clicked = Signal()
    import_clicked = Signal()
    settings_clicked = Signal()
    logs_clicked = Signal()

    def __init__(self, parent=None):
        super().__init__(parent)
        self.setFixedHeight(138)
        self.setStyleSheet(
            """
            QFrame#QuickActionsWidget {
                background-color: #06070b;
                border: 1px solid #141620;
                border-radius: 14px;
                padding: 12px;
            }
            """
        )
        self.setObjectName("QuickActionsWidget")

        main_layout = QVBoxLayout(self)
        main_layout.setContentsMargins(14, 10, 14, 12)
        main_layout.setSpacing(8)

        # Header
        header = QLabel("⚡ Quick Actions")
        header.setStyleSheet("font-size: 12px; font-weight: 700; color: #cbd5e1; background: transparent;")
        main_layout.addWidget(header)

        # 4 Tiles in a Row
        tiles_layout = QHBoxLayout()
        tiles_layout.setSpacing(10)

        t1 = QuickActionTile("＋", "Create Mode", "Build your own")
        t1.clicked.connect(self.create_clicked.emit)

        t2 = QuickActionTile("📥", "Import Mode", "From JSON file")
        t2.clicked.connect(self.import_clicked.emit)

        t3 = QuickActionTile("⚙", "Settings", "Customize")
        t3.clicked.connect(self.settings_clicked.emit)

        t4 = QuickActionTile("📋", "Logs", "View history")
        t4.clicked.connect(self.logs_clicked.emit)

        tiles_layout.addWidget(t1)
        tiles_layout.addWidget(t2)
        tiles_layout.addWidget(t3)
        tiles_layout.addWidget(t4)

        main_layout.addLayout(tiles_layout)


class DeviceItemRow(QFrame):
    """Refined individual device row widget with fixed height and hover interaction."""

    clicked = Signal()

    def __init__(self, icon: str, name: str, sub: str, is_connected: bool = True, parent=None):
        super().__init__(parent)
        self.setFixedHeight(38)
        self.setCursor(Qt.CursorShape.PointingHandCursor)
        self.setStyleSheet("""
            QFrame {
                background-color: transparent;
                border: none;
                border-radius: 8px;
            }
            QFrame:hover {
                background-color: #0b1220;
            }
        """)

        layout = QHBoxLayout(self)
        layout.setContentsMargins(6, 4, 8, 4)
        layout.setSpacing(8)

        icon_box = QLabel(icon)
        icon_box.setFixedSize(26, 26)
        icon_box.setAlignment(Qt.AlignmentFlag.AlignCenter)
        icon_box.setStyleSheet("background-color: #0c1424; border: 1px solid #16243b; border-radius: 6px; font-size: 11px;")

        text_box = QVBoxLayout()
        text_box.setContentsMargins(0, 0, 0, 0)
        text_box.setSpacing(1)

        name_lbl = QLabel(name)
        name_lbl.setStyleSheet("font-size: 11px; font-weight: 600; color: #f8fafc;")

        sub_lbl = QLabel(sub)
        sub_lbl.setStyleSheet("font-size: 9px; color: #64748b;")

        text_box.addWidget(name_lbl)
        text_box.addWidget(sub_lbl)

        conn_badge = QLabel("● Connected" if is_connected else "Offline")
        conn_badge.setStyleSheet("""
            background-color: #062b1e;
            color: #10b981;
            border: 1px solid #0f5132;
            border-radius: 4px;
            padding: 2px 6px;
            font-size: 9px;
            font-weight: 600;
        """)

        arrow = QLabel("›")
        arrow.setStyleSheet("color: #475569; font-size: 13px; font-weight: bold;")

        layout.addWidget(icon_box)
        layout.addLayout(text_box, stretch=1)
        layout.addWidget(conn_badge)
        layout.addWidget(arrow)

    def mousePressEvent(self, event) -> None:
        if event.button() == Qt.MouseButton.LeftButton:
            self.clicked.emit()
            event.accept()
        else:
            super().mousePressEvent(event)


class ActivityItemRow(QFrame):
    """Refined activity row widget with click-to-run action."""

    run_requested = Signal(str)

    def __init__(self, icon: str, name: str, time_str: str, mode_id: str, parent=None):
        super().__init__(parent)
        self.mode_id = mode_id
        self.setFixedHeight(38)
        self.setCursor(Qt.CursorShape.PointingHandCursor)
        self.setStyleSheet("""
            QFrame {
                background-color: transparent;
                border: none;
                border-radius: 8px;
            }
            QFrame:hover {
                background-color: #0b1220;
            }
        """)

        layout = QHBoxLayout(self)
        layout.setContentsMargins(6, 4, 8, 4)
        layout.setSpacing(8)

        icon_box = QLabel(icon)
        icon_box.setFixedSize(26, 26)
        icon_box.setAlignment(Qt.AlignmentFlag.AlignCenter)
        icon_box.setStyleSheet("background-color: #0c1424; border: 1px solid #16243b; border-radius: 6px; font-size: 11px;")

        text_box = QVBoxLayout()
        text_box.setContentsMargins(0, 0, 0, 0)
        text_box.setSpacing(1)

        name_lbl = QLabel(name)
        name_lbl.setStyleSheet("font-size: 11px; font-weight: 600; color: #f8fafc;")

        sub_lbl = QLabel(time_str)
        sub_lbl.setStyleSheet("font-size: 9px; color: #64748b;")

        text_box.addWidget(name_lbl)
        text_box.addWidget(sub_lbl)

        run_btn = QPushButton("›")
        run_btn.setFixedSize(20, 20)
        run_btn.setCursor(Qt.CursorShape.PointingHandCursor)
        run_btn.setStyleSheet("""
            QPushButton {
                background: transparent;
                border: none;
                color: #64748b;
                font-size: 14px;
                font-weight: bold;
            }
            QPushButton:hover {
                color: #38bdf8;
            }
        """)
        run_btn.clicked.connect(lambda: self.run_requested.emit(self.mode_id))

        layout.addWidget(icon_box)
        layout.addLayout(text_box, stretch=1)
        layout.addWidget(run_btn)

    def mousePressEvent(self, event) -> None:
        if event.button() == Qt.MouseButton.LeftButton:
            self.run_requested.emit(self.mode_id)
            event.accept()
        else:
            super().mousePressEvent(event)


class RightColumnPanel(QWidget):
    """Right sidebar panel containing Connected Devices, Recent Activity, and Live HUD."""

    view_devices_requested = Signal()
    view_activity_requested = Signal()
    run_mode_requested = Signal(str)
    notifications_clicked = Signal()

    def __init__(self, parent=None):
        super().__init__(parent)
        self.setFixedWidth(295)
        self.setStyleSheet("background: transparent;")

        panel_layout = QVBoxLayout(self)
        panel_layout.setContentsMargins(0, 0, 0, 0)
        panel_layout.setSpacing(0)

        # 1. Pinned Top Status Bar
        top_bar_widget = QWidget()
        top_bar_widget.setStyleSheet("background: transparent;")
        top_bar = QHBoxLayout(top_bar_widget)
        top_bar.setContentsMargins(4, 16, 16, 8)
        top_bar.setSpacing(8)

        self.ready_badge = QLabel("● System Ready")
        self.ready_badge.setStyleSheet("""
            QLabel {
                background-color: rgba(6, 78, 59, 0.45);
                color: #34d399;
                border: 1px solid rgba(16, 185, 129, 0.35);
                border-radius: 12px;
                padding: 4px 12px;
                font-size: 11px;
                font-weight: 600;
                letter-spacing: 0.2px;
            }
        """)

        self.bell_btn = QPushButton("🔔")
        self.bell_btn.setFixedSize(28, 28)
        self.bell_btn.setCursor(Qt.CursorShape.PointingHandCursor)
        self.bell_btn.setToolTip("System Notifications")
        self.bell_btn.setStyleSheet("""
            QPushButton {
                background-color: #090e18;
                border: 1px solid #162032;
                border-radius: 14px;
                font-size: 11px;
                color: #94a3b8;
            }
            QPushButton:hover {
                background-color: #121c2d;
                border-color: #0284c7;
                color: #f8fafc;
            }
            QPushButton:pressed {
                background-color: #0a1320;
            }
        """)
        self.bell_btn.clicked.connect(self.notifications_clicked.emit)

        top_bar.addStretch()
        top_bar.addWidget(self.ready_badge)
        top_bar.addWidget(self.bell_btn)
        panel_layout.addWidget(top_bar_widget)

        # 2. Scroll Area to ensure zero squishing/overlapping on any screen height
        scroll = QScrollArea()
        scroll.setWidgetResizable(True)
        scroll.setFrameShape(QFrame.Shape.NoFrame)
        scroll.setHorizontalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAlwaysOff)
        scroll.setVerticalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAsNeeded)
        self.scroll = scroll
        self.smooth_scroll = install_smooth_scroll(scroll)
        scroll.setStyleSheet("""
            QScrollArea {
                background: transparent;
                border: none;
            }
            QScrollBar:vertical {
                background: transparent;
                width: 4px;
                margin: 0px;
            }
            QScrollBar::handle:vertical {
                background: #141c2c;
                min-height: 20px;
                border-radius: 2px;
            }
            QScrollBar::handle:vertical:hover {
                background: #0284c7;
            }
            QScrollBar::add-line:vertical, QScrollBar::sub-line:vertical {
                height: 0px;
            }
        """)

        content_container = QWidget()
        content_container.setStyleSheet("background: transparent;")
        main_layout = QVBoxLayout(content_container)
        main_layout.setContentsMargins(4, 0, 16, 16)
        main_layout.setSpacing(12)

        # 2. Connected Devices Card
        devices_card = QFrame()
        devices_card.setObjectName("DevicesCard")
        devices_card.setStyleSheet("""
            QFrame#DevicesCard {
                background-color: #060913;
                border: 1px solid #131c2e;
                border-radius: 12px;
            }
        """)
        dev_layout = QVBoxLayout(devices_card)
        dev_layout.setContentsMargins(12, 10, 12, 10)
        dev_layout.setSpacing(2)

        dev_header = QHBoxLayout()
        dev_header.setContentsMargins(4, 0, 4, 4)
        dev_title = QLabel("Connected Devices")
        dev_title.setStyleSheet("font-size: 12px; font-weight: 700; color: #f8fafc;")

        dev_view_all = QPushButton("View all →")
        dev_view_all.setCursor(Qt.CursorShape.PointingHandCursor)
        dev_view_all.setStyleSheet("background: transparent; border: none; font-size: 10px; color: #64748b;")
        dev_view_all.clicked.connect(self.view_devices_requested.emit)

        dev_header.addWidget(dev_title)
        dev_header.addStretch()
        dev_header.addWidget(dev_view_all)
        dev_layout.addLayout(dev_header)

        # Device items list
        device_items = [
            ("🎸", "Scarlett 2i2", "Audio Interface"),
            ("🎧", "Headphones", "Audio Output"),
            ("🎹", "MIDI Keyboard", "MIDI Device"),
            ("🎮", "Controller", "Game Controller"),
        ]
        for icon, name, sub in device_items:
            row_widget = DeviceItemRow(icon, name, sub, is_connected=True, parent=devices_card)
            row_widget.clicked.connect(self.view_devices_requested.emit)
            dev_layout.addWidget(row_widget)

        main_layout.addWidget(devices_card)

        # 3. Recent Activity Card
        act_card = QFrame()
        act_card.setObjectName("ActCard")
        act_card.setStyleSheet("""
            QFrame#ActCard {
                background-color: #060913;
                border: 1px solid #131c2e;
                border-radius: 12px;
            }
        """)
        act_layout = QVBoxLayout(act_card)
        act_layout.setContentsMargins(12, 10, 12, 10)
        act_layout.setSpacing(2)

        act_header = QHBoxLayout()
        act_header.setContentsMargins(4, 0, 4, 4)
        act_title = QLabel("Recent Activity")
        act_title.setStyleSheet("font-size: 12px; font-weight: 700; color: #f8fafc;")

        act_view_all = QPushButton("View all →")
        act_view_all.setCursor(Qt.CursorShape.PointingHandCursor)
        act_view_all.setStyleSheet("background: transparent; border: none; font-size: 10px; color: #64748b;")
        act_view_all.clicked.connect(self.view_activity_requested.emit)

        act_header.addWidget(act_title)
        act_header.addStretch()
        act_header.addWidget(act_view_all)
        act_layout.addLayout(act_header)

        activities = [
            ("🎸", "Guitar Mode", "Completed • 8:42 PM", "guitar_mode"),
            ("💻", "Coding Mode", "Completed • 6:10 PM", "coding_mode"),
            ("🎮", "Gaming Mode", "Completed • Yesterday", "gaming_mode"),
            ("🎵", "Music Mode", "Completed • Yesterday", "music_production_mode"),
        ]
        for icon, name, time_str, m_id in activities:
            act_row = ActivityItemRow(icon, name, time_str, m_id, parent=act_card)
            act_row.run_requested.connect(self.run_mode_requested.emit)
            act_layout.addWidget(act_row)

        main_layout.addWidget(act_card)

        # 4. Docked Live Execution / Quick Status HUD Card
        self.hud_card = QFrame()
        self.hud_card.setObjectName("HUDCard")
        self.hud_card.setStyleSheet("""
            QFrame#HUDCard {
                background-color: #060913;
                border: 1px solid #131c2e;
                border-radius: 12px;
            }
        """)
        hud_layout = QVBoxLayout(self.hud_card)
        hud_layout.setContentsMargins(14, 12, 14, 12)
        hud_layout.setSpacing(8)

        hud_head = QHBoxLayout()
        hud_head.setSpacing(8)
        self.hud_icon = QLabel("⚡")
        self.hud_icon.setStyleSheet("font-size: 14px; color: #38bdf8; background: transparent;")

        hud_info = QVBoxLayout()
        hud_info.setSpacing(1)
        self.hud_title = QLabel("Automation Engine")
        self.hud_title.setStyleSheet("font-size: 11px; font-weight: 700; color: #f8fafc; background: transparent;")

        self.hud_sub = QLabel("Ready • All systems operational")
        self.hud_sub.setStyleSheet("font-size: 9px; color: #94a3b8; background: transparent;")

        hud_info.addWidget(self.hud_title)
        hud_info.addWidget(self.hud_sub)

        hud_head.addWidget(self.hud_icon)
        hud_head.addLayout(hud_info, stretch=1)
        hud_layout.addLayout(hud_head)

        # Active steps box (hidden when idle, shown when running)
        self.steps_box = QWidget()
        self.steps_box.setStyleSheet("background: transparent;")
        self.steps_layout = QVBoxLayout(self.steps_box)
        self.steps_layout.setContentsMargins(0, 4, 0, 0)
        self.steps_layout.setSpacing(4)
        hud_layout.addWidget(self.steps_box)
        self.steps_box.setVisible(False)

        # Electric-blue Progress Bar (zero purple)
        self.prog_container = QWidget()
        self.prog_container.setStyleSheet("background: transparent;")
        prog_row = QHBoxLayout(self.prog_container)
        prog_row.setContentsMargins(0, 0, 0, 0)
        prog_row.setSpacing(8)

        self.prog_bar = QFrame()
        self.prog_bar.setFixedHeight(4)
        self.prog_bar.setStyleSheet("""
            QFrame {
                background: qlineargradient(x1:0, y1:0, x2:1, y2:0, stop:0 #0284c7, stop:0.8 #38bdf8, stop:0.81 #131c2c, stop:1 #131c2c);
                border-radius: 2px;
            }
        """)
        self.prog_count = QLabel("Idle")
        self.prog_count.setStyleSheet("font-size: 9px; color: #64748b; font-weight: 600; background: transparent;")

        prog_row.addWidget(self.prog_bar, stretch=1)
        prog_row.addWidget(self.prog_count)
        hud_layout.addWidget(self.prog_container)

        main_layout.addWidget(self.hud_card)
        main_layout.addStretch()

        scroll.setWidget(content_container)
        panel_layout.addWidget(scroll)


class DashboardView(QWidget):
    """Main Dashboard View matching the complete reference mock."""

    run_mode_requested = Signal(str)        # mode_id
    edit_mode_requested = Signal(str)       # mode_id
    create_mode_requested = Signal()
    import_mode_requested = Signal(str)     # path
    export_mode_requested = Signal(str)     # mode_id
    duplicate_mode_requested = Signal(str)  # mode_id
    delete_mode_requested = Signal(str)     # mode_id
    navigate_requested = Signal(int)        # tab index (0=Home, 1=Modes, 2=Devices, 3=Activity, 4=Settings)
    notifications_requested = Signal()

    def __init__(self, parent=None):
        super().__init__(parent)
        self.setObjectName("DashboardView")
        self.setAttribute(Qt.WidgetAttribute.WA_StyledBackground, True)
        self.setAutoFillBackground(True)
        self.setStyleSheet("QWidget#DashboardView { background-color: #030305; }")
        self.all_modes: List[Mode] = []
        self._current_filtered_modes: List[Mode] = []

        # Master Horizontal Layout: Left Main Area + Right Sidebar Panel
        master_layout = QHBoxLayout(self)
        master_layout.setContentsMargins(0, 0, 0, 0)
        master_layout.setSpacing(0)

        # Scrollable Left Canvas Area
        scroll = QScrollArea()
        scroll.setWidgetResizable(True)
        scroll.setStyleSheet("QScrollArea { border: none; background: transparent; }")
        self.scroll = scroll
        self.smooth_scroll = install_smooth_scroll(scroll)

        left_canvas = QWidget()
        left_layout = QVBoxLayout(left_canvas)
        left_layout.setContentsMargins(24, 20, 24, 24)
        left_layout.setSpacing(20)

        # 1. Hero Dune Header Banner
        self.hero = HeroBannerWidget()
        self.hero.search_input.textChanged.connect(self._filter_modes)
        left_layout.addWidget(self.hero)

        # 2. Modes Section Header
        modes_header_box = QHBoxLayout()
        modes_header_box.setContentsMargins(4, 4, 4, 0)

        title_col = QVBoxLayout()
        title_col.setSpacing(1)
        m_title = QLabel("✦ Modes")
        m_title.setStyleSheet("font-size: 16px; font-weight: 700; color: #ffffff;")
        m_sub = QLabel("One click. Everything ready.")
        m_sub.setStyleSheet("font-size: 11px; color: #64748b;")
        title_col.addWidget(m_title)
        title_col.addWidget(m_sub)

        view_all_modes_btn = QPushButton("View all →")
        view_all_modes_btn.setCursor(Qt.CursorShape.PointingHandCursor)
        view_all_modes_btn.setStyleSheet(
            """
            QPushButton {
                background: transparent;
                border: none;
                font-size: 11px;
                color: #64748b;
            }
            QPushButton:hover {
                color: #38bdf8;
            }
            """
        )
        view_all_modes_btn.clicked.connect(lambda: self.navigate_requested.emit(1))

        modes_header_box.addLayout(title_col)
        modes_header_box.addStretch()
        modes_header_box.addWidget(view_all_modes_btn)
        left_layout.addLayout(modes_header_box)

        # 3. 2-Row x 3-Column Modes Grid
        self.grid_container = QWidget()
        self.grid_layout = QGridLayout(self.grid_container)
        self.grid_layout.setContentsMargins(0, 0, 0, 0)
        self.grid_layout.setSpacing(14)
        left_layout.addWidget(self.grid_container)

        # 4. Bottom Row: Mountain Card ("Less setup. More doing.") + Quick Actions Panel
        bottom_row = QHBoxLayout()
        bottom_row.setSpacing(14)

        self.mountain_banner = MountainBannerWidget()
        self.quick_actions = QuickActionsWidget()
        self.quick_actions.create_clicked.connect(self.create_mode_requested.emit)
        self.quick_actions.import_clicked.connect(self._on_import_clicked)
        self.quick_actions.settings_clicked.connect(lambda: self.navigate_requested.emit(4))
        self.quick_actions.logs_clicked.connect(lambda: self.navigate_requested.emit(3))

        bottom_row.addWidget(self.mountain_banner)
        bottom_row.addWidget(self.quick_actions, stretch=1)
        left_layout.addLayout(bottom_row)

        scroll.setWidget(left_canvas)
        master_layout.addWidget(scroll, stretch=1)

        # Right Column
        self.right_col = RightColumnPanel()
        self.right_col.view_devices_requested.connect(lambda: self.navigate_requested.emit(2))
        self.right_col.view_activity_requested.connect(lambda: self.navigate_requested.emit(3))
        self.right_col.run_mode_requested.connect(self.run_mode_requested.emit)
        self.right_col.notifications_clicked.connect(self.notifications_requested.emit)
        master_layout.addWidget(self.right_col)

    def update_modes(self, modes: List[Mode]) -> None:
        """Refresh mode cards grid."""
        def mode_sort_key(m: Mode) -> int:
            m_id = m.id.lower()
            order = ["guitar", "gaming", "coding", "music", "study", "movie"]
            for idx, key in enumerate(order):
                if key in m_id:
                    return idx
            return 999

        self.all_modes = sorted(modes, key=mode_sort_key)
        self._filter_modes(self.hero.search_input.text())

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

    def _render_modes(self, modes: List[Mode]) -> None:
        # Clear existing grid widgets
        while self.grid_layout.count():
            item = self.grid_layout.takeAt(0)
            if item.widget():
                item.widget().deleteLater()

        # Render 3 columns to match the 2-row x 3-column reference design
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
        """Update system status and active mode HUD."""
        if running_mode:
            self.right_col.ready_badge.setText(f"● Running {running_mode}")
            self.right_col.ready_badge.setStyleSheet("""
                background-color: #0c2538;
                color: #38bdf8;
                border: 1px solid #0284c7;
                border-radius: 12px;
                padding: 4px 12px;
                font-size: 11px;
                font-weight: 600;
            """)
            self.right_col.hud_title.setText(f"{running_mode} Mode")
            self.right_col.hud_sub.setText("Executing automation steps...")
            self.right_col.steps_box.setVisible(True)
            self.right_col.prog_count.setText("Running")
        else:
            self.right_col.ready_badge.setText("● System Ready")
            self.right_col.ready_badge.setStyleSheet("""
                background-color: #062b1e;
                color: #10b981;
                border: 1px solid #0f5132;
                border-radius: 12px;
                padding: 4px 12px;
                font-size: 11px;
                font-weight: 600;
            """)
            self.right_col.hud_title.setText("Automation Engine")
            self.right_col.hud_sub.setText("Ready • All systems operational")
            self.right_col.steps_box.setVisible(False)
            self.right_col.prog_count.setText("Idle")

