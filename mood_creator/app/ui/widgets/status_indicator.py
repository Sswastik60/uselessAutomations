from PySide6.QtCore import Qt
from PySide6.QtWidgets import QHBoxLayout, QLabel, QWidget


class StatusIndicator(QWidget):
    """Status dot indicator with state label."""

    def __init__(self, label_text: str = "", active: bool = True, parent=None):
        super().__init__(parent)
        self._active = active

        layout = QHBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(6)

        self.dot = QLabel()
        self.dot.setFixedSize(10, 10)
        self.set_active(active)

        self.label = QLabel(label_text)
        self.label.setStyleSheet("font-size: 12px; color: #94a3b8;")

        layout.addWidget(self.dot)
        layout.addWidget(self.label)

    def set_active(self, active: bool, text: str | None = None) -> None:
        self._active = active
        color = "#10b981" if active else "#ef4444"
        self.dot.setStyleSheet(f"background-color: {color}; border-radius: 5px;")
        if text:
            self.label.setText(text)
