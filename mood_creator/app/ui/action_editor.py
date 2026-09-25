from typing import Any, Dict, Optional
from PySide6.QtCore import Qt
from PySide6.QtWidgets import (
    QCheckBox,
    QComboBox,
    QDialog,
    QFileDialog,
    QFormLayout,
    QHBoxLayout,
    QLabel,
    QLineEdit,
    QPushButton,
    QSpinBox,
    QVBoxLayout,
)

from app.core.action_registry import action_registry
from app.models.action import ActionConfig


class ActionEditorDialog(QDialog):
    """Dialog for configuring or editing an individual Action parameters."""

    def __init__(self, action_config: Optional[ActionConfig] = None, parent=None):
        super().__init__(parent)
        self.setWindowTitle("Action Configurator")
        self.setMinimumWidth(540)

        self.action_config = action_config
        self.param_inputs: Dict[str, Any] = {}

        main_layout = QVBoxLayout(self)
        main_layout.setContentsMargins(20, 20, 20, 20)
        main_layout.setSpacing(18)

        # Form layout
        self.form_layout = QFormLayout()
        self.form_layout.setSpacing(12)

        # Action Type selector
        self.type_combo = QComboBox()
        self._populate_action_types()
        self.type_combo.currentIndexChanged.connect(self._on_action_type_changed)
        self.form_layout.addRow("Action Type:", self.type_combo)

        # Custom Action Name
        self.name_input = QLineEdit()
        self.name_input.setPlaceholderText("Optional custom step title (e.g. Launch Practice DAW)")
        self.form_layout.addRow("Custom Label:", self.name_input)

        # On Failure Policy selector
        self.failure_combo = QComboBox()
        self.failure_combo.addItem("Stop Mode Execution (default)", "stop")
        self.failure_combo.addItem("Continue to Next Action Step", "continue")
        self.failure_combo.addItem("Retry Action Step (1 retry attempt)", "retry")
        self.form_layout.addRow("Failure Policy:", self.failure_combo)

        # Dynamic Parameters Container Layout
        self.params_container = QVBoxLayout()
        self.params_form = QFormLayout()
        self.params_form.setSpacing(10)
        self.params_container.addLayout(self.params_form)
        
        param_section_lbl = QLabel("Action Parameters")
        param_section_lbl.setStyleSheet("font-weight: 700; color: #38bdf8; margin-top: 6px;")
        
        main_layout.addLayout(self.form_layout)
        main_layout.addWidget(param_section_lbl)
        main_layout.addLayout(self.params_container)

        # Action Buttons
        btn_layout = QHBoxLayout()
        btn_layout.addStretch()

        self.save_btn = QPushButton("💾 Save Action")
        self.save_btn.setProperty("class", "PrimaryButton")
        self.save_btn.clicked.connect(self.accept)

        self.cancel_btn = QPushButton("Cancel")
        self.cancel_btn.setProperty("class", "SecondaryButton")
        self.cancel_btn.clicked.connect(self.reject)

        btn_layout.addWidget(self.cancel_btn)
        btn_layout.addWidget(self.save_btn)

        main_layout.addLayout(btn_layout)

        # Populate if editing existing config
        if self.action_config:
            self._load_existing_config(self.action_config)
        else:
            self._on_action_type_changed()

    def _populate_action_types(self) -> None:
        all_actions = action_registry.list_actions()
        # Sort by category then display_name
        all_actions.sort(key=lambda x: (x["category"], x["display_name"]))

        for meta in all_actions:
            label = f"[{meta['category']}]  {meta['display_name']} ({meta['type']})"
            self.type_combo.addItem(label, meta['type'])

    def _on_action_type_changed(self) -> None:
        action_type = self.type_combo.currentData()
        if not action_type:
            return

        # Clear existing dynamic fields
        while self.params_form.count():
            item = self.params_form.takeAt(0)
            if item.widget():
                item.widget().deleteLater()
        self.param_inputs.clear()

        # Build fields based on param_schema
        meta_list = [m for m in action_registry.list_actions() if m["type"] == action_type]
        if not meta_list:
            return
        schema = meta_list[0].get("param_schema", {})

        for field_key, field_spec in schema.items():
            field_type = field_spec.get("type", "string")
            field_label = field_spec.get("label", field_key)
            default_val = field_spec.get("default")
            placeholder = field_spec.get("placeholder")

            if field_type == "boolean":
                inp = QCheckBox()
                if default_val is not None:
                    inp.setChecked(bool(default_val))
                self.param_inputs[field_key] = inp
                self.params_form.addRow(f"{field_label}:", inp)
            elif field_type == "number":
                inp = QSpinBox()
                inp.setRange(0, 99999)
                if default_val is not None:
                    inp.setValue(int(default_val))
                self.param_inputs[field_key] = inp
                self.params_form.addRow(f"{field_label}:", inp)
            else:
                # Check if window title selector parameter
                if field_key.lower() in ("title", "window_title", "window"):
                    h_box = QHBoxLayout()
                    inp = QLineEdit()
                    if default_val is not None:
                        inp.setText(str(default_val))
                    if placeholder:
                        inp.setPlaceholderText(placeholder)

                    pick_btn = QPushButton("🪟 Select Window...")
                    pick_btn.setProperty("class", "SecondaryButton")
                    pick_btn.clicked.connect(lambda _, field=inp: self._select_running_window(field))

                    h_box.addWidget(inp, stretch=1)
                    h_box.addWidget(pick_btn)

                    self.param_inputs[field_key] = inp
                    self.params_form.addRow(f"{field_label}:", h_box)

                # Check if file path parameter
                elif any(kw in field_key.lower() for kw in ["path", "file", "source", "destination", "directory", "executable", "application"]):
                    h_box = QHBoxLayout()
                    inp = QLineEdit()
                    if default_val is not None:
                        inp.setText(str(default_val))
                    if placeholder:
                        inp.setPlaceholderText(placeholder)

                    browse_btn = QPushButton("Browse...")
                    browse_btn.setProperty("class", "SecondaryButton")
                    browse_btn.clicked.connect(lambda _, field=inp, key=field_key: self._browse_path(field, key))

                    h_box.addWidget(inp, stretch=1)
                    h_box.addWidget(browse_btn)

                    self.param_inputs[field_key] = inp
                    self.params_form.addRow(f"{field_label}:", h_box)
                else:
                    inp = QLineEdit()
                    if default_val is not None:
                        inp.setText(str(default_val))
                    if placeholder:
                        inp.setPlaceholderText(placeholder)
                    self.param_inputs[field_key] = inp
                    self.params_form.addRow(f"{field_label}:", inp)

    def _select_running_window(self, line_edit: QLineEdit) -> None:
        """Display a popup menu of currently active visible windows to auto-fill target title."""
        from app.windows.windows import WindowManager
        from PySide6.QtWidgets import QMenu
        from PySide6.QtGui import QCursor

        menu = QMenu(self)
        menu.setStyleSheet(
            "QMenu { background: #1e293b; color: #f8fafc; border: 1px solid #334155; padding: 4px; } "
            "QMenu::item { padding: 6px 14px; border-radius: 4px; } "
            "QMenu::item:selected { background: #38bdf8; color: #0f172a; }"
        )

        act_last = menu.addAction("⚡ [Last Launched App / Active Window]")
        act_last.triggered.connect(lambda: line_edit.setText(""))
        menu.addSeparator()

        windows = WindowManager.get_all_visible_windows()
        seen = set()
        count = 0
        for hwnd, title, pname in windows:
            if title and pname:
                label = f"{title[:45]} ({pname})"
                val = pname.removesuffix(".exe")
            elif title:
                label = title[:50]
                val = title
            elif pname:
                label = pname
                val = pname.removesuffix(".exe")
            else:
                continue

            if val in seen:
                continue
            seen.add(val)

            act = menu.addAction(f"🪟 {label}")
            act.triggered.connect(lambda checked=False, v=val: line_edit.setText(v))
            count += 1
            if count >= 30:
                break

        menu.exec(QCursor.pos())

    def _browse_path(self, line_edit: QLineEdit, field_key: str) -> None:
        if "dir" in field_key.lower() or "folder" in field_key.lower():
            path = QFileDialog.getExistingDirectory(self, f"Select Directory for {field_key}")
        elif any(kw in field_key.lower() for kw in ["app", "executable", "process"]):
            path, _ = QFileDialog.getOpenFileName(
                self,
                f"Select Application for {field_key}",
                "",
                "Executables & Shortcuts (*.exe *.lnk *.bat *.cmd);;All Files (*.*)",
            )
        else:
            path, _ = QFileDialog.getOpenFileName(self, f"Select File for {field_key}", "", "All Files (*.*)")
        if path:
            line_edit.setText(path)

    def _load_existing_config(self, cfg: ActionConfig) -> None:
        index = self.type_combo.findData(cfg.type)
        if index >= 0:
            self.type_combo.setCurrentIndex(index)

        self.name_input.setText(cfg.name or "")
        
        fail_idx = self.failure_combo.findData(cfg.on_failure)
        if fail_idx >= 0:
            self.failure_combo.setCurrentIndex(fail_idx)

        # Set parameter values
        for key, widget in self.param_inputs.items():
            if key in cfg.params:
                val = cfg.params[key]
                if isinstance(widget, QCheckBox):
                    widget.setChecked(bool(val))
                elif isinstance(widget, QSpinBox):
                    widget.setValue(int(val))
                elif isinstance(widget, QLineEdit):
                    if isinstance(val, list):
                        widget.setText(" ".join(str(x) for x in val))
                    else:
                        widget.setText(str(val))

    def get_action_config(self) -> ActionConfig:
        action_type = self.type_combo.currentData()
        name = self.name_input.text().strip() or None
        on_failure = self.failure_combo.currentData()

        params = {}
        for key, widget in self.param_inputs.items():
            if isinstance(widget, QCheckBox):
                params[key] = widget.isChecked()
            elif isinstance(widget, QSpinBox):
                params[key] = widget.value()
            elif isinstance(widget, QLineEdit):
                params[key] = widget.text().strip()

        return ActionConfig(
            type=action_type,
            name=name,
            params=params,
            on_failure=on_failure,
        )
