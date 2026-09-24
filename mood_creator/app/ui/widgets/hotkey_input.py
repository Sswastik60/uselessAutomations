from PySide6.QtCore import Qt, Signal
from PySide6.QtGui import QKeyEvent
from PySide6.QtWidgets import QHBoxLayout, QLineEdit, QPushButton, QWidget


class HotkeyInputWidget(QWidget):
    """Interactive hotkey recorder input with key detection."""

    hotkey_changed = Signal(str)

    def __init__(self, parent=None):
        super().__init__(parent)
        self.is_recording = False

        layout = QHBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(8)

        self.line_edit = QLineEdit()
        self.line_edit.setPlaceholderText("e.g. CTRL+ALT+G (or click Record)")
        self.line_edit.textChanged.connect(self.hotkey_changed.emit)

        self.record_btn = QPushButton("🎙 Record Hotkey")
        self.record_btn.setProperty("class", "SecondaryButton")
        self.record_btn.setFixedWidth(130)
        self.record_btn.clicked.connect(self.toggle_recording)

        self.clear_btn = QPushButton("✕")
        self.clear_btn.setProperty("class", "SecondaryButton")
        self.clear_btn.setFixedWidth(32)
        self.clear_btn.setToolTip("Clear Hotkey")
        self.clear_btn.clicked.connect(lambda: self.line_edit.setText(""))

        layout.addWidget(self.line_edit, stretch=1)
        layout.addWidget(self.record_btn)
        layout.addWidget(self.clear_btn)

        self.line_edit.installEventFilter(self)

    def toggle_recording(self) -> None:
        if self.is_recording:
            self.stop_recording()
        else:
            self.start_recording()

    def start_recording(self) -> None:
        self.is_recording = True
        self.record_btn.setText("🔴 Press Keys...")
        self.record_btn.setStyleSheet("background-color: #991b1b; color: #ffffff; border-color: #ef4444;")
        self.line_edit.setFocus()
        self.line_edit.setPlaceholderText("Press hotkey combination...")

    def stop_recording(self) -> None:
        self.is_recording = False
        self.record_btn.setText("🎙 Record Hotkey")
        self.record_btn.setStyleSheet("")
        self.line_edit.setPlaceholderText("e.g. CTRL+ALT+G (or click Record)")

    def text(self) -> str:
        return self.line_edit.text().strip()

    def setText(self, text: str) -> None:
        self.line_edit.setText(text)

    def eventFilter(self, obj, event) -> bool:
        if obj == self.line_edit and self.is_recording and event.type() == QKeyEvent.Type.KeyPress:
            key = event.key()
            if key in (Qt.Key.Key_Control, Qt.Key.Key_Shift, Qt.Key.Key_Alt, Qt.Key.Key_Meta):
                return True  # Wait for non-modifier key press

            parts = []
            mods = event.modifiers()
            if mods & Qt.KeyboardModifier.ControlModifier:
                parts.append("CTRL")
            if mods & Qt.KeyboardModifier.AltModifier:
                parts.append("ALT")
            if mods & Qt.KeyboardModifier.ShiftModifier:
                parts.append("SHIFT")
            if mods & Qt.KeyboardModifier.MetaModifier:
                parts.append("WIN")

            # Key name
            if Qt.Key.Key_A <= key <= Qt.Key.Key_Z:
                parts.append(chr(key))
            elif Qt.Key.Key_0 <= key <= Qt.Key.Key_9:
                parts.append(chr(key))
            elif Qt.Key.Key_F1 <= key <= Qt.Key.Key_F12:
                parts.append(f"F{key - Qt.Key.Key_F1 + 1}")
            elif key == Qt.Key.Key_Space:
                parts.append("SPACE")
            elif key in (Qt.Key.Key_Return, Qt.Key.Key_Enter):
                parts.append("ENTER")
            elif key == Qt.Key.Key_Escape:
                parts.append("ESC")
            elif key == Qt.Key.Key_Tab:
                parts.append("TAB")

            if parts:
                hotkey_str = "+".join(parts)
                self.line_edit.setText(hotkey_str)
                self.stop_recording()
                return True

        return super().eventFilter(obj, event)
