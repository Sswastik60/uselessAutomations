from PySide6.QtCore import Qt, Signal
from PySide6.QtWidgets import QLabel, QPushButton, QVBoxLayout, QWidget


class SidebarWidget(QWidget):
    """Sidebar navigation bar for main application window."""

    page_changed = Signal(int)  # index of page

    NAV_ITEMS = [
        ("⚡  Dashboard", 0),
        ("🛠  Mode Editor", 1),
        ("🔌  Devices", 2),
        ("📜  Logs", 3),
        ("⚙  Settings", 4),
    ]

    def __init__(self, parent=None):
        super().__init__(parent)
        self.setObjectName("SidebarWidget")

        layout = QVBoxLayout(self)
        layout.setContentsMargins(12, 16, 12, 16)
        layout.setSpacing(6)

        # App title header
        title_lbl = QLabel("⚡ Automation Hub")
        title_lbl.setObjectName("SidebarTitle")
        layout.addWidget(title_lbl)

        sub_title = QLabel("Windows 11 Mode Control")
        sub_title.setObjectName("SidebarSubtitle")
        layout.addWidget(sub_title)

        # Nav buttons
        self.buttons: list[QPushButton] = []
        for text, index in self.NAV_ITEMS:
            btn = QPushButton(text)
            btn.setCheckable(True)
            btn.setCursor(Qt.CursorShape.PointingHandCursor)
            btn.setProperty("class", "NavButton")
            btn.clicked.connect(lambda _, idx=index: self._on_btn_clicked(idx))
            layout.addWidget(btn)
            self.buttons.append(btn)

        layout.addStretch()

        # System info footer
        ver_lbl = QLabel("v1.0.0 Pro • Windows 11")
        ver_lbl.setStyleSheet("color: #475569; font-size: 11px; font-weight: 500; padding-left: 12px;")
        layout.addWidget(ver_lbl)

        # Select dashboard by default
        self.set_active_page(0)

    def _on_btn_clicked(self, index: int) -> None:
        self.set_active_page(index)
        self.page_changed.emit(index)

    def set_active_page(self, index: int) -> None:
        for i, btn in enumerate(self.buttons):
            btn.setChecked(i == index)
