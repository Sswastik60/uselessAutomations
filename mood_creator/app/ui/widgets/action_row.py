from PySide6.QtCore import Qt, Signal
from PySide6.QtWidgets import QFrame, QHBoxLayout, QLabel, QPushButton
from app.models.action import ActionConfig


class ActionRowWidget(QFrame):
    """Row widget representing an action item in the Mode Editor action sequence."""

    edit_clicked = Signal(int)
    move_up_clicked = Signal(int)
    move_down_clicked = Signal(int)
    duplicate_clicked = Signal(int)
    delete_clicked = Signal(int)

    CATEGORY_COLORS = {
        "process": "#0284c7",
        "audio": "#10b981",
        "window": "#a855f7",
        "keyboard": "#f59e0b",
        "mouse": "#ec4899",
        "wait": "#64748b",
        "file": "#3b82f6",
        "condition": "#eab308",
        "notification": "#06b6d4",
        "midi": "#84cc16",
    }

    def __init__(self, index: int, action_config: ActionConfig, is_first: bool = False, is_last: bool = False, parent=None):
        super().__init__(parent)
        self.index = index
        self.action_config = action_config

        category = action_config.type.split(".")[0].lower() if "." in action_config.type else "custom"
        cat_color = self.CATEGORY_COLORS.get(category, "#64748b")

        self.setStyleSheet(f"""
            QFrame {{
                background-color: #111827;
                border: 1px solid #1f2937;
                border-left: 4px solid {cat_color};
                border-radius: 8px;
                padding: 4px;
            }}
            QFrame:hover {{
                border-color: #374151;
                border-left-color: {cat_color};
                background-color: #172033;
            }}
        """)

        layout = QHBoxLayout(self)
        layout.setContentsMargins(10, 8, 10, 8)
        layout.setSpacing(10)

        # Step badge
        step_lbl = QLabel(f"Step {index + 1}")
        step_lbl.setStyleSheet("font-weight: 700; color: #94a3b8; font-size: 12px;")
        layout.addWidget(step_lbl)

        # Type badge
        type_lbl = QLabel(action_config.type)
        type_lbl.setStyleSheet(f"""
            background-color: #0b0f19;
            border: 1px solid #1f2937;
            border-radius: 4px;
            color: {cat_color};
            padding: 2px 8px;
            font-size: 11px;
            font-weight: 700;
            font-family: 'Consolas', 'Segoe UI Mono', monospace;
        """)
        layout.addWidget(type_lbl)

        # Action Name & Summary
        name_str = action_config.get_display_name()
        params_summary = ", ".join(f"{k}={v}" for k, v in action_config.params.items() if v is not None and v != "")
        if len(params_summary) > 60:
            params_summary = params_summary[:57] + "..."

        summary_lbl = QLabel(f"<b>{name_str}</b>" + (f" <span style='color: #64748b;'>({params_summary})</span>" if params_summary else ""))
        summary_lbl.setTextFormat(Qt.TextFormat.RichText)
        layout.addWidget(summary_lbl, stretch=1)

        # Failure policy pill
        if action_config.on_failure != "stop":
            pol_lbl = QLabel(f"on_error: {action_config.on_failure}")
            pol_lbl.setStyleSheet("color: #f59e0b; font-size: 11px; font-weight: 600; background: #1e293b; padding: 2px 6px; border-radius: 4px;")
            layout.addWidget(pol_lbl)

        # Control Action Buttons
        self.up_btn = QPushButton("▲")
        self.up_btn.setFixedSize(28, 28)
        self.up_btn.setToolTip("Move Up")
        self.up_btn.setProperty("class", "SecondaryButton")
        self.up_btn.setEnabled(not is_first)
        self.up_btn.clicked.connect(lambda: self.move_up_clicked.emit(self.index))

        self.down_btn = QPushButton("▼")
        self.down_btn.setFixedSize(28, 28)
        self.down_btn.setToolTip("Move Down")
        self.down_btn.setProperty("class", "SecondaryButton")
        self.down_btn.setEnabled(not is_last)
        self.down_btn.clicked.connect(lambda: self.move_down_clicked.emit(self.index))

        self.edit_btn = QPushButton("✎")
        self.edit_btn.setFixedSize(28, 28)
        self.edit_btn.setToolTip("Edit Action Parameters")
        self.edit_btn.setProperty("class", "SecondaryButton")
        self.edit_btn.clicked.connect(lambda: self.edit_clicked.emit(self.index))

        self.dup_btn = QPushButton("❐")
        self.dup_btn.setFixedSize(28, 28)
        self.dup_btn.setToolTip("Duplicate Action")
        self.dup_btn.setProperty("class", "SecondaryButton")
        self.dup_btn.clicked.connect(lambda: self.duplicate_clicked.emit(self.index))

        self.del_btn = QPushButton("✕")
        self.del_btn.setFixedSize(28, 28)
        self.del_btn.setToolTip("Delete Action")
        self.del_btn.setStyleSheet("color: #ef4444; border-color: #7f1d1d;")
        self.del_btn.setProperty("class", "SecondaryButton")
        self.del_btn.clicked.connect(lambda: self.delete_clicked.emit(self.index))

        layout.addWidget(self.up_btn)
        layout.addWidget(self.down_btn)
        layout.addWidget(self.edit_btn)
        layout.addWidget(self.dup_btn)
        layout.addWidget(self.del_btn)
