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

        self.badge_btn = QPushButton("⌘ K")
        self.badge_btn.setFixedSize(36, 22)
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


class RightColumnPanel(QWidget):
    """Right sidebar panel containing Connected Devices, Recent Activity, and Live HUD."""

    view_devices_requested = Signal()
    view_activity_requested = Signal()
    run_mode_requested = Signal(str)

    def __init__(self, parent=None):
        super().__init__(parent)
        self.setFixedWidth(290)

        main_layout = QVBoxLayout(self)
        main_layout.setContentsMargins(0, 12, 14, 14)
        main_layout.setSpacing(14)

        # 1. Top Header Status Bar
        top_bar = QHBoxLayout()
        top_bar.setContentsMargins(4, 4, 4, 4)
        top_bar.setSpacing(8)

        self.ready_badge = QLabel("● System Ready")
        self.ready_badge.setStyleSheet(
            """
            QLabel {
                background-color: #062b1e;
                color: #10b981;
                border: 1px solid #0f5132;
                border-radius: 12px;
                padding: 4px 12px;
                font-size: 11px;
                font-weight: 600;
            }
            """
        )

        bell_btn = QPushButton("🔔")
        bell_btn.setFixedSize(28, 28)
        bell_btn.setStyleSheet(
            """
            QPushButton {
                background-color: #0b0d14;
                border: 1px solid #1c2232;
                border-radius: 14px;
                font-size: 11px;
                color: #94a3b8;
            }
            QPushButton:hover {
                background-color: #141a28;
                color: #f8fafc;
            }
            """
        )

        top_bar.addStretch()
        top_bar.addWidget(self.ready_badge)
        top_bar.addWidget(bell_btn)
        main_layout.addLayout(top_bar)

        # 2. Connected Devices Card
        devices_card = QFrame()
        devices_card.setStyleSheet(
            """
            QFrame {
                background-color: #06070b;
                border: 1px solid #141620;
                border-radius: 14px;
                padding: 4px;
            }
            """
        )
        dev_layout = QVBoxLayout(devices_card)
        dev_layout.setContentsMargins(14, 12, 14, 12)
        dev_layout.setSpacing(10)

        dev_header = QHBoxLayout()
        dev_title = QLabel("● Connected Devices")
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
            row = QHBoxLayout()
            row.setSpacing(8)

            icon_box = QLabel(icon)
            icon_box.setFixedSize(28, 28)
            icon_box.setAlignment(Qt.AlignmentFlag.AlignCenter)
            icon_box.setStyleSheet("background-color: #0d101a; border-radius: 14px; font-size: 12px;")

            text_box = QVBoxLayout()
            text_box.setSpacing(1)
            name_lbl = QLabel(name)
            name_lbl.setStyleSheet("font-size: 11px; font-weight: 600; color: #f8fafc;")
            sub_lbl = QLabel(sub)
            sub_lbl.setStyleSheet("font-size: 9px; color: #64748b;")
            text_box.addWidget(name_lbl)
            text_box.addWidget(sub_lbl)

            conn_badge = QLabel("Connected")
            conn_badge.setStyleSheet(
                """
                background-color: #062b1e;
                color: #10b981;
                border: 1px solid #0f5132;
                border-radius: 6px;
                padding: 2px 6px;
                font-size: 9px;
                font-weight: 600;
                """
            )

            arrow = QLabel("›")
            arrow.setStyleSheet("color: #475569; font-size: 14px; font-weight: bold;")

            row.addWidget(icon_box)
            row.addLayout(text_box, stretch=1)
            row.addWidget(conn_badge)
            row.addWidget(arrow)
            dev_layout.addLayout(row)

        main_layout.addWidget(devices_card)

        # 3. Recent Activity Card
        act_card = QFrame()
        act_card.setStyleSheet(
            """
            QFrame {
                background-color: #06070b;
                border: 1px solid #141620;
                border-radius: 14px;
                padding: 4px;
            }
            """
        )
        act_layout = QVBoxLayout(act_card)
        act_layout.setContentsMargins(14, 12, 14, 12)
        act_layout.setSpacing(10)

        act_header = QHBoxLayout()
        act_title = QLabel("🕒 Recent Activity")
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
            row = QHBoxLayout()
            row.setSpacing(8)

            icon_box = QLabel(icon)
            icon_box.setFixedSize(28, 28)
            icon_box.setAlignment(Qt.AlignmentFlag.AlignCenter)
            icon_box.setStyleSheet("background-color: #0d101a; border-radius: 14px; font-size: 12px;")

            text_box = QVBoxLayout()
            text_box.setSpacing(1)
            name_lbl = QLabel(name)
            name_lbl.setStyleSheet("font-size: 11px; font-weight: 600; color: #f8fafc;")
            sub_lbl = QLabel(time_str)
            sub_lbl.setStyleSheet("font-size: 9px; color: #64748b;")
            text_box.addWidget(name_lbl)
            text_box.addWidget(sub_lbl)

            arrow = QPushButton("›")
            arrow.setCursor(Qt.CursorShape.PointingHandCursor)
            arrow.setStyleSheet("background: transparent; border: none; color: #475569; font-size: 14px; font-weight: bold;")
            arrow.clicked.connect(lambda _, mode_id=m_id: self.run_mode_requested.emit(mode_id))

            row.addWidget(icon_box)
            row.addLayout(text_box, stretch=1)
            row.addWidget(arrow)
            act_layout.addLayout(row)

        main_layout.addWidget(act_card)

        # 4. Docked Live Execution HUD Card
        self.hud_card = QFrame()
        self.hud_card.setStyleSheet(
            """
            QFrame {
                background-color: #07090f;
                border: 1px solid #1a2234;
                border-radius: 14px;
                padding: 6px;
            }
            """
        )
        hud_layout = QVBoxLayout(self.hud_card)
        hud_layout.setContentsMargins(14, 12, 14, 12)
        hud_layout.setSpacing(8)

        hud_head = QHBoxLayout()
        hud_icon = QLabel("🎸")
        hud_icon.setStyleSheet("font-size: 14px;")
        hud_info = QVBoxLayout()
        hud_info.setSpacing(1)
        self.hud_title = QLabel("Guitar Mode")
        self.hud_title.setStyleSheet("font-size: 11px; font-weight: 700; color: #f8fafc;")
        self.hud_sub = QLabel("Ready for automation")
        self.hud_sub.setStyleSheet("font-size: 9px; color: #94a3b8;")
        hud_info.addWidget(self.hud_title)
        hud_info.addWidget(self.hud_sub)

        close_btn = QPushButton("✕")
        close_btn.setFixedSize(18, 18)
        close_btn.setStyleSheet("background: transparent; border: none; color: #64748b; font-size: 10px;")

        hud_head.addWidget(hud_icon)
        hud_head.addLayout(hud_info, stretch=1)
        hud_head.addWidget(close_btn)
        hud_layout.addLayout(hud_head)

        # Steps
        self.steps_box = QVBoxLayout()
        self.steps_box.setSpacing(4)
        sample_steps = [
            ("✓", "Detecting audio interface", "2.1s", "#10b981"),
            ("✓", "Configuring input/output", "1.8s", "#10b981"),
            ("✓", "Launching FL Studio", "3.4s", "#10b981"),
            ("○", "Opening project", "—", "#64748b"),
        ]
        for mark, desc, duration, color in sample_steps:
            s_row = QHBoxLayout()
            m_lbl = QLabel(mark)
            m_lbl.setStyleSheet(f"color: {color}; font-size: 11px; font-weight: bold;")
            d_lbl = QLabel(desc)
            d_lbl.setStyleSheet("color: #cbd5e1; font-size: 10px;")
            dur_lbl = QLabel(duration)
            dur_lbl.setStyleSheet("color: #64748b; font-size: 9px;")
            s_row.addWidget(m_lbl)
            s_row.addWidget(d_lbl, stretch=1)
            s_row.addWidget(dur_lbl)
            self.steps_box.addLayout(s_row)

        hud_layout.addLayout(self.steps_box)

        # Glowing Progress Bar with Counter
        prog_row = QHBoxLayout()
        prog_bar = QFrame()
        prog_bar.setFixedHeight(5)
        prog_bar.setStyleSheet(
            """
            QFrame {
                background: qlineargradient(x1:0, y1:0, x2:1, y2:0, stop:0 #38bdf8, stop:0.75 #818cf8, stop:0.76 #161a24, stop:1 #161a24);
                border-radius: 2px;
            }
            """
        )
        prog_count = QLabel("3/4")
        prog_count.setStyleSheet("font-size: 9px; color: #94a3b8; font-weight: 600;")
        prog_row.addWidget(prog_bar, stretch=1)
        prog_row.addWidget(prog_count)
        hud_layout.addLayout(prog_row)

        main_layout.addWidget(self.hud_card)
        main_layout.addStretch()


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

    def __init__(self, parent=None):
        super().__init__(parent)
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
            self.right_col.ready_badge.setStyleSheet(
                """
                background-color: #0c2538;
                color: #38bdf8;
                border: 1px solid #1e40af;
                border-radius: 12px;
                padding: 4px 12px;
                font-size: 11px;
                font-weight: 600;
                """
            )
            self.right_col.hud_title.setText(f"{running_mode} Mode")
            self.right_col.hud_sub.setText("Executing automation steps...")
        else:
            self.right_col.ready_badge.setText("● System Ready")
            self.right_col.ready_badge.setStyleSheet(
                """
                background-color: #062b1e;
                color: #10b981;
                border: 1px solid #0f5132;
                border-radius: 12px;
                padding: 4px 12px;
                font-size: 11px;
                font-weight: 600;
                """
            )
