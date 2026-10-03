"""FormCrawler - Master automation workflow orchestrator."""

import threading
import time
from typing import Callable, Optional, List, Dict
from playwright.sync_api import Error as PlaywrightError
from .browser import BrowserManager
from .form_detector import FormDetector
from .field_matcher import AutomationFieldMatcher
from .form_filler import FormFiller
from .navigation import MultiPageNavigator
from .human_intervention import HumanInterventionDetector
from ..models.profile import UserProfile
from ..models.form_field import FieldMatch
from ..models.scan_result import ScanResult, AutomationStatus
from ..services.settings import AppSettings
from ..services.logger import get_logger


class FormCrawler:
    """Orchestrates end-to-end hackathon form scanning, matching, filling, and review."""

    def __init__(self, settings: Optional[AppSettings] = None):
        self.settings = settings or AppSettings()
        self.logger = get_logger()

        self.browser_manager = BrowserManager(
            browser_type=self.settings.browser,
            custom_executable_path=self.settings.custom_browser_path,
            visible=self.settings.browser_visible,
            timeout_seconds=self.settings.timeout_seconds
        )
        self.detector = FormDetector()
        self.matcher = AutomationFieldMatcher()
        self.filler = FormFiller()
        self.navigator = MultiPageNavigator(max_pages=self.settings.max_pages)

        # Thread synchronization
        self._stop_requested = threading.Event()
        self._pause_event = threading.Event()
        self._pause_event.set()  # set = running, clear = paused

        # Cumulative matches across all visited pages
        self.cumulative_matches: List[FieldMatch] = []
        self.last_scan_result: Optional[ScanResult] = None
        self.status = AutomationStatus.IDLE

        # UI Callbacks
        self.on_status_changed: Optional[Callable[[AutomationStatus, str], None]] = None
        self.on_progress_updated: Optional[Callable[[int, int], None]] = None
        self.on_manual_intervention_required: Optional[Callable[[str], None]] = None
        self.on_uncertain_field: Optional[Callable[[FieldMatch], None]] = None
        self.on_review_required: Optional[Callable[[List[FieldMatch], ScanResult], None]] = None
        self.on_completed: Optional[Callable[[bool, str], None]] = None

    def _update_status(self, status: AutomationStatus, message: str) -> None:
        self.status = status
        self.logger.info(message)
        if self.on_status_changed:
            self.on_status_changed(status, message)

    def request_stop(self) -> None:
        """Signal automation to halt immediately."""
        self.logger.warning("Stop requested by user. Aborting automation...")
        self._stop_requested.set()
        self._pause_event.set()  # Unblock any waiting pause
        self._update_status(AutomationStatus.STOPPED, "Automation stopped by user.")

    def resume(self) -> None:
        """Unpause automation after manual user interaction."""
        self.logger.info("Resuming automation...")
        self._pause_event.set()

    def run(self, url: str, profile: UserProfile) -> None:
        """Main automation execution loop."""
        self._stop_requested.clear()
        self._pause_event.set()
        self.cumulative_matches.clear()
        self.navigator.reset()

        try:
            # 1. Launch Browser
            self._update_status(AutomationStatus.CONNECTING, "Launching browser...")
            ok, err = self.browser_manager.launch()
            if not ok:
                self._update_status(AutomationStatus.ERROR, f"Browser launch failed: {err}")
                if self.on_completed:
                    self.on_completed(False, err)
                return

            if self._stop_requested.is_set():
                self._cleanup()
                return

            # 2. Navigate to URL
            self._update_status(AutomationStatus.CONNECTING, f"Navigating to {url}...")
            ok, err = self.browser_manager.navigate(url)
            if not ok:
                self._update_status(AutomationStatus.ERROR, f"Navigation failed: {err}")
                if self.on_completed:
                    self.on_completed(False, err)
                return

            page = self.browser_manager.page
            if not page:
                self._update_status(AutomationStatus.ERROR, "Browser page handle lost.")
                return

            # Multi-page scanning & filling loop
            while not self._stop_requested.is_set():
                current_page_num = self.navigator.current_page_number

                # 3. Check for Human Intervention (CAPTCHA, OTP, login)
                has_barrier, reason = HumanInterventionDetector.check(page)
                if has_barrier and self.settings.pause_on_captcha:
                    self._update_status(
                        AutomationStatus.WAITING_MANUAL,
                        f"MANUAL ACTION REQUIRED: {reason}"
                    )
                    if self.on_manual_intervention_required:
                        self.on_manual_intervention_required(reason or "Verification challenge detected.")

                    self._pause_event.clear()
                    self._pause_event.wait()  # Block until user resumes or stops

                    if self._stop_requested.is_set():
                        break

                # 4. Scan the DOM for fields
                self._update_status(AutomationStatus.SCANNING, f"Scanning page {current_page_num}...")
                scan_res = self.detector.scan_page(page, page_number=current_page_num)
                self.last_scan_result = scan_res

                if not scan_res.fields:
                    self.logger.warning(f"No registration form fields detected on page {current_page_num}.")

                # 5. Match Fields against Profile
                self._update_status(AutomationStatus.MATCHING, "Matching fields with profile...")
                matches = self.matcher.process_scan(scan_res, profile)

                # Check for custom/uncertain fields requiring prompt
                if self.settings.pause_on_uncertain_fields:
                    for match in matches:
                        if self._stop_requested.is_set():
                            break
                        if match.status == "PENDING_CONFIRMATION" and not match.is_confirmed:
                            self._update_status(
                                AutomationStatus.WAITING_CONFIRMATION,
                                f"Waiting for user confirmation on field: '{match.field.display_name}'"
                            )
                            if self.on_uncertain_field:
                                self.on_uncertain_field(match)
                                self._pause_event.clear()
                                self._pause_event.wait()

                if self._stop_requested.is_set():
                    break

                # 6. Fill Fields
                self._update_status(AutomationStatus.FILLING, "Filling compatible fields...")
                filled_count = self.filler.fill_all(page, matches)
                self.cumulative_matches.extend(matches)

                total_discovered = len(self.cumulative_matches)
                total_filled = sum(1 for m in self.cumulative_matches if m.status == "FILLED")
                if self.on_progress_updated:
                    self.on_progress_updated(total_filled, total_discovered)

                # 7. Check Multi-Page Progression
                if self.navigator.can_advance(scan_res):
                    adv_ok = self.navigator.advance(page, scan_res)
                    if adv_ok:
                        continue  # Continue loop for next step
                    else:
                        break
                else:
                    # Final step reached
                    break

            if self._stop_requested.is_set():
                self._cleanup()
                return

            # 8. Mandatory Pre-Submission Review Screen
            self._update_status(AutomationStatus.WAITING_REVIEW, "Form filling completed. Review required.")
            if self.on_review_required and self.last_scan_result:
                self.on_review_required(self.cumulative_matches, self.last_scan_result)

        except Exception as e:
            err_msg = f"Unexpected automation error: {str(e)}"
            self.logger.error(err_msg)
            self._update_status(AutomationStatus.ERROR, err_msg)
            if self.on_completed:
                self.on_completed(False, err_msg)
        finally:
            pass  # Keep browser open for user review until explicitly closed

    def submit_final_form(self) -> Tuple[bool, str]:
        """
        Explicitly triggers the final submit button in the browser.
        MUST ONLY BE CALLED UPON USER CONFIRMATION ON THE REVIEW SCREEN.
        """
        if not self.browser_manager.is_alive() or not self.browser_manager.page:
            return False, "Cannot submit: Browser is not open."

        if not self.last_scan_result or not self.last_scan_result.submit_button_selector:
            return False, "Submit button selector not found on page."

        try:
            page = self.browser_manager.page
            selector = self.last_scan_result.submit_button_selector
            self._update_status(AutomationStatus.SUBMITTING, "Submitting final registration...")

            btn = page.locator(selector).first
            btn.click(timeout=8000)

            # Wait briefly for submission response
            try:
                page.wait_for_load_state("load", timeout=5000)
            except Exception:
                pass

            self._update_status(AutomationStatus.COMPLETED, "Registration submitted successfully!")
            if self.on_completed:
                self.on_completed(True, "Registration completed successfully.")
            return True, ""
        except PlaywrightError as pe:
            err = f"Failed to click submit button: {str(pe)}"
            self.logger.error(err)
            self._update_status(AutomationStatus.ERROR, err)
            return False, err
        except Exception as e:
            err = f"Unexpected error submitting form: {str(e)}"
            self.logger.error(err)
            self._update_status(AutomationStatus.ERROR, err)
            return False, err

    def _cleanup(self) -> None:
        """Close browser resources cleanly."""
        self.browser_manager.close()
