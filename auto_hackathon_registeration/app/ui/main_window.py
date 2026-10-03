"""MainWindow - Host window managing navigation, views, and worker threads."""

from pathlib import Path
from typing import Optional, List
from PySide6.QtWidgets import (
    QMainWindow, QWidget, QVBoxLayout, QHBoxLayout, QPushButton,
    QStackedWidget, QLabel, QFrame, QMessageBox, QApplication
)
from PySide6.QtCore import Qt, QThread, Signal
from PySide6.QtGui import QFont, QCloseEvent

from .components import (
    GLOBAL_STYLE_SHEET, BadgeLabel,
    COLOR_BG_BLACK, COLOR_BG_CARD, COLOR_BG_SURFACE, COLOR_BG_HOVER,
    COLOR_BORDER, COLOR_BORDER_LIGHT, COLOR_TEXT_WHITE, COLOR_TEXT_MUTED,
    COLOR_TEXT_DIM, COLOR_WHITE, COLOR_DARK
)
from .dashboard import DashboardView
from .automation_view import AutomationView
from .review_view import ReviewView
from .profile_view import ProfileView
from .settings_view import SettingsView

from ..models.profile import UserProfile
from ..models.form_field import FieldMatch
from ..models.scan_result import ScanResult, AutomationStatus
from ..profile.parser import ProfileParser
from ..services.settings import SettingsManager
from ..services.logger import get_logger
from ..automation.crawler import FormCrawler


class AutomationWorker(QThread):
    """Dedicated background worker thread running Playwright automation."""

    sig_status = Signal(object, str)
    sig_progress = Signal(int, int)
    sig_manual = Signal(str)
    sig_uncertain = Signal(object)
    sig_review = Signal(object, object)
    sig_completed = Signal(bool, str)

    def __init__(self, crawler: FormCrawler, url: str, profile: UserProfile):
        super().__init__()
        self.crawler = crawler
        self.url = url
        self.profile = profile

        # Wire crawler internal callbacks to thread signals
        self.crawler.on_status_changed = lambda st, msg: self.sig_status.emit(st, msg)
        self.crawler.on_progress_updated = lambda f, t: self.sig_progress.emit(f, t)
        self.crawler.on_manual_intervention_required = lambda r: self.sig_manual.emit(r)
        self.crawler.on_uncertain_field = lambda m: self.sig_uncertain.emit(m)
        self.crawler.on_review_required = lambda m, s: self.sig_review.emit(m, s)
        self.crawler.on_completed = lambda ok, msg: self.sig_completed.emit(ok, msg)

    def run(self):
        self.crawler.run(self.url, self.profile)


