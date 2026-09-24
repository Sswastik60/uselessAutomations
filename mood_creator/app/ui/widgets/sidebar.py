"""Compact, collapsible sidebar navigation with smooth animation."""

from typing import List, Tuple
from PySide6.QtCore import QPropertyAnimation, QEasingCurve, Qt, Signal
from PySide6.QtWidgets import QHBoxLayout, QLabel, QPushButton, QVBoxLayout, QWidget

from app.ui.animation_manager import AnimationManager
from app.ui.styles.design_tokens import AnimationDuration, DarkPalette


class SidebarWidget(QWidget):
    """Collapsible sidebar navigation bar with smooth transition animations."""

    page_changed = Signal(int)  # Page index

    NAV_ITEMS: List[Tuple[str, str, int]] = [
        ("⌂", "Dashboard", 0),
        ("⚡", "Modes", 1),
        ("🔌", "Devices", 2),
        ("📜", "Activity", 3),
        ("⚙", "Settings", 4),
    ]

    def __init__(self, parent=None):
        super().__init__(parent)
        self.setObjectName("SidebarWidget")
        self.is_collapsed = False

        self.setMinimumWidth(230)
        self.setMaximumWidth(230)

        main_layout = QVBoxLayout(self)
        main_layout.setContentsMargins(10, 16, 10, 16)
        main_layout.setSpacing(6)

        # Header: App Title & Toggle Button
        header_layout = QHBoxLayout()
        header_layout.setContentsMargins(4, 0, 4, 0)

        self.title_lbl = QLabel("⚡ Automation Hub")
        self.title_lbl.setObjectName("SidebarTitle")
        self.title_lbl.setStyleSheet(f"font-size: 16px; font-weight: 800; color: {DarkPalette.ACCENT_LIGHT};")
        header_layout.addWidget(self.title_lbl, stretch=1)

        self.toggle_btn = QPushButton("◀")
        self.toggle_btn.setFixedSize(26, 26)
        self.toggle_btn.setCursor(Qt.CursorShape.PointingHandCursor)
        self.toggle_btn.setStyleSheet(
            """
            QPushButton {
                background-color: #0f172a;
                color: #94a3b8;
                border: 1px solid #1e293b;
                border-radius: 6px;
                font-size: 11px;
            }
            QPushButton:hover {
                background-color: #1e293b;
                color: #f8fafc;
            }
            """
        )
        self.toggle_btn.clicked.connect(self.toggle_collapse)
        header_layout.addWidget(self.toggle_btn)

        main_layout.addLayout(header_layout)

        self.sub_title = QLabel("Windows 11 Control")
        self.sub_title.setObjectName("SidebarSubtitle")
        self.sub_title.setStyleSheet("color: #64748b; font-size: 11px; padding-left: 4px; margin-bottom: 12px;")
        main_layout.addWidget(self.sub_title)

        # Nav Buttons
        self.buttons: List[QPushButton] = []
        for icon, label, index in self.NAV_ITEMS:
            btn = QPushButton(f"  {icon}   {label}")
            btn.setCheckable(True)
            btn.setCursor(Qt.CursorShape.PointingHandCursor)
            btn.setProperty("class", "NavButton")
            btn.setToolTip(label)
            btn.clicked.connect(lambda _, idx=index: self._on_btn_clicked(idx))
            main_layout.addWidget(btn)
            self.buttons.append(btn)

        main_layout.addStretch()

        # Keyboard Shortcut Hint / Version Footer
        self.hint_lbl = QLabel("Press Ctrl+K to search")
        self.hint_lbl.setStyleSheet("color: #475569; font-size: 11px; font-weight: 600; padding: 6px;")
        main_layout.addWidget(self.hint_lbl)

        # Select Dashboard (index 0) by default
        self.set_active_page(0)

    def toggle_collapse(self) -> None:
        """Toggle sidebar collapsed / expanded state with smooth width animation."""
        self.is_collapsed = not self.is_collapsed
        target_width = 68 if self.is_collapsed else 230

        self.anim = QPropertyAnimation(self, b"maximumWidth")
        self.anim.setDuration(AnimationDuration.PANEL)
        self.anim.setStartValue(self.width())
        self.anim.setEndValue(target_width)
        self.anim.setEasingCurve(QEasingCurve.Type.OutCubic)

        self.anim_min = QPropertyAnimation(self, b"minimumWidth")
        self.anim_min.setDuration(AnimationDuration.PANEL)
        self.anim_min.setStartValue(self.width())
        self.anim_min.setEndValue(target_width)
        self.anim_min.setEasingCurve(QEasingCurve.Type.OutCubic)

        self.toggle_btn.setText("▶" if self.is_collapsed else "◀")
        self.title_lbl.setVisible(not self.is_collapsed)
        self.sub_title.setVisible(not self.is_collapsed)
        self.hint_lbl.setVisible(not self.is_collapsed)

        for btn, (icon, label, _) in zip(self.buttons, self.NAV_ITEMS):
            if self.is_collapsed:
                btn.setText(icon)
            else:
                btn.setText(f"  {icon}   {label}")

        self.anim.start()
        self.anim_min.start()

    def _on_btn_clicked(self, index: int) -> None:
        self.set_active_page(index)
        self.page_changed.emit(index)

    def set_active_page(self, index: int) -> None:
        for i, btn in enumerate(self.buttons):
            btn.setChecked(i == index)
