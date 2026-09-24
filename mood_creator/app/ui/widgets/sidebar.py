"""World-class sidebar navigation matching the premium desktop control center design."""

from typing import List, Tuple
from PySide6.QtCore import QEasingCurve, QPropertyAnimation, Qt, Signal
from PySide6.QtWidgets import (
    QFrame,
    QHBoxLayout,
    QLabel,
    QPushButton,
    QVBoxLayout,
    QWidget,
)

from app.ui.styles.design_tokens import AnimationDuration, DarkPalette


class NavItemButton(QPushButton):
    """Navigation button with custom pill highlight and glowing active dot."""

    def __init__(self, icon_str: str, label_str: str, parent=None):
        super().__init__(parent)
        self.icon_str = icon_str
        self.label_str = label_str
        self.setCheckable(True)
        self.setCursor(Qt.CursorShape.PointingHandCursor)
        self.setFixedHeight(42)

        layout = QHBoxLayout(self)
        layout.setContentsMargins(14, 0, 14, 0)
        layout.setSpacing(12)

        self.icon_lbl = QLabel(icon_str)
        self.icon_lbl.setStyleSheet("font-size: 15px; color: #94a3b8; background: transparent;")
        
        self.text_lbl = QLabel(label_str)
        self.text_lbl.setStyleSheet("font-size: 13px; font-weight: 500; color: #94a3b8; background: transparent;")

        self.dot_lbl = QLabel("●")
        self.dot_lbl.setStyleSheet("font-size: 9px; color: #38bdf8; background: transparent;")
        self.dot_lbl.setVisible(False)

        layout.addWidget(self.icon_lbl)
        layout.addWidget(self.text_lbl, stretch=1)
        layout.addWidget(self.dot_lbl)

    def set_active_state(self, is_active: bool) -> None:
        self.setChecked(is_active)
        self.dot_lbl.setVisible(is_active)
        if is_active:
            self.setStyleSheet(
                """
                QPushButton {
                    background-color: #12151f;
                    border: 1px solid #1e2433;
                    border-radius: 10px;
                }
                """
            )
            self.icon_lbl.setStyleSheet("font-size: 15px; color: #ffffff; background: transparent;")
            self.text_lbl.setStyleSheet("font-size: 13px; font-weight: 600; color: #ffffff; background: transparent;")
        else:
            self.setStyleSheet(
                """
                QPushButton {
                    background-color: transparent;
                    border: 1px solid transparent;
                    border-radius: 10px;
                }
                QPushButton:hover {
                    background-color: #0c0e14;
                    border: 1px solid #181b24;
                }
                """
            )
            self.icon_lbl.setStyleSheet("font-size: 15px; color: #94a3b8; background: transparent;")
            self.text_lbl.setStyleSheet("font-size: 13px; font-weight: 500; color: #94a3b8; background: transparent;")