class MainWindow(QMainWindow):
    """Main application window for HackFill."""

    def __init__(self):
        super().__init__()
        self.setWindowTitle("HackFill — Fill hackathon registrations in seconds")
        self.resize(1200, 800)
        self.setMinimumSize(1000, 700)
        self.setStyleSheet(GLOBAL_STYLE_SHEET)

        self.logger = get_logger()
        self.settings_manager = SettingsManager()
        self.crawler: Optional[FormCrawler] = None
        self.worker: Optional[AutomationWorker] = None

        self._init_ui()
        self._init_data()

    def _init_ui(self):
        central_widget = QWidget()
        self.setCentralWidget(central_widget)
        main_layout = QHBoxLayout(central_widget)
        main_layout.setContentsMargins(0, 0, 0, 0)
        main_layout.setSpacing(0)

        # 1. Left Sidebar
        sidebar = QFrame()
        sidebar.setFixedWidth(240)
        sidebar.setStyleSheet(f"""
            QFrame {{
                background-color: {COLOR_BG_SURFACE};
                border-right: 1px solid {COLOR_BORDER};
            }}
        """)
        sidebar_layout = QVBoxLayout(sidebar)
        sidebar_layout.setContentsMargins(20, 24, 20, 24)
        sidebar_layout.setSpacing(12)

        # Branding
        brand_label = QLabel("HACKFILL")
        brand_label.setFont(QFont("Consolas", 15, QFont.Bold))
        brand_label.setStyleSheet(f"color: {COLOR_WHITE}; letter-spacing: 1.5px;")

        tagline_label = QLabel("v1.0.0 • Desktop")
        tagline_label.setFont(QFont("-apple-system", 9))
        tagline_label.setStyleSheet(f"color: {COLOR_TEXT_DIM};")

        sidebar_layout.addWidget(brand_label)
        sidebar_layout.addWidget(tagline_label)
        sidebar_layout.addSpacing(20)

        # Navigation Buttons
        self.nav_buttons: List[QPushButton] = []

        self.btn_nav_dashboard = self._create_nav_button("Dashboard", 0)
        self.btn_nav_automation = self._create_nav_button("Automation", 1)
        self.btn_nav_review = self._create_nav_button("Review", 2)
        self.btn_nav_profile = self._create_nav_button("Profile", 3)
        self.btn_nav_settings = self._create_nav_button("Settings", 4)

        for btn in (
            self.btn_nav_dashboard, self.btn_nav_automation,
            self.btn_nav_review, self.btn_nav_profile, self.btn_nav_settings
        ):
            sidebar_layout.addWidget(btn)

        sidebar_layout.addStretch()

        # Sidebar footer
        status_box = QFrame()
        status_box.setStyleSheet(f"background-color: {COLOR_BG_CARD}; border-radius: 6px; padding: 10px; border: 1px solid {COLOR_BORDER};")
        status_box_layout = QVBoxLayout(status_box)
        status_box_layout.setContentsMargins(8, 8, 8, 8)
        status_box_layout.setSpacing(4)

        sb_title = QLabel("SYSTEM STATUS")
        sb_title.setFont(QFont("Consolas", 8, QFont.Bold))
        sb_title.setStyleSheet(f"color: {COLOR_TEXT_DIM};")

        self.sb_status = QLabel("Engine Ready")
        self.sb_status.setFont(QFont("-apple-system", 9, QFont.DemiBold))
        self.sb_status.setStyleSheet(f"color: {COLOR_WHITE};")

        status_box_layout.addWidget(sb_title)
        status_box_layout.addWidget(self.sb_status)
        sidebar_layout.addWidget(status_box)

        main_layout.addWidget(sidebar)

        # 2. Main Stacked Views
        self.stack = QStackedWidget()
        self.dashboard_view = DashboardView()
        self.automation_view = AutomationView()
        self.review_view = ReviewView()
        self.profile_view = ProfileView()
        self.settings_view = SettingsView(self.settings_manager)

        self.stack.addWidget(self.dashboard_view)    # Index 0
        self.stack.addWidget(self.automation_view)   # Index 1
        self.stack.addWidget(self.review_view)       # Index 2
        self.stack.addWidget(self.profile_view)      # Index 3
        self.stack.addWidget(self.settings_view)     # Index 4

        main_layout.addWidget(self.stack, stretch=1)

        # Wire view signals
        self._connect_signals()
        self._set_active_nav(0)

    def _create_nav_button(self, text: str, index: int) -> QPushButton:
        btn = QPushButton(text)
        btn.setFont(QFont("-apple-system", 10, QFont.Medium))
        btn.setCursor(Qt.PointingHandCursor)
        btn.setFixedHeight(38)
        btn.clicked.connect(lambda: self._set_active_nav(index))
        self.nav_buttons.append(btn)
        return btn

    def _set_active_nav(self, index: int):
        self.stack.setCurrentIndex(index)
        for i, btn in enumerate(self.nav_buttons):
            if i == index:
                btn.setStyleSheet(f"""
                    QPushButton {{
                        background-color: {COLOR_WHITE};
                        color: {COLOR_DARK};
                        border: none;
                        border-radius: 6px;
                        text-align: left;
                        padding-left: 14px;
                        font-weight: 600;
                    }}
                """)
            else:
                btn.setStyleSheet(f"""
                    QPushButton {{
                        background-color: transparent;
                        color: {COLOR_TEXT_MUTED};
                        border: none;
                        border-radius: 6px;
                        text-align: left;
                        padding-left: 14px;
                    }}
                    QPushButton:hover {{
                        background-color: {COLOR_BG_HOVER};
                        color: {COLOR_TEXT_WHITE};
                    }}
                """)

    def _connect_signals(self):
        # Dashboard signals
        self.dashboard_view.start_automation_requested.connect(self._start_automation)
        self.dashboard_view.view_profile_requested.connect(self._navigate_to_profile)

        # Profile signals
        self.profile_view.profile_updated.connect(self.dashboard_view.update_profile_status)

        # Automation signals
        self.automation_view.stop_requested.connect(self._stop_automation)
        self.automation_view.manual_continue_requested.connect(self._resume_automation)
        self.automation_view.custom_field_resolved.connect(self._resolve_custom_question)
        self.automation_view.skip_field_requested.connect(self._skip_custom_question)

        # Review signals
        self.review_view.back_requested.connect(lambda: self._set_active_nav(0))
        self.review_view.submit_confirmed.connect(self._execute_final_submit)

    def _init_data(self):
        # Check if example profile exists and auto-load into profile view
        ex = Path("profiles/example_profile.txt")
        if ex.exists():
            self.profile_view.load_profile_path(str(ex.absolute()))

    def _navigate_to_profile(self, path: str):
        if path:
            self.profile_view.load_profile_path(path)
        self._set_active_nav(3)

    def _start_automation(self, url: str, profile_path: str):
        profile, _ = ProfileParser.parse_file(profile_path)
        if len(profile) == 0:
            QMessageBox.warning(self, "Invalid Profile", "The selected profile contains no fields.")
            return

        # Prepare crawler
        self.crawler = FormCrawler(settings=self.settings_manager.settings)
        self.automation_view.set_target_url(url, browser_name=self.settings_manager.settings.browser)
        self._set_active_nav(1)  # Switch to Automation View

        # Spawn Worker Thread
        self.worker = AutomationWorker(self.crawler, url, profile)
        self.worker.sig_status.connect(self._on_worker_status)
        self.worker.sig_progress.connect(self.automation_view.update_progress)
        self.worker.sig_manual.connect(self.automation_view.show_intervention)
        self.worker.sig_uncertain.connect(self.automation_view.show_custom_question)
        self.worker.sig_review.connect(self._on_worker_review)
        self.worker.sig_completed.connect(self._on_worker_completed)

        self.sb_status.setText("Automating...")
        self.worker.start()

    def _on_worker_status(self, status: AutomationStatus, message: str):
        self.automation_view.update_pipeline_status(status, message)
        self.sb_status.setText(status.value)
        if self.crawler and self.crawler.cumulative_matches:
            self.automation_view.update_fields_list(self.crawler.cumulative_matches)

    def _on_worker_review(self, matches: List[FieldMatch], scan_result: ScanResult):
        self.review_view.load_review_data(matches, scan_result)
        self._set_active_nav(2)  # Automatically switch to Review View
        self.sb_status.setText("Review Required")

    def _on_worker_completed(self, success: bool, message: str):
        self.sb_status.setText("Completed" if success else "Stopped")
        if success:
            QMessageBox.information(self, "Success", "Hackathon registration workflow completed!")

    def _stop_automation(self):
        if self.crawler:
            self.crawler.request_stop()
        self.sb_status.setText("Stopped")

    def _resume_automation(self):
        if self.crawler:
            self.crawler.resume()

    def _resolve_custom_question(self, match: FieldMatch, answer: str):
        match.user_override_value = answer
        match.status = "FILLED" if answer else "SKIPPED"
        match.is_confirmed = True
        if self.crawler:
            self.crawler.resume()

    def _skip_custom_question(self, match: FieldMatch):
        match.status = "SKIPPED"
        match.is_confirmed = True
        if self.crawler:
            self.crawler.resume()

    def _execute_final_submit(self):
        """Execute the final submission in the browser after explicit confirmation."""
        if not self.crawler:
            QMessageBox.warning(self, "Error", "No active automation session.")
            return

        ok, err = self.crawler.submit_final_form()
        if ok:
            QMessageBox.information(
                self, "Submission Successful",
                "Your hackathon registration was submitted successfully in the browser!"
            )
            self._set_active_nav(0)
        else:
            QMessageBox.critical(self, "Submission Failed", f"Submission error: {err}")

    def closeEvent(self, event: QCloseEvent):
        """Clean up background workers and browser before exit."""
        if self.crawler:
            self.crawler.request_stop()
            self.crawler._cleanup()
        if self.worker and self.worker.isRunning():
            self.worker.quit()
            self.worker.wait(3000)
        event.accept()
