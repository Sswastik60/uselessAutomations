from PySide6.QtCore import Qt, Signal
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


class ExecutionDialog(QDialog):
    """Live modal dialog displaying active mode automation progress."""

    cancel_requested = Signal()

    def __init__(self, mode_name: str, parent=None):
        super().__init__(parent)
        self.setWindowTitle(f"Executing {mode_name}")
        self.setMinimumWidth(500)
        self.setMinimumHeight(400)
        self.setWindowFlags(self.windowFlags() & ~Qt.WindowContextHelpButtonHint)

        main_layout = QVBoxLayout(self)
        main_layout.setContentsMargins(22, 22, 22, 22)
        main_layout.setSpacing(16)

        # Header Title
        self.title_lbl = QLabel(f"Executing {mode_name}...")
        self.title_lbl.setStyleSheet("font-size: 20px; font-weight: 800; color: #f8fafc;")
        main_layout.addWidget(self.title_lbl)

        # Status Subtitle
        self.status_lbl = QLabel("Initializing engine context...")
        self.status_lbl.setStyleSheet("color: #94a3b8; font-size: 13px;")
        main_layout.addWidget(self.status_lbl)

        # Progress Bar
        self.progress_bar = QProgressBar()
        self.progress_bar.setRange(0, 100)
        self.progress_bar.setValue(0)
        main_layout.addWidget(self.progress_bar)

        # Action Steps List Scroll Area
        self.scroll = QScrollArea()
        self.scroll.setWidgetResizable(True)
        self.scroll.setStyleSheet("QScrollArea { border: 1px solid #1f2937; border-radius: 10px; background-color: #111827; }")

        self.steps_container = QWidget()
        self.steps_layout = QVBoxLayout(self.steps_container)
        self.steps_layout.setContentsMargins(14, 14, 14, 14)
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
        lbl.setStyleSheet("font-size: 13px; color: #38bdf8; font-weight: 600; padding: 4px; background: #1e293b; border-radius: 6px;")
        self.steps_layout.addWidget(lbl)
        self.status_lbl.setText(f"Executing step {step_idx}/{total_steps}: {action_name}")
        
        # Auto-scroll to bottom
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
                        w.setStyleSheet("font-size: 13px; color: #10b981; font-weight: 600; padding: 4px; background: #064e3b; border-radius: 6px;")
                    else:
                        w.setText(f"✗  Step {step_idx}/{total_steps}: {action_name} — {result.error or result.message}")
                        w.setStyleSheet("font-size: 13px; color: #ef4444; font-weight: 600; padding: 4px; background: #7f1d1d; border-radius: 6px;")

        # Auto-scroll
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
            self.title_lbl.setStyleSheet("font-size: 20px; font-weight: 800; color: #f59e0b;")
            self.status_lbl.setText(f"Automation steps finished in {duration:.2f}s (some steps encountered issues).")
        else:
            self.title_lbl.setText(f"⚡ {mode_name} Ready!")
            self.title_lbl.setStyleSheet("font-size: 20px; font-weight: 800; color: #10b981;")
            self.status_lbl.setText(f"Completed all automation steps in {duration:.2f} seconds.")

        self.progress_bar.setValue(100)
        self.cancel_btn.setVisible(False)
        self.done_btn.setVisible(True)

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
