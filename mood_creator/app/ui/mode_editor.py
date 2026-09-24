from typing import List, Optional
from PySide6.QtCore import Qt, Signal
from PySide6.QtWidgets import (
    QFileDialog,
    QFormLayout,
    QFrame,
    QHBoxLayout,
    QLabel,
    QLineEdit,
    QMessageBox,
    QPushButton,
    QScrollArea,
    QVBoxLayout,
    QWidget,
)

from app.models.action import ActionConfig
from app.models.mode import Mode
from app.ui.action_editor import ActionEditorDialog
from app.ui.widgets.action_row import ActionRowWidget
from app.ui.widgets.app_picker_dialog import AppPickerDialog
from app.ui.widgets.hotkey_input import HotkeyInputWidget


class ModeEditorView(QWidget):
    """Full view for creating and editing Modes."""

    save_requested = Signal(Mode)
    delete_requested = Signal(str)  # mode_id
    export_requested = Signal(str)  # mode_id
    cancelled = Signal()

    EMOJI_PRESETS = ["🎸", "🎮", "💻", "🎹", "📚", "☕", "⚡", "🚀", "🎧", "🎨", "🛡️", "🔥"]

    def __init__(self, parent=None):
        super().__init__(parent)
        self.current_mode_id: Optional[str] = None
        self.actions_list: List[ActionConfig] = []

        main_layout = QVBoxLayout(self)
        main_layout.setContentsMargins(24, 24, 24, 24)
        main_layout.setSpacing(20)

        # Header Title
        self.header_title = QLabel("Edit Mode")
        self.header_title.setStyleSheet("font-size: 24px; font-weight: 800; color: #f8fafc; letter-spacing: -0.5px;")
        main_layout.addWidget(self.header_title)

        # Metadata Form Section
        meta_frame = QFrame()
        meta_frame.setStyleSheet("QFrame { background-color: #080808; border: 1px solid #181818; border-radius: 12px; padding: 18px; }")
        meta_form = QFormLayout(meta_frame)
        meta_form.setSpacing(14)

        self.id_input = QLineEdit()
        self.id_input.setPlaceholderText("e.g. guitar_practice_mode (unique identifier)")

        self.name_input = QLineEdit()
        self.name_input.setPlaceholderText("Display Name (e.g. Gaming Mode)")

        self.desc_input = QLineEdit()
        self.desc_input.setPlaceholderText("Short description of what this mode automates")

        # Icon input + Quick Emoji Selector
        icon_layout = QHBoxLayout()
        self.icon_input = QLineEdit()
        self.icon_input.setPlaceholderText("Emoji or icon (e.g. 🎮)")
        self.icon_input.setFixedWidth(80)

        icon_layout.addWidget(self.icon_input)
        icon_layout.addWidget(QLabel("Quick Pick:"))

        for emoji in self.EMOJI_PRESETS:
            ebtn = QPushButton(emoji)
            ebtn.setFixedSize(30, 30)
            ebtn.setProperty("class", "SecondaryButton")
            ebtn.clicked.connect(lambda _, e=emoji: self.icon_input.setText(e))
            icon_layout.addWidget(ebtn)

        icon_layout.addStretch()

        # Hotkey recorder widget
        self.hotkey_widget = HotkeyInputWidget()

        meta_form.addRow("Mode ID:", self.id_input)
        meta_form.addRow("Display Name:", self.name_input)
        meta_form.addRow("Description:", self.desc_input)
        meta_form.addRow("Icon / Emoji:", icon_layout)
        meta_form.addRow("Global Hotkey:", self.hotkey_widget)

        main_layout.addWidget(meta_frame)

        # Actions Header
        act_header = QHBoxLayout()
        act_lbl = QLabel("Actions Sequence")
        act_lbl.setStyleSheet("font-size: 18px; font-weight: 700; color: #f8fafc;")

        self.act_count_lbl = QLabel("(0 Steps)")
        self.act_count_lbl.setStyleSheet("color: #94a3b8; font-size: 14px; margin-top: 2px;")

        self.batch_apps_btn = QPushButton("📱 Add App Shortcuts...")
        self.batch_apps_btn.setProperty("class", "SecondaryButton")
        self.batch_apps_btn.clicked.connect(self._on_batch_add_apps)

        self.add_act_btn = QPushButton("+ Add Action Step")
        self.add_act_btn.setProperty("class", "PrimaryButton")
        self.add_act_btn.clicked.connect(self._on_add_action)

        act_header.addWidget(act_lbl)
        act_header.addWidget(self.act_count_lbl)
        act_header.addStretch()
        act_header.addWidget(self.batch_apps_btn)
        act_header.addWidget(self.add_act_btn)

        main_layout.addLayout(act_header)

        # Actions Scroll Container
        scroll = QScrollArea()
        scroll.setWidgetResizable(True)
        scroll.setStyleSheet("QScrollArea { border: none; background: transparent; }")

        self.actions_container = QWidget()
        self.actions_layout = QVBoxLayout(self.actions_container)
        self.actions_layout.setContentsMargins(0, 0, 0, 0)
        self.actions_layout.setSpacing(10)
        scroll.setWidget(self.actions_container)

        main_layout.addWidget(scroll, stretch=1)

        # Bottom Bar: Delete, Export, Cancel, Save
        bottom_layout = QHBoxLayout()
        bottom_layout.setSpacing(12)

        self.del_btn = QPushButton("🗑 Delete Mode")
        self.del_btn.setProperty("class", "DangerButton")
        self.del_btn.clicked.connect(self._on_delete_clicked)

        self.export_btn = QPushButton("📤 Export JSON")
        self.export_btn.setProperty("class", "SecondaryButton")
        self.export_btn.clicked.connect(self._on_export_clicked)

        self.cancel_btn = QPushButton("Cancel")
        self.cancel_btn.setProperty("class", "SecondaryButton")
        self.cancel_btn.clicked.connect(self.cancelled.emit)

        self.save_btn = QPushButton("💾 Save Mode")
        self.save_btn.setProperty("class", "PrimaryButton")
        self.save_btn.clicked.connect(self._on_save_clicked)

        bottom_layout.addWidget(self.del_btn)
        bottom_layout.addWidget(self.export_btn)
        bottom_layout.addStretch()
        bottom_layout.addWidget(self.cancel_btn)
        bottom_layout.addWidget(self.save_btn)

        main_layout.addLayout(bottom_layout)

    def load_mode(self, mode: Optional[Mode] = None) -> None:
        """Load mode into editor form."""
        if mode:
            self.current_mode_id = mode.id
            self.header_title.setText(f"Edit Mode: {mode.name}")
            self.id_input.setText(mode.id)
            self.id_input.setEnabled(False)  # Lock ID when editing existing mode
            self.name_input.setText(mode.name)
            self.desc_input.setText(mode.description)
            self.icon_input.setText(mode.icon)
            self.hotkey_widget.setText(mode.hotkey or "")
            self.actions_list = [ActionConfig.model_validate(a.model_dump()) for a in mode.actions]
            self.del_btn.setVisible(True)
            self.export_btn.setVisible(True)
        else:
            self.current_mode_id = None
            self.header_title.setText("Create New Mode")
            self.id_input.setText("")
            self.id_input.setEnabled(True)
            self.name_input.setText("")
            self.desc_input.setText("")
            self.icon_input.setText("⚡")
            self.hotkey_widget.setText("")
            self.actions_list = []
            self.del_btn.setVisible(False)
            self.export_btn.setVisible(False)

        self.refresh_actions_list()

    def refresh_actions_list(self) -> None:
        """Render action row widgets."""
        while self.actions_layout.count():
            item = self.actions_layout.takeAt(0)
            if item.widget():
                item.widget().deleteLater()

        self.act_count_lbl.setText(f"({len(self.actions_list)} Step{'s' if len(self.actions_list) != 1 else ''})")

        if not self.actions_list:
            empty_lbl = QLabel("No actions added yet. Click '📱 Add App Shortcuts...' or '+ Add Action Step' above.")
            empty_lbl.setStyleSheet("color: #64748b; padding: 24px; font-style: italic; background: #080808; border: 1px dashed #181818; border-radius: 8px;")
            empty_lbl.setAlignment(Qt.AlignmentFlag.AlignCenter)
            self.actions_layout.addWidget(empty_lbl)
            return

        total = len(self.actions_list)
        for idx, act in enumerate(self.actions_list):
            row = ActionRowWidget(
                index=idx,
                action_config=act,
                is_first=(idx == 0),
                is_last=(idx == total - 1),
            )
            row.edit_clicked.connect(self._on_edit_action)
            row.move_up_clicked.connect(self._on_move_up)
            row.move_down_clicked.connect(self._on_move_down)
            row.duplicate_clicked.connect(self._on_duplicate_action)
            row.delete_clicked.connect(self._on_delete_action)

            self.actions_layout.addWidget(row)

    def _on_batch_add_apps(self) -> None:
        dlg = AppPickerDialog(current_mode_name=self.name_input.text(), parent=self)
        if dlg.exec() == AppPickerDialog.Accepted:
            new_actions = dlg.get_action_configs()
            self.actions_list.extend(new_actions)
            self.refresh_actions_list()

    def _on_add_action(self) -> None:
        dlg = ActionEditorDialog(parent=self)
        if dlg.exec() == ActionEditorDialog.Accepted:
            cfg = dlg.get_action_config()
            self.actions_list.append(cfg)
            self.refresh_actions_list()

    def _on_edit_action(self, idx: int) -> None:
        if 0 <= idx < len(self.actions_list):
            dlg = ActionEditorDialog(action_config=self.actions_list[idx], parent=self)
            if dlg.exec() == ActionEditorDialog.Accepted:
                self.actions_list[idx] = dlg.get_action_config()
                self.refresh_actions_list()

    def _on_move_up(self, idx: int) -> None:
        if idx > 0:
            self.actions_list[idx], self.actions_list[idx - 1] = self.actions_list[idx - 1], self.actions_list[idx]
            self.refresh_actions_list()

    def _on_move_down(self, idx: int) -> None:
        if idx < len(self.actions_list) - 1:
            self.actions_list[idx], self.actions_list[idx + 1] = self.actions_list[idx + 1], self.actions_list[idx]
            self.refresh_actions_list()

    def _on_duplicate_action(self, idx: int) -> None:
        if 0 <= idx < len(self.actions_list):
            dup = ActionConfig.model_validate(self.actions_list[idx].model_dump())
            self.actions_list.insert(idx + 1, dup)
            self.refresh_actions_list()

    def _on_delete_action(self, idx: int) -> None:
        if 0 <= idx < len(self.actions_list):
            del self.actions_list[idx]
            self.refresh_actions_list()

    def _on_save_clicked(self) -> None:
        mode_id = self.id_input.text().strip()
        name = self.name_input.text().strip()

        if not mode_id or not name:
            QMessageBox.warning(self, "Validation Error", "Mode ID and Display Name are required!")
            return

        mode = Mode(
            schema_version=1,
            id=mode_id,
            name=name,
            description=self.desc_input.text().strip(),
            icon=self.icon_input.text().strip() or "⚡",
            hotkey=self.hotkey_widget.text() or None,
            enabled=True,
            actions=self.actions_list,
        )
        self.save_requested.emit(mode)

    def _on_export_clicked(self) -> None:
        if self.current_mode_id:
            self.export_requested.emit(self.current_mode_id)

    def _on_delete_clicked(self) -> None:
        if self.current_mode_id:
            res = QMessageBox.question(
                self,
                "Confirm Delete",
                f"Are you sure you want to delete mode '{self.name_input.text()}'?",
                QMessageBox.Yes | QMessageBox.No,
            )
            if res == QMessageBox.Yes:
                self.delete_requested.emit(self.current_mode_id)
