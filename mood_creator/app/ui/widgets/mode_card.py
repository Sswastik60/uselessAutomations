"""Tactile, interactive Mode Card component with hover elevation and press compression."""

from typing import Optional
from PySide6.QtCore import QPoint, QPropertyAnimation, Qt, Signal
from PySide6.QtWidgets import (
    QFrame,
    QGraphicsDropShadowEffect,
    QHBoxLayout,
    QLabel,
    QMenu,
    QPushButton,
    QVBoxLayout,
    QWidget,
)
from PySide6.QtGui import QColor

from app.models.mode import Mode
from app.ui.animation_manager import AnimationManager
from app.ui.design.tokens import DarkPalette, Duration, Easing, Radius, Spacing


class ModeCard(QFrame):
    """High-quality interactive Mode Card with physical press compression and subtle ambient depth."""

    run_requested = Signal(str)        # mode_id
    edit_requested = Signal(str)       # mode_id
    export_requested = Signal(str)     # mode_id
    duplicate_requested = Signal(str)  # mode_id
    delete_requested = Signal(str)     # mode_id

    def __init__(self, mode: Mode, parent=None):
        super().__init__(parent)
        self.mode = mode
        self.setObjectName("ModeCard")
        self.setProperty("class", "ModeCard")
        self.setMinimumWidth(280)
        self.setMinimumHeight(210)
        self.setCursor(Qt.CursorShape.PointingHandCursor)

        # Ambient subtle shadow
        self.shadow = QGraphicsDropShadowEffect(self)
        self.shadow.setBlurRadius(16)
        self.shadow.setColor(QColor(0, 0, 0, 100))
        self.shadow.setOffset(0, 4)
        self.setGraphicsEffect(self.shadow)

        main_layout = QVBoxLayout(self)
        main_layout.setContentsMargins(Spacing.LG, Spacing.LG, Spacing.LG, Spacing.LG)
        main_layout.setSpacing(Spacing.MD)

        # Top Bar: Icon + Action Badge + Hotkey Pill
        top_layout = QHBoxLayout()
        
        self.icon_lbl = QLabel(mode.icon or "⚡")
        self.icon_lbl.setStyleSheet("font-size: 32px; background: transparent; padding: 0px;")
        top_layout.addWidget(self.icon_lbl)

        # Action count badge
        act_count = len(mode.actions)
        act_badge = QLabel(f"{act_count} Step{'s' if act_count != 1 else ''}")
        act_badge.setStyleSheet(
            """
            QLabel {
                background-color: rgba(255, 255, 255, 0.05);
                border: 1px solid rgba(255, 255, 255, 0.1);
                border-radius: 6px;
                color: #94a3b8;
                padding: 3px 8px;
                font-size: 11px;
                font-weight: 600;
            }
            """
        )
        top_layout.addWidget(act_badge)

        top_layout.addStretch()

        # Keyboard shortcut pill
        if mode.hotkey:
            self.hk_lbl = QLabel(mode.hotkey)
            self.hk_lbl.setStyleSheet(
                """
                QLabel {
                    background-color: #050505;
                    border: 1px solid #38bdf8;
                    border-radius: 6px;
                    color: #38bdf8;
                    padding: 3px 8px;
                    font-size: 11px;
                    font-weight: 700;
                    font-family: 'Consolas', monospace;
                }
                """
            )
            top_layout.addWidget(self.hk_lbl)

        main_layout.addLayout(top_layout)

        # Title & Subtitle/Description (Visual Rhythm)
        self.title_lbl = QLabel(mode.name)
        self.title_lbl.setStyleSheet("font-size: 18px; font-weight: 800; color: #f8fafc; letter-spacing: -0.3px;")
        main_layout.addWidget(self.title_lbl)

        self.desc_lbl = QLabel(mode.description or "Configured computer setup mode.")
        self.desc_lbl.setStyleSheet("font-size: 12px; color: #94a3b8; line-height: 1.4;")
        self.desc_lbl.setWordWrap(True)
        self.desc_lbl.setMaximumHeight(36)
        main_layout.addWidget(self.desc_lbl)

        # Step preview pills
        if mode.actions:
            preview_layout = QHBoxLayout()
            preview_layout.setSpacing(4)
            for act in mode.actions[:3]:
                act_type_short = act.type.split(".")[-1].replace("_", " ").title()
                p_lbl = QLabel(act_type_short)
                p_lbl.setStyleSheet(
                    "background-color: #121212; border-radius: 4px; color: #cbd5e1; font-size: 11px; padding: 2px 6px;"
                )
                preview_layout.addWidget(p_lbl)
            if len(mode.actions) > 3:
                more_lbl = QLabel(f"+{len(mode.actions)-3} more")
                more_lbl.setStyleSheet("color: #64748b; font-size: 11px;")
                preview_layout.addWidget(more_lbl)
            preview_layout.addStretch()
            main_layout.addLayout(preview_layout)

        main_layout.addStretch()

        # Bottom Action Bar: Run (Primary), Edit (Secondary), Context Menu (...)
        btn_layout = QHBoxLayout()
        btn_layout.setSpacing(8)

        self.run_btn = QPushButton("▶  Run Mode")
        self.run_btn.setProperty("class", "PrimaryButton")
        self.run_btn.setCursor(Qt.CursorShape.PointingHandCursor)
        self.run_btn.clicked.connect(lambda: self.run_requested.emit(self.mode.id))

        self.edit_btn = QPushButton("⚙ Edit")
        self.edit_btn.setProperty("class", "SecondaryButton")
        self.edit_btn.setCursor(Qt.CursorShape.PointingHandCursor)
        self.edit_btn.clicked.connect(lambda: self.edit_requested.emit(self.mode.id))

        self.more_btn = QPushButton("⋮")
        self.more_btn.setProperty("class", "SecondaryButton")
        self.more_btn.setFixedWidth(32)
        self.more_btn.setCursor(Qt.CursorShape.PointingHandCursor)
        self.more_btn.clicked.connect(self._show_context_menu)

        btn_layout.addWidget(self.run_btn, stretch=3)
        btn_layout.addWidget(self.edit_btn, stretch=2)
        btn_layout.addWidget(self.more_btn)

        main_layout.addLayout(btn_layout)

    def enterEvent(self, event) -> None:
        """Hover elevation animation."""
        super().enterEvent(event)
        self.shadow.setBlurRadius(24)
        self.shadow.setColor(QColor(2, 132, 199, 120))
        self.shadow.setOffset(0, 6)

    def leaveEvent(self, event) -> None:
        """Return to resting state."""
        super().leaveEvent(event)
        self.shadow.setBlurRadius(16)
        self.shadow.setColor(QColor(0, 0, 0, 100))
        self.shadow.setOffset(0, 4)

    def mousePressEvent(self, event) -> None:
        """Physical press compression feedback."""
        super().mousePressEvent(event)
        if event.button() == Qt.MouseButton.LeftButton:
            AnimationManager.pulse(self, duration=Duration.MICRO)

    def _show_context_menu(self) -> None:
        menu = QMenu(self)
        menu.setStyleSheet(
            """
            QMenu {
                background-color: #0f172a;
                color: #f8fafc;
                border: 1px solid #1e293b;
                border-radius: 8px;
                padding: 4px;
            }
            QMenu::item {
                padding: 6px 16px;
                border-radius: 4px;
            }
            QMenu::item:selected {
                background-color: #0284c7;
                color: #ffffff;
            }
            """
        )

        run_act = menu.addAction("▶  Run Mode")
        run_act.triggered.connect(lambda: self.run_requested.emit(self.mode.id))

        edit_act = menu.addAction("⚙  Edit Mode")
        edit_act.triggered.connect(lambda: self.edit_requested.emit(self.mode.id))

        dup_act = menu.addAction("❐  Duplicate Mode")
        dup_act.triggered.connect(lambda: self.duplicate_requested.emit(self.mode.id))

        exp_act = menu.addAction("📤  Export JSON...")
        exp_act.triggered.connect(lambda: self.export_requested.emit(self.mode.id))

        menu.addSeparator()
        del_act = menu.addAction("🗑  Delete Mode")
        del_act.triggered.connect(lambda: self.delete_requested.emit(self.mode.id))

        menu.exec(self.more_btn.mapToGlobal(self.more_btn.rect().bottomLeft()))
