"""Signature Mode Execution Overlay HUD Window.

Provides a polished, non-intrusive floating HUD widget that appears on system-wide hotkey trigger,
animates action steps through (○ -> ◌ -> ✓), displays '✓ You're ready.', and gracefully fades out.
"""

import logging
from typing import Dict, List, Optional
from PySide6.QtCore import QPoint, QPropertyAnimation, QTimer, Qt
from PySide6.QtGui import QColor, QFont, QGuiApplication
from PySide6.QtWidgets import (
    QFrame,
    QGraphicsDropShadowEffect,
    QHBoxLayout,
    QLabel,
    QProgressBar,
    QVBoxLayout,
    QWidget,
)

from app.ui.animation_manager import AnimationManager
from app.ui.design.tokens import DarkPalette, Duration, Easing

logger = logging.getLogger(__name__)


class ExecutionStepWidget(QWidget):
    """Step indicator row displaying step status transitions (○ -> ◌ -> ✓)."""

    def __init__(self, step_num: int, title: str, parent=None):
        super().__init__(parent)
        layout = QHBoxLayout(self)
        layout.setContentsMargins(0, 2, 0, 2)
        layout.setSpacing(8)

        self.status_lbl = QLabel("○")
        self.status_lbl.setStyleSheet(f"font-size: 13px; color: {DarkPalette.TEXT_MUTED}; background: transparent;")
        layout.addWidget(self.status_lbl)

        self.title_lbl = QLabel(title)
        self.title_lbl.setStyleSheet(f"font-size: 12px; color: {DarkPalette.TEXT_SECONDARY}; background: transparent;")
        layout.addWidget(self.title_lbl, stretch=1)

    def set_running(self) -> None:
        self.status_lbl.setText("◌")
        self.status_lbl.setStyleSheet(f"font-size: 13px; color: {DarkPalette.ACCENT_LIGHT}; font-weight: 700; background: transparent;")
        self.title_lbl.setStyleSheet(f"font-size: 12px; color: {DarkPalette.TEXT_PRIMARY}; font-weight: 600; background: transparent;")

    def set_completed(self) -> None:
        self.status_lbl.setText("✓")
        self.status_lbl.setStyleSheet(f"font-size: 13px; color: {DarkPalette.SUCCESS}; font-weight: 800; background: transparent;")
        self.title_lbl.setStyleSheet(f"font-size: 12px; color: {DarkPalette.TEXT_PRIMARY}; background: transparent;")

    def set_failed(self, error: str) -> None:
        self.status_lbl.setText("✕")
        self.status_lbl.setStyleSheet(f"font-size: 13px; color: {DarkPalette.ERROR}; font-weight: 800; background: transparent;")
        self.title_lbl.setStyleSheet(f"font-size: 12px; color: {DarkPalette.ERROR}; background: transparent;")


