"""Subtle non-intrusive toast notifications system."""

import logging
from typing import Optional
from PySide6.QtCore import QPoint, QTimer, Qt
from PySide6.QtWidgets import QHBoxLayout, QLabel, QWidget

from app.ui.animation_manager import AnimationManager
from app.ui.styles.design_tokens import AnimationDuration, DarkPalette

logger = logging.getLogger(__name__)


class ToastWidget(QWidget):
    """Subtle floating toast notification pill."""

    def __init__(self, message: str, level: str = "info", parent: Optional[QWidget] = None):
        super().__init__(parent)
        self.setWindowFlags(
            Qt.WindowType.FramelessWindowHint
            | Qt.WindowType.Tool
            | Qt.WindowType.WindowStaysOnTopHint
            | Qt.WindowType.WindowDoesNotAcceptFocus
        )
        self.setAttribute(Qt.WidgetAttribute.WA_TranslucentBackground)
        self.setAttribute(Qt.WidgetAttribute.WA_ShowWithoutActivating)

        layout = QHBoxLayout(self)
        layout.setContentsMargins(14, 10, 16, 10)
        layout.setSpacing(10)

        # Icon prefix based on level
        icons = {
            "info": "⚡",
            "success": "✓",
            "warning": "⚠",
            "error": "✕",
        }
        icon_colors = {
            "info": DarkPalette.ACCENT_LIGHT,
            "success": DarkPalette.SUCCESS,
            "warning": DarkPalette.WARNING,
            "error": DarkPalette.ERROR,
        }

        self.icon_lbl = QLabel(icons.get(level, "⚡"))
        self.icon_lbl.setStyleSheet(
            f"font-size: 15px; font-weight: 800; color: {icon_colors.get(level, DarkPalette.TEXT_PRIMARY)};"
        )
        layout.addWidget(self.icon_lbl)

        self.msg_lbl = QLabel(message)
        self.msg_lbl.setStyleSheet(
            f"font-size: 13px; font-weight: 600; color: {DarkPalette.TEXT_PRIMARY};"
        )
        layout.addWidget(self.msg_lbl)

        # Style pill container
        self.setStyleSheet(
            f"""
            ToastWidget {{
                background-color: #0f172a;
                border: 1px solid #1e293b;
                border-radius: 10px;
            }}
            """
        )

        self.adjustSize()

        # Timer to auto dismiss
        self.dismiss_timer = QTimer(self)
        self.dismiss_timer.setSingleShot(True)
        self.dismiss_timer.timeout.connect(self.dismiss)

    def show_toast(self, duration_ms: int = 3000) -> None:
        """Display toast with smooth fade-in and set dismiss timer."""
        self.show()
        AnimationManager.fade_in(self, duration=AnimationDuration.NORMAL)
        self.dismiss_timer.start(duration_ms)

    def dismiss(self) -> None:
        """Fade out toast and delete widget."""
        AnimationManager.fade_out(
            self,
            duration=AnimationDuration.NORMAL,
            on_finished=self.deleteLater,
        )


class ToastManager:
    """Global utility manager for displaying subtle desktop toast notifications."""

    _active_toasts = []

    @classmethod
    def show_toast(
        cls,
        parent: Optional[QWidget],
        message: str,
        level: str = "success",
        duration_ms: int = 2500,
    ) -> ToastWidget:
        """Spawn and align a subtle toast notification near the bottom right of screen or parent."""
        toast = ToastWidget(message=message, level=level, parent=parent)

        if parent:
            parent_geo = parent.geometry()
            global_pos = parent.mapToGlobal(QPoint(0, 0))
            x = global_pos.x() + parent_geo.width() - toast.width() - 24
            y = global_pos.y() + parent_geo.height() - toast.height() - 24
            toast.move(max(10, x), max(10, y))
        else:
            toast.move(100, 100)

        toast.show_toast(duration_ms=duration_ms)
        cls._active_toasts.append(toast)
        return toast
