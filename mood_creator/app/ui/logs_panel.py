import csv
from typing import Optional
from PySide6.QtCore import Qt
from PySide6.QtWidgets import (
    QComboBox,
    QFileDialog,
    QHBoxLayout,
    QHeaderView,
    QLabel,
    QLineEdit,
    QMessageBox,
    QPushButton,
    QTableWidget,
    QTableWidgetItem,
    QVBoxLayout,
    QWidget,
)

from app.persistence.database import Database


class LogsPanelView(QWidget):
    """Execution Activity Logs viewer tab with live filtering and CSV export."""

    def __init__(self, db: Database, parent=None):
        super().__init__(parent)
        self.db = db
        self.raw_logs = []

        main_layout = QVBoxLayout(self)
        main_layout.setContentsMargins(24, 24, 24, 24)
        main_layout.setSpacing(16)

        # Header Row
        header_layout = QHBoxLayout()
        title_lbl = QLabel("Activity Logs")
        title_lbl.setStyleSheet("font-size: 24px; font-weight: 800; color: #f8fafc; letter-spacing: -0.5px;")

        self.count_lbl = QLabel("(0 Entries)")
        self.count_lbl.setStyleSheet("font-size: 14px; color: #94a3b8; margin-top: 4px;")

        # Search Bar & Filters
        self.search_input = QLineEdit()
        self.search_input.setPlaceholderText("🔍 Search logs...")
        self.search_input.setClearButtonEnabled(True)
        self.search_input.setFixedWidth(200)
        self.search_input.textChanged.connect(self._apply_filters)

        self.status_filter_combo = QComboBox()
        self.status_filter_combo.addItem("All Statuses", "all")
        self.status_filter_combo.addItem("Success Only", "success")
        self.status_filter_combo.addItem("Failures Only", "failure")
        self.status_filter_combo.currentIndexChanged.connect(self._apply_filters)

        # Buttons
        self.export_btn = QPushButton("📤 Export CSV")
        self.export_btn.setProperty("class", "SecondaryButton")
        self.export_btn.clicked.connect(self.export_csv)

        self.clear_btn = QPushButton("🗑 Clear Logs")
        self.clear_btn.setProperty("class", "SecondaryButton")
        self.clear_btn.clicked.connect(self.clear_logs)

        self.refresh_btn = QPushButton("🔄 Refresh")
        self.refresh_btn.setProperty("class", "SecondaryButton")
        self.refresh_btn.clicked.connect(self.refresh_logs)

        header_layout.addWidget(title_lbl)
        header_layout.addWidget(self.count_lbl)
        header_layout.addStretch()
        header_layout.addWidget(self.search_input)
        header_layout.addWidget(self.status_filter_combo)
        header_layout.addWidget(self.export_btn)
        header_layout.addWidget(self.clear_btn)
        header_layout.addWidget(self.refresh_btn)

        main_layout.addLayout(header_layout)

        # Logs Table
        self.log_table = QTableWidget(0, 6)
        self.log_table.setHorizontalHeaderLabels([
            "Timestamp",
            "Mode",
            "Action Name",
            "Status",
            "Duration (s)",
            "Details / Message",
        ])
        self.log_table.horizontalHeader().setSectionResizeMode(QHeaderView.ResizeToContents)
        self.log_table.horizontalHeader().setSectionResizeMode(5, QHeaderView.Stretch)
        
        main_layout.addWidget(self.log_table)

        self.refresh_logs()

    def refresh_logs(self) -> None:
        """Fetch logs from SQLite database and render table rows."""
        self.raw_logs = self.db.get_recent_logs(limit=300)
        self._apply_filters()

    def _apply_filters(self) -> None:
        query = self.search_input.text().strip().lower()
        status_filter = self.status_filter_combo.currentData()

        filtered = []
        for entry in self.raw_logs:
            success = bool(entry.get("success", 0))

            if status_filter == "success" and not success:
                continue
            if status_filter == "failure" and success:
                continue

            if query:
                m_name = str(entry.get("mode_name", "")).lower()
                a_name = str(entry.get("action_name", "")).lower()
                msg = str(entry.get("error") or entry.get("message") or "").lower()
                if query not in m_name and query not in a_name and query not in msg:
                    continue

            filtered.append(entry)

        self.count_lbl.setText(f"({len(filtered)} Entr{'ies' if len(filtered) != 1 else 'y'})")
        self.log_table.setRowCount(len(filtered))

        for row, entry in enumerate(filtered):
            ts = entry.get("timestamp", "")
            if "T" in ts:
                ts = ts.replace("T", " ").split(".")[0]

            self.log_table.setItem(row, 0, QTableWidgetItem(ts))
            self.log_table.setItem(row, 1, QTableWidgetItem(entry.get("mode_name", "")))
            self.log_table.setItem(row, 2, QTableWidgetItem(entry.get("action_name", "")))

            success = bool(entry.get("success", 0))
            status_item = QTableWidgetItem("✓ SUCCESS" if success else "✗ FAILED")
            status_item.setForeground(Qt.GlobalColor.green if success else Qt.GlobalColor.red)
            self.log_table.setItem(row, 3, status_item)

            dur = entry.get("duration", 0.0)
            self.log_table.setItem(row, 4, QTableWidgetItem(f"{dur:.2f}s"))

            msg = entry.get("error") or entry.get("message") or ""
            self.log_table.setItem(row, 5, QTableWidgetItem(msg))

    def export_csv(self) -> None:
        """Export visible logs to a CSV file."""
        if not self.raw_logs:
            QMessageBox.information(self, "Export Logs", "No log entries to export.")
            return

        file_path, _ = QFileDialog.getSaveFileName(
            self, "Export Activity Logs to CSV", "automation_hub_logs.csv", "CSV Files (*.csv);;All Files (*.*)"
        )
        if file_path:
            try:
                with open(file_path, "w", newline="", encoding="utf-8") as f:
                    writer = csv.writer(f)
                    writer.writerow(["Timestamp", "Mode ID", "Mode Name", "Action Name", "Success", "Duration (s)", "Details"])
                    for entry in self.raw_logs:
                        writer.writerow([
                            entry.get("timestamp", ""),
                            entry.get("mode_id", ""),
                            entry.get("mode_name", ""),
                            entry.get("action_name", ""),
                            entry.get("success", 0),
                            entry.get("duration", 0.0),
                            entry.get("error") or entry.get("message") or "",
                        ])
                QMessageBox.information(self, "Export Complete", f"Successfully exported activity logs to:\n{file_path}")
            except Exception as e:
                QMessageBox.critical(self, "Export Error", f"Failed to export logs: {e}")

    def clear_logs(self) -> None:
        """Clear database logs."""
        res = QMessageBox.question(
            self, "Clear Logs", "Are you sure you want to permanently clear all activity logs?", QMessageBox.Yes | QMessageBox.No
        )
        if res == QMessageBox.Yes:
            self.db.clear_logs()
            self.refresh_logs()
