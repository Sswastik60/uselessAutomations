from PySide6.QtCore import Qt, Signal
from PySide6.QtWidgets import (
    QFrame,
    QHBoxLayout,
    QLabel,
    QMenu,
    QPushButton,
    QVBoxLayout,
    QWidget,
)
from app.models.mode import Mode


class ModeCard(QFrame):
    """Enhanced Dashboard card representing an Automation Mode."""

    run_requested = Signal(str)      # mode_id
    edit_requested = Signal(str)     # mode_id
    export_requested = Signal(str)   # mode_id
    duplicate_requested = Signal(str) # mode_id
    delete_requested = Signal(str)   # mode_id

    def __init__(self, mode: Mode, parent=None):
        super().__init__(parent)
        self.mode = mode
        self.setProperty("class", "ModeCard")
        self.setMinimumWidth(260)
        self.setMinimumHeight(210)
        self.setCursor(Qt.CursorShape.PointingHandCursor)

        main_layout = QVBoxLayout(self)
        main_layout.setContentsMargins(18, 16, 18, 16)
        main_layout.setSpacing(10)

        # Top row: Icon + Action Badge + Hotkey pill
        top_layout = QHBoxLayout()
        icon_lbl = QLabel(mode.icon or "⚡")
        icon_lbl.setProperty("class", "ModeIcon")

        top_layout.addWidget(icon_lbl)

        # Action count badge
        act_count = len(mode.actions)
        act_badge = QLabel(f"⚡ {act_count} Step{'s' if act_count != 1 else ''}")
        act_badge.setProperty("class", "ActionBadge")
        top_layout.addWidget(act_badge)

        top_layout.addStretch()

        if mode.hotkey:
            hk_lbl = QLabel(mode.hotkey)
            hk_lbl.setProperty("class", "HotkeyPill")
            top_layout.addWidget(hk_lbl)

        main_layout.addLayout(top_layout)

        # Middle: Title & Description
        title_lbl = QLabel(mode.name)
        title_lbl.setProperty("class", "ModeTitle")
        main_layout.addWidget(title_lbl)

        desc_lbl = QLabel(mode.description or "No description provided.")
        desc_lbl.setProperty("class", "ModeDesc")
        desc_lbl.setWordWrap(True)
        desc_lbl.setMaximumHeight(36)
        main_layout.addWidget(desc_lbl)

        # Action Preview Pills (first 3 action types)
        if mode.actions:
            preview_layout = QHBoxLayout()
            preview_layout.setSpacing(4)
            for act in mode.actions[:3]:
                # Extract clean short name (e.g. process.launch -> Launch)
                act_type_short = act.type.split(".")[-1].replace("_", " ").title()
                p_lbl = QLabel(act_type_short)
                p_lbl.setProperty("class", "StepPill")
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

        self.run_btn = QPushButton("▶  RUN MODE")
        self.run_btn.setProperty("class", "PrimaryButton")
        self.run_btn.clicked.connect(lambda: self.run_requested.emit(self.mode.id))

        self.edit_btn = QPushButton("⚙ Edit")
        self.edit_btn.setProperty("class", "SecondaryButton")
        self.edit_btn.clicked.connect(lambda: self.edit_requested.emit(self.mode.id))

        self.more_btn = QPushButton("⋮")
        self.more_btn.setProperty("class", "SecondaryButton")
        self.more_btn.setFixedWidth(32)
        self.more_btn.clicked.connect(self._show_context_menu)

        btn_layout.addWidget(self.run_btn, stretch=3)
        btn_layout.addWidget(self.edit_btn, stretch=2)
        btn_layout.addWidget(self.more_btn)

        main_layout.addLayout(btn_layout)

    def _show_context_menu(self) -> None:
        menu = QMenu(self)
        menu.setStyleSheet("""
            QMenu { background-color: #1e293b; color: #f8fafc; border: 1px solid #334155; border-radius: 8px; padding: 4px; }
            QMenu::item { padding: 6px 16px; border-radius: 4px; }
            QMenu::item:selected { background-color: #0284c7; color: #ffffff; }
        """)

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
