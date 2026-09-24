import glob
import os
import sys
import winreg
from pathlib import Path
from typing import List, Tuple

from PySide6.QtCore import Qt
from PySide6.QtWidgets import (
    QCheckBox,
    QDialog,
    QFileDialog,
    QFrame,
    QHBoxLayout,
    QLabel,
    QLineEdit,
    QPushButton,
    QScrollArea,
    QVBoxLayout,
    QWidget,
)

from app.models.action import ActionConfig
from app.windows.processes import ProcessManager


class AppPickerDialog(QDialog):
    """Dialog allowing users to batch select and import multiple apps/shortcuts into a mode."""

    def __init__(self, current_mode_name: str = "", parent=None):
        super().__init__(parent)
        self.setWindowTitle("Batch Add Application Shortcuts")
        self.setMinimumWidth(560)
        self.setMinimumHeight(480)
        self.setStyleSheet("QDialog { background-color: #000000; color: #f8fafc; }")

        self.selected_apps: List[Tuple[str, str]] = []  # (display_name, path_or_key)

        main_layout = QVBoxLayout(self)
        main_layout.setContentsMargins(22, 22, 22, 22)
        main_layout.setSpacing(16)

        # Header
        title_lbl = QLabel("Add Apps to Automation Sequence")
        title_lbl.setStyleSheet("font-size: 20px; font-weight: 800; color: #f8fafc;")

        desc_lbl = QLabel(
            "Select from discovered system apps, dedicated shortcuts, or browse files to add them as step-by-step launch actions."
        )
        desc_lbl.setStyleSheet("color: #94a3b8; font-size: 12px; line-height: 1.4;")
        desc_lbl.setWordWrap(True)

        main_layout.addWidget(title_lbl)
        main_layout.addWidget(desc_lbl)

        # Browse files button bar
        browse_bar = QHBoxLayout()
        browse_lbl = QLabel("Don't see your app?")
        browse_lbl.setStyleSheet("color: #64748b; font-size: 12px;")

        self.browse_files_btn = QPushButton("📁 Browse EXEs / Shortcuts...")
        self.browse_files_btn.setProperty("class", "SecondaryButton")
        self.browse_files_btn.clicked.connect(self._on_browse_files)

        browse_bar.addWidget(browse_lbl)
        browse_bar.addStretch()
        browse_bar.addWidget(self.browse_files_btn)

        main_layout.addLayout(browse_bar)

        # Discovered Apps Checklist Container
        scroll = QScrollArea()
        scroll.setWidgetResizable(True)
        scroll.setStyleSheet("QScrollArea { border: 1px solid #1c1c1c; border-radius: 10px; background-color: #080808; }")

        self.scroll_content = QWidget()
        self.scroll_layout = QVBoxLayout(self.scroll_content)
        self.scroll_layout.setContentsMargins(14, 14, 14, 14)
        self.scroll_layout.setSpacing(10)
        scroll.setWidget(self.scroll_content)

        main_layout.addWidget(scroll, stretch=1)

        # Populate discovered and dedicated apps
        self.checkboxes: List[Tuple[QCheckBox, str, str]] = []  # (checkbox, name, path)
        self._populate_available_apps()

        # Bottom Action Bar
        btn_layout = QHBoxLayout()
        
        self.count_lbl = QLabel("0 apps selected")
        self.count_lbl.setStyleSheet("color: #38bdf8; font-size: 12px; font-weight: 600;")

        self.cancel_btn = QPushButton("Cancel")
        self.cancel_btn.setProperty("class", "SecondaryButton")
        self.cancel_btn.clicked.connect(self.reject)

        self.add_btn = QPushButton("🚀 Add Apps to Sequence")
        self.add_btn.setProperty("class", "PrimaryButton")
        self.add_btn.clicked.connect(self._on_confirm_add)

        btn_layout.addWidget(self.count_lbl)
        btn_layout.addStretch()
        btn_layout.addWidget(self.cancel_btn)
        btn_layout.addWidget(self.add_btn)

        main_layout.addLayout(btn_layout)

    def _populate_available_apps(self) -> None:
        """Scan DEDICATED_MODES and well-known system locations."""
        discovered: List[Tuple[str, str, str]] = []  # (Category, Name, Path)

        # 1. DEDICATED_MODES shortcuts
        candidate_dirs = [
            Path(__file__).resolve().parent.parent.parent.parent / "DEDICATED_MODES",
            Path(sys.executable).parent / "DEDICATED_MODES",
            Path(sys.executable).parent.parent / "DEDICATED_MODES",
            Path.cwd() / "DEDICATED_MODES",
        ]
        if getattr(sys, "frozen", False) and hasattr(sys, "_MEIPASS"):
            candidate_dirs.append(Path(sys._MEIPASS) / "DEDICATED_MODES")

        for dedicated_dir in candidate_dirs:
            if dedicated_dir.exists():
                for root, _, files in os.walk(dedicated_dir):
                    folder_name = os.path.basename(root)
                    for f in files:
                        if f.endswith((".lnk", ".exe", ".url")):
                            name = os.path.splitext(f)[0]
                            full_path = os.path.join(root, f)
                            if not any(d[2] == full_path for d in discovered):
                                discovered.append((f"DEDICATED_MODES ({folder_name})", name, full_path))


        # 2. Popular Games & Apps
        well_known = [
            ("Steam", "steam"),
            ("Discord", "discord"),
            ("Spotify", "spotify"),
            ("VS Code", "code"),
            ("FL Studio", "fl_studio"),
            ("Google Chrome", "chrome"),
            ("Microsoft Edge", "msedge"),
        ]

        # Add Valorant specifically if found
        riot_valorant = r"C:\Riot Games\VALORANT\live\VALORANT.exe"
        if os.path.exists(riot_valorant):
            discovered.append(("System Games", "VALORANT", riot_valorant))

        for display_name, app_key in well_known:
            path = ProcessManager.auto_discover_app_path(app_key)
            if path:
                # Avoid duplicate names
                if not any(d[1].lower() == display_name.lower() for d in discovered):
                    discovered.append(("Discovered System Apps", display_name, path))

        if not discovered:
            empty_lbl = QLabel("No pre-configured apps discovered automatically. Use 'Browse EXEs / Shortcuts' above.")
            empty_lbl.setStyleSheet("color: #64748b; font-style: italic; padding: 12px;")
            self.scroll_layout.addWidget(empty_lbl)
            return

        # Group by category
        categories = {}
        for cat, name, path in discovered:
            categories.setdefault(cat, []).append((name, path))

        for cat_name, app_list in categories.items():
            cat_lbl = QLabel(cat_name)
            cat_lbl.setStyleSheet("font-weight: 700; color: #38bdf8; font-size: 13px; margin-top: 6px;")
            self.scroll_layout.addWidget(cat_lbl)

            for app_name, app_path in app_list:
                cb = QCheckBox(f"{app_name}  ({os.path.basename(app_path)})")
                cb.setToolTip(app_path)
                cb.setStyleSheet("QCheckBox { font-size: 13px; color: #f8fafc; padding: 4px; }")
                cb.stateChanged.connect(self._update_selected_count)
                self.scroll_layout.addWidget(cb)
                self.checkboxes.append((cb, app_name, app_path))

    def _on_browse_files(self) -> None:
        files, _ = QFileDialog.getOpenFileNames(
            self,
            "Select Executables or Shortcuts",
            "",
            "Applications & Shortcuts (*.exe *.lnk *.url);;Executables (*.exe);;Shortcuts (*.lnk);;All Files (*.*)",
        )
        if files:
            for fpath in files:
                name = os.path.splitext(os.path.basename(fpath))[0].title()
                cb = QCheckBox(f"{name}  ({os.path.basename(fpath)})")
                cb.setChecked(True)
                cb.setToolTip(fpath)
                cb.setStyleSheet("QCheckBox { font-size: 13px; color: #10b981; padding: 4px; font-weight: 600; }")
                cb.stateChanged.connect(self._update_selected_count)
                self.scroll_layout.insertWidget(0, cb)
                self.checkboxes.insert(0, (cb, name, fpath))
            self._update_selected_count()

    def _update_selected_count(self) -> None:
        count = sum(1 for cb, _, _ in self.checkboxes if cb.isChecked())
        self.count_lbl.setText(f"{count} app{'s' if count != 1 else ''} selected")

    def _on_confirm_add(self) -> None:
        self.selected_apps = [(name, path) for cb, name, path in self.checkboxes if cb.isChecked()]
        if self.selected_apps:
            self.accept()
        else:
            self.reject()

    def get_action_configs(self) -> List[ActionConfig]:
        """Convert selected apps into process.launch ActionConfig objects."""
        actions = []
        for name, path in self.selected_apps:
            actions.append(
                ActionConfig(
                    type="process.launch",
                    name=f"Launch {name}",
                    params={"application": path},
                    on_failure="continue",
                )
            )
        return actions
