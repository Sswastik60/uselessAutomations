"""Multi-page form navigation and loop prevention."""

import hashlib
from typing import Set, Optional
from playwright.sync_api import Page, Error as PlaywrightError
from ..models.scan_result import ScanResult
from ..services.logger import get_logger


class MultiPageNavigator:
    """Manages progression through multi-step forms while preventing infinite loops."""

    def __init__(self, max_pages: int = 30):
        self.max_pages = max_pages
        self.visited_signatures: Set[str] = set()
        self.current_page_number = 1
        self.logger = get_logger()

    def generate_dom_signature(self, page: Page) -> str:
        """Create a hash of currently visible form fields and text to detect repeated states."""
        try:
            content = page.evaluate("""
                () => {
                    function isVis(el) {
                        if (!el) return false;
                        const style = window.getComputedStyle(el);
                        if (style.display === 'none' || style.visibility === 'hidden' || style.opacity === '0') return false;
                        const rect = el.getBoundingClientRect();
                        return rect.width > 0 && rect.height > 0;
                    }
                    const inputs = Array.from(document.querySelectorAll('input:not([type="hidden"]), select, textarea'))
                        .filter(isVis);
                    const activeStep = document.querySelector('.active, [aria-selected="true"], h1, h2')?.innerText || '';
                    return inputs.map(i => (i.id || i.name || '') + ':' + (i.value || '')).join('|') + '::' + activeStep + '::' + document.title;
                }
            """)
            return hashlib.md5(content.encode("utf-8")).hexdigest()
        except Exception:
            return ""

    def can_advance(self, scan_result: ScanResult) -> bool:
        """Determine if there is a valid forward navigation button and we are within page limits."""
        if self.current_page_number >= self.max_pages:
            self.logger.warning(f"Maximum page limit reached ({self.max_pages}). Halting multi-page navigation.")
            return False

        return bool(scan_result.next_button_selector)

    def advance(self, page: Page, scan_result: ScanResult) -> bool:
        """Click the next/continue button and wait for the new page state."""
        if not scan_result.next_button_selector:
            return False

        # Record signature before clicking
        pre_sig = self.generate_dom_signature(page)
        if pre_sig:
            self.visited_signatures.add(pre_sig)

        try:
            btn_text = scan_result.next_button_text or "Next"
            self.logger.info(f"Advancing to next step via button '{btn_text}'...")

            locator = page.locator(scan_result.next_button_selector).first
            locator.click(timeout=5000)

            # Wait for either DOM change or brief delay
            try:
                page.wait_for_load_state("domcontentloaded", timeout=5000)
            except PlaywrightError:
                pass

            # Smart pause for client-side transitions
            page.wait_for_timeout(600)

            # Check for loops
            post_sig = self.generate_dom_signature(page)
            if post_sig and post_sig in self.visited_signatures:
                self.logger.warning("Detected form loop (same page state after clicking Next). Halting step progression.")
                return False

            self.current_page_number += 1
            self.logger.success(f"Successfully reached step {self.current_page_number}.")
            return True

        except PlaywrightError as pe:
            self.logger.warning(f"Failed to click next button: {str(pe)}")
            return False
        except Exception as e:
            self.logger.warning(f"Unexpected error advancing page: {str(e)}")
            return False

    def reset(self) -> None:
        """Reset visited state tracking for a new automation run."""
        self.visited_signatures.clear()
        self.current_page_number = 1