class SidebarWidget(QWidget):
    """World-class sidebar navigation panel with profile card and active indicators."""

    page_changed = Signal(int)  # Page index
    theme_toggle_requested = Signal()

    NAV_ITEMS: List[Tuple[str, str, int]] = [
        ("🏠", "Home", 0),
        ("⊞", "Modes", 1),
        ("🖥", "Devices", 2),
        ("📈", "Activity", 3),
        ("⚙", "Settings", 4),
    ]

    def __init__(self, parent=None):
        super().__init__(parent)
        self.setObjectName("SidebarWidget")
        self.setFixedWidth(224)
        self.setStyleSheet(
            """
            #SidebarWidget {
                background-color: #030305;
                border-right: 1px solid #12131a;
            }
            """
        )

        main_layout = QVBoxLayout(self)
        main_layout.setContentsMargins(14, 16, 14, 16)
        main_layout.setSpacing(8)

        # 1. Traffic Light Window Controls / App Branding
        top_bar = QHBoxLayout()
        top_bar.setContentsMargins(4, 0, 4, 10)
        top_bar.setSpacing(6)

        dot_red = QLabel("●")
        dot_red.setStyleSheet("color: #ef4444; font-size: 11px;")
        dot_yellow = QLabel("●")
        dot_yellow.setStyleSheet("color: #f59e0b; font-size: 11px;")
        dot_green = QLabel("●")
        dot_green.setStyleSheet("color: #10b981; font-size: 11px;")

        top_bar.addWidget(dot_red)
        top_bar.addWidget(dot_yellow)
        top_bar.addWidget(dot_green)
        top_bar.addStretch()
        main_layout.addLayout(top_bar)

        # App Logo & Tagline Header
        logo_box = QHBoxLayout()
        logo_box.setContentsMargins(4, 0, 4, 6)
        logo_box.setSpacing(10)

        logo_icon = QLabel("⚡")
        logo_icon.setStyleSheet(
            """
            font-size: 18px;
            color: #38bdf8;
            background-color: #0e1526;
            border: 1px solid #1e293b;
            border-radius: 8px;
            padding: 4px 6px;
            """
        )

        logo_text_box = QVBoxLayout()
        logo_text_box.setSpacing(1)

        self.title_lbl = QLabel("Automation Hub")
        self.title_lbl.setStyleSheet("font-size: 15px; font-weight: 700; color: #f8fafc;")

        self.sub_title = QLabel("Your computer. Ready for what's next.")
        self.sub_title.setStyleSheet("color: #64748b; font-size: 10px; font-weight: 400;")

        logo_text_box.addWidget(self.title_lbl)
        logo_text_box.addWidget(self.sub_title)

        logo_box.addWidget(logo_icon)
        logo_box.addLayout(logo_text_box)
        main_layout.addLayout(logo_box)

        main_layout.addSpacing(14)

        # 2. Navigation Items
        self.nav_buttons: List[NavItemButton] = []
        for icon, label, index in self.NAV_ITEMS:
            btn = NavItemButton(icon, label)
            btn.clicked.connect(lambda _, idx=index: self._on_btn_clicked(idx))
            main_layout.addWidget(btn)
            self.nav_buttons.append(btn)

        main_layout.addStretch()

        # 3. User Profile Card
        profile_card = QFrame()
        profile_card.setStyleSheet(
            """
            QFrame {
                background-color: #08090e;
                border: 1px solid #161822;
                border-radius: 12px;
                padding: 4px;
            }
            QFrame:hover {
                background-color: #0c0e16;
                border-color: #1e2230;
            }
            """
        )
        profile_layout = QHBoxLayout(profile_card)
        profile_layout.setContentsMargins(8, 8, 8, 8)
        profile_layout.setSpacing(10)

        avatar_lbl = QLabel("👤")
        avatar_lbl.setStyleSheet(
            """
            background-color: #141824;
            color: #38bdf8;
            border: 1px solid #243048;
            border-radius: 14px;
            font-size: 14px;
            padding: 4px 6px;
            """
        )

        name_box = QVBoxLayout()
        name_box.setSpacing(1)
        name_lbl = QLabel("Swastik")
        name_lbl.setStyleSheet("color: #f8fafc; font-size: 12px; font-weight: 600;")
        badge_lbl = QLabel("Pro")
        badge_lbl.setStyleSheet("color: #38bdf8; font-size: 10px; font-weight: 500;")
        name_box.addWidget(name_lbl)
        name_box.addWidget(badge_lbl)

        chevron_lbl = QLabel("›")
        chevron_lbl.setStyleSheet("color: #64748b; font-size: 16px; font-weight: bold;")

        profile_layout.addWidget(avatar_lbl)
        profile_layout.addLayout(name_box, stretch=1)
        profile_layout.addWidget(chevron_lbl)

        main_layout.addWidget(profile_card)

        # 4. Theme Selector Row
        theme_btn = QPushButton("🌙 Dark Mode   ⌵")
        theme_btn.setCursor(Qt.CursorShape.PointingHandCursor)
        theme_btn.setStyleSheet(
            """
            QPushButton {
                background-color: transparent;
                border: none;
                color: #64748b;
                font-size: 11px;
                padding: 6px 8px;
                text-align: left;
            }
            QPushButton:hover {
                color: #94a3b8;
            }
            """
        )
        theme_btn.clicked.connect(self.theme_toggle_requested.emit)
        main_layout.addWidget(theme_btn)

        # Select Dashboard (index 0) by default
        self.set_active_page(0)

    def _on_btn_clicked(self, index: int) -> None:
        self.set_active_page(index)
        self.page_changed.emit(index)

    def set_active_page(self, index: int) -> None:
        for i, btn in enumerate(self.nav_buttons):
            btn.set_active_state(i == index)