class FloatingOverlayWindow(QWidget):
    """Signature HUD Overlay Window appearing on global hotkey trigger or execution."""

    _instance: Optional["FloatingOverlayWindow"] = None

    def __init__(self):
        super().__init__()
        FloatingOverlayWindow._instance = self

        self.setWindowFlags(
            Qt.WindowType.FramelessWindowHint
            | Qt.WindowType.Tool
            | Qt.WindowType.WindowStaysOnTopHint
            | Qt.WindowType.WindowDoesNotAcceptFocus
        )
        self.setAttribute(Qt.WidgetAttribute.WA_TranslucentBackground)
        self.setAttribute(Qt.WidgetAttribute.WA_ShowWithoutActivating)

        self.setFixedSize(360, 160)

        # Card Container
        self.card = QFrame(self)
        self.card.setGeometry(0, 0, 360, 160)
        self.card.setStyleSheet(
            """
            QFrame {
                background-color: #060913;
                border: 1px solid #1e293b;
                border-radius: 16px;
            }
            """
        )

        # Drop shadow
        shadow = QGraphicsDropShadowEffect(self)
        shadow.setBlurRadius(28)
        shadow.setColor(QColor(0, 0, 0, 200))
        shadow.setOffset(0, 8)
        self.card.setGraphicsEffect(shadow)

        layout = QVBoxLayout(self.card)
        layout.setContentsMargins(18, 16, 18, 16)
        layout.setSpacing(8)

        # Header Row: Icon + Title + Status Badge
        header_layout = QHBoxLayout()
        header_layout.setSpacing(10)

        self.icon_lbl = QLabel("⚡")
        self.icon_lbl.setStyleSheet("font-size: 24px; background: transparent; border: none;")
        header_layout.addWidget(self.icon_lbl)

        self.title_lbl = QLabel("Executing Mode...")
        self.title_lbl.setStyleSheet(
            f"font-size: 15px; font-weight: 800; color: {DarkPalette.TEXT_PRIMARY}; background: transparent; border: none;"
        )
        header_layout.addWidget(self.title_lbl, stretch=1)

        self.badge_lbl = QLabel("RUNNING")
        self.badge_lbl.setStyleSheet(
            """
            QLabel {
                background-color: #0284c7;
                color: #ffffff;
                font-size: 10px;
                font-weight: 800;
                border-radius: 5px;
                padding: 3px 7px;
                border: none;
            }
            """
        )
        header_layout.addWidget(self.badge_lbl)

        layout.addLayout(header_layout)

        # Active Step Description
        self.status_sub_lbl = QLabel("Preparing setup...")
        self.status_sub_lbl.setStyleSheet(
            f"font-size: 12px; font-weight: 600; color: {DarkPalette.TEXT_SECONDARY}; background: transparent; border: none;"
        )
        layout.addWidget(self.status_sub_lbl)

        # Progress Bar
        self.progress_bar = QProgressBar()
        self.progress_bar.setRange(0, 100)
        self.progress_bar.setValue(0)
        self.progress_bar.setFixedHeight(6)
        self.progress_bar.setTextVisible(False)
        self.progress_bar.setStyleSheet(
            """
            QProgressBar {
                background-color: #0f172a;
                border: none;
                border-radius: 3px;
            }
            QProgressBar::chunk {
                background-color: qlineargradient(x1:0, y1:0, x2:1, y2:0, stop:0 #0284c7, stop:1 #10b981);
                border-radius: 3px;
            }
            """
        )
        layout.addWidget(self.progress_bar)

        # Auto-dismiss timer
        self.dismiss_timer = QTimer(self)
        self.dismiss_timer.setSingleShot(True)
        self.dismiss_timer.timeout.connect(self.hide_overlay)

    def position_top_right(self) -> None:
        """Position overlay in the top-right corner of the primary screen."""
        screen = QGuiApplication.primaryScreen()
        if screen:
            geo = screen.availableGeometry()
            x = geo.x() + geo.width() - self.width() - 28
            y = geo.y() + 28
            self.move(x, y)

    def start_mode(self, mode_id: str, mode_name: str, icon: str = "⚡") -> None:
        """Trigger overlay display when mode execution begins."""
        self.dismiss_timer.stop()
        self.icon_lbl.setText(icon or "⚡")
        self.title_lbl.setText(f"{mode_name}")
        self.status_sub_lbl.setText("Preparing your setup...")
        self.badge_lbl.setText("RUNNING")
        self.badge_lbl.setStyleSheet(
            "background-color: #0284c7; color: #ffffff; font-size: 10px; font-weight: 800; border-radius: 5px; padding: 3px 7px; border: none;"
        )
        self.card.setStyleSheet(
            """
            QFrame {
                background-color: #060913;
                border: 1px solid #0284c7;
                border-radius: 16px;
            }
            """
        )
        self.progress_bar.setValue(0)

        self.position_top_right()
        self.show()
        AnimationManager.fade_in(self, duration=Duration.PANEL)

    def update_action(self, step_idx: int, total_steps: int, action_name: str) -> None:
        """Update active step display."""
        pct = int(((step_idx - 1) / max(1, total_steps)) * 100)
        self.progress_bar.setValue(pct)
        self.status_sub_lbl.setText(f"Step {step_idx}/{total_steps}: {action_name}")

    def update_progress(self, percent: float, status_msg: str) -> None:
        """Update progress bar value."""
        self.progress_bar.setValue(int(percent))
        if status_msg:
            self.status_sub_lbl.setText(status_msg)

    def complete_mode(self, mode_id: str, mode_name: str, duration: float) -> None:
        """Show signature completed state: '✓ You're ready.' and auto-dismiss gracefully."""
        self.progress_bar.setValue(100)
        self.icon_lbl.setText("✓")
        self.icon_lbl.setStyleSheet("font-size: 24px; color: #10b981; background: transparent; border: none;")
        self.title_lbl.setText("You're ready.")
        self.status_sub_lbl.setText(f"{mode_name} completed in {duration:.2f}s")
        self.badge_lbl.setText("READY")
        self.badge_lbl.setStyleSheet(
            "background-color: #059669; color: #ffffff; font-size: 10px; font-weight: 800; border-radius: 5px; padding: 3px 7px; border: none;"
        )
        self.card.setStyleSheet(
            """
            QFrame {
                background-color: #021a12;
                border: 1px solid #10b981;
                border-radius: 16px;
            }
            """
        )
        AnimationManager.pulse(self.card, duration=Duration.EXECUTION)
        self.dismiss_timer.start(1800)

    def fail_mode(self, mode_id: str, mode_name: str, error_msg: str) -> None:
        """Show human error state and auto-dismiss after 3.5s."""
        self.icon_lbl.setText("✕")
        self.icon_lbl.setStyleSheet("font-size: 24px; color: #ef4444; background: transparent; border: none;")
        self.title_lbl.setText(f"Couldn't finish {mode_name}")
        self.status_sub_lbl.setText(error_msg[:45] + "..." if len(error_msg) > 45 else error_msg)
        self.badge_lbl.setText("FAILED")
        self.badge_lbl.setStyleSheet(
            "background-color: #991b1b; color: #ffffff; font-size: 10px; font-weight: 800; border-radius: 5px; padding: 3px 7px; border: none;"
        )
        self.card.setStyleSheet(
            """
            QFrame {
                background-color: #1a0505;
                border: 1px solid #ef4444;
                border-radius: 16px;
            }
            """
        )
        AnimationManager.shake(self)
        self.dismiss_timer.start(3500)

    def hide_overlay(self) -> None:
        """Fade out overlay smoothly."""
        AnimationManager.fade_out(self, duration=Duration.PANEL, hide_on_finish=True)


def get_overlay_window() -> FloatingOverlayWindow:
    """Singleton getter for FloatingOverlayWindow."""
    if FloatingOverlayWindow._instance is None:
        FloatingOverlayWindow._instance = FloatingOverlayWindow()
    return FloatingOverlayWindow._instance
