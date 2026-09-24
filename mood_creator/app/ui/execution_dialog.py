from PySide6.QtCore import Qt, QTimer, Signal
from PySide6.QtWidgets import (
    QDialog,
    QHBoxLayout,
    QLabel,
    QProgressBar,
    QPushButton,
    QScrollArea,
    QVBoxLayout,
    QWidget,
)

from app.models.action_result import ActionResult
from app.ui.design.tokens import DarkPalette, Radius, Spacing


class ExecutionDialog(QDialog):
    """Refined AMOLED execution modal displaying real-time automation progress."""

    cancel_requested = Signal()

    def __init__(self, mode_name: str, parent=None):
        super().__init__(parent)
        self.setWindowTitle(f"Running {mode_name}")
        self.setMinimumWidth(520)
        self.setMinimumHeight(420)
        self.setWindowFlags(self.windowFlags() & ~Qt.WindowContextHelpButtonHint)

        self.setStyleSheet(
            f"""
            QDialog {{
                background-color: {DarkPalette.BG_PRIMARY};
                border: 1px solid {DarkPalette.BORDER_SUBTLE};
                border-radius: {Radius.LG}px;
            }}
            QLabel {{
                color: {DarkPalette.TEXT_PRIMARY};
                font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif;
            }}
            QProgressBar {{
                background-color: {DarkPalette.SURFACE_PRIMARY};
                border: 1px solid {DarkPalette.BORDER_SUBTLE};
                border-radius: 6px;
                height: 8px;
                text-align: center;
                color: transparent;
            }}
            QProgressBar::chunk {{
                background: qlineargradient(x1:0, y1:0, x2:1, y2:0, stop:0 #38bdf8, stop:1 #818cf8);
                border-radius: 5px;
            }}
            QScrollArea {{
                border: 1px solid {DarkPalette.BORDER_SUBTLE};
                border-radius: 10px;
                background-color: {DarkPalette.SURFACE_PRIMARY};
            }}
            """
        )

        main_layout = QVBoxLayout(self)
        main_layout.setContentsMargins(Spacing.XL, Spacing.XL, Spacing.XL, Spacing.XL)
        main_layout.setSpacing(Spacing.MD)

        # Header Title
        self.title_lbl = QLabel(f"Executing {mode_name}...")
        self.title_lbl.setStyleSheet(f"font-size: 20px; font-weight: 800; color: {DarkPalette.TEXT_PRIMARY}; letter-spacing: -0.3px;")
        main_layout.addWidget(self.title_lbl)

        # Status Subtitle
        self.status_lbl = QLabel("Initializing engine context...")
        self.status_lbl.setStyleSheet(f"color: {DarkPalette.TEXT_MUTED}; font-size: 13px;")
        main_layout.addWidget(self.status_lbl)

        # Progress Bar
        self.progress_bar = QProgressBar()
        self.progress_bar.setRange(0, 100)
        self.progress_bar.setValue(0)
        main_layout.addWidget(self.progress_bar)

        # Action Steps List Scroll Area
        self.scroll = QScrollArea()
        self.scroll.setWidgetResizable(True)

        self.steps_container = QWidget()
        self.steps_container.setStyleSheet("background: transparent;")
        self.steps_layout = QVBoxLayout(self.steps_container)
        self.steps_layout.setContentsMargins(12, 12, 12, 12)
        self.steps_layout.setSpacing(8)
        self.scroll.setWidget(self.steps_container)

        main_layout.addWidget(self.scroll, stretch=1)

        # Action Buttons
        btn_layout = QHBoxLayout()
        btn_layout.addStretch()

        self.cancel_btn = QPushButton("Cancel Execution")
        self.cancel_btn.setProperty("class", "DangerButton")
        self.cancel_btn.clicked.connect(self.cancel_requested.emit)

        self.done_btn = QPushButton("Done")
        self.done_btn.setProperty("class", "PrimaryButton")
        self.done_btn.setVisible(False)
        self.done_btn.clicked.connect(self.accept)

        btn_layout.addWidget(self.cancel_btn)
        btn_layout.addWidget(self.done_btn)

        main_layout.addLayout(btn_layout)

    def on_action_started(self, step_idx: int, total_steps: int, action_name: str) -> None:
        lbl = QLabel(f"⏳  Step {step_idx}/{total_steps}: {action_name}")
        lbl.setStyleSheet(
            f"""
            QLabel {{
                font-size: 13px;
                color: #38bdf8;
                font-weight: 600;
                padding: 8px 12px;
                background-color: rgba(56, 189, 248, 0.08);
                border: 1px solid rgba(56, 189, 248, 0.2);
                border-radius: 6px;
            }}
            """
        )
        self.steps_layout.addWidget(lbl)
        self.status_lbl.setText(f"Executing step {step_idx}/{total_steps}: {action_name}")
        self.scroll.verticalScrollBar().setValue(self.scroll.verticalScrollBar().maximum())

    def on_action_completed(self, step_idx: int, total_steps: int, action_name: str, result: ActionResult) -> None:
        count = self.steps_layout.count()
        if count > 0:
            item = self.steps_layout.itemAt(count - 1)
            if item and item.widget():
                w = item.widget()
                if isinstance(w, QLabel):
                    if result.success:
                        w.setText(f"✓  Step {step_idx}/{total_steps}: {action_name}  <span style='color: #64748b;'>({result.duration:.2f}s)</span>")
                        w.setStyleSheet(
                            """
                            QLabel {
                                font-size: 13px;
                                color: #10b981;
                                font-weight: 600;
                                padding: 8px 12px;
                                background-color: rgba(16, 185, 129, 0.08);
                                border: 1px solid rgba(16, 185, 129, 0.2);
                                border-radius: 6px;
                            }
                            """
                        )
                    else:
                        w.setText(f"✗  Step {step_idx}/{total_steps}: {action_name} — {result.error or result.message}")
                        w.setStyleSheet(
                            """
                            QLabel {
                                font-size: 13px;
                                color: #ef4444;
                                font-weight: 600;
                                padding: 8px 12px;
                                background-color: rgba(239, 68, 68, 0.08);
                                border: 1px solid rgba(239, 68, 68, 0.2);
                                border-radius: 6px;
                            }
                            """
                        )

        self.scroll.verticalScrollBar().setValue(self.scroll.verticalScrollBar().maximum())

    def on_progress(self, percent: float, status_msg: str) -> None:
        self.progress_bar.setValue(int(percent))
        self.status_lbl.setText(status_msg)

    def on_completed(self, mode_id: str, mode_name: str, duration: float) -> None:
        has_errors = False
        for i in range(self.steps_layout.count()):
            item = self.steps_layout.itemAt(i)
            if item and item.widget() and isinstance(item.widget(), QLabel):
                if item.widget().text().startswith("✗"):
                    has_errors = True
                    break

        if has_errors:
            self.title_lbl.setText(f"⚡ {mode_name} Finished with Warnings")
            self.title_lbl.setStyleSheet(f"font-size: 20px; font-weight: 800; color: #f59e0b;")
            self.status_lbl.setText(f"Finished in {duration:.2f}s (some actions reported warnings).")
        else:
            self.title_lbl.setText(f"⚡ {mode_name} Ready!")
            self.title_lbl.setStyleSheet(f"font-size: 20px; font-weight: 800; color: #10b981;")
            self.status_lbl.setText(f"Completed all steps in {duration:.2f} seconds.")

        self.progress_bar.setValue(100)
        self.cancel_btn.setVisible(False)
        self.done_btn.setVisible(True)

        # Auto-dismiss on success after 1.5 seconds if no errors occurred
        if not has_errors:
            QTimer.singleShot(1500, self.accept)

    def on_failed(self, mode_id: str, mode_name: str, error_msg: str) -> None:
        self.title_lbl.setText("Execution Halted")
        self.title_lbl.setStyleSheet("font-size: 20px; font-weight: 800; color: #ef4444;")
        self.status_lbl.setText(error_msg)
        self.cancel_btn.setText("Close")
        try:
            self.cancel_btn.clicked.disconnect()
        except Exception:
            pass
        self.cancel_btn.clicked.connect(self.reject)

    def on_cancelled(self, mode_id: str, mode_name: str) -> None:
        self.title_lbl.setText("Cancelled")
        self.title_lbl.setStyleSheet("font-size: 20px; font-weight: 800; color: #f59e0b;")
        self.status_lbl.setText("Mode execution cancelled by user.")
        self.cancel_btn.setText("Close")
        try:
            self.cancel_btn.clicked.disconnect()
        except Exception:
            pass
        self.cancel_btn.clicked.connect(self.reject)
