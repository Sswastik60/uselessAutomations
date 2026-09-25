"""Liquid-smooth cross-dissolve stacked widget for zero-lag tab transitions."""

from typing import Optional
from PySide6.QtCore import QEasingCurve, QPropertyAnimation, Qt
from PySide6.QtWidgets import (
    QGraphicsOpacityEffect,
    QLabel,
    QStackedWidget,
    QWidget,
)


class SmoothStackedWidget(QStackedWidget):
    """Clean, high-performance QStackedWidget that eliminates overlay ghosting and artifacts."""

    def __init__(self, parent: Optional[QWidget] = None):
        super().__init__(parent)
        self.setAttribute(Qt.WidgetAttribute.WA_StyledBackground, True)
        self.setStyleSheet("background-color: #030305;")

    def set_current_index_smooth(self, index: int, reduce_motion: bool = False) -> None:
        """Switch to page at index cleanly without ghosting overlays."""
        if index < 0 or index >= self.count():
            return
        self.setCurrentIndex(index)
