"""Playwright Chromium Browser Lifecycle Manager."""

from typing import Optional, Tuple
from playwright.sync_api import sync_playwright, Playwright, Browser, BrowserContext, Page, Error as PlaywrightError
from ..services.logger import get_logger


class BrowserManager:
    """Manages the lifecycle of a controlled visible Chromium browser instance."""

    def __init__(self, visible: bool = True, timeout_seconds: int = 30):
        self.visible = visible
        self.timeout_ms = timeout_seconds * 1000
        self.playwright: Optional[Playwright] = None
        self.browser: Optional[Browser] = None
        self.context: Optional[BrowserContext] = None
        self.page: Optional[Page] = None
        self.logger = get_logger()

    def launch(self) -> Tuple[bool, str]:
        """Launch Chromium browser in visible or headless mode."""
        try:
            self.logger.info("Initializing Playwright engine...")
            self.playwright = sync_playwright().start()

            launch_args = [
                "--start-maximized",
                "--disable-blink-features=AutomationControlled",
            ]

            self.logger.info(f"Launching Chromium (Visible={self.visible})...")
            self.browser = self.playwright.chromium.launch(
                headless=not self.visible,
                args=launch_args,
                slow_mo=50  # Modest human-visible pacing
            )

            self.context = self.browser.new_context(
                viewport={"width": 1280, "height": 850},
                user_agent="Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/122.0.0.0 Safari/537.36"
            )

            self.page = self.context.new_page()
            self.page.set_default_timeout(self.timeout_ms)
            self.logger.success("Browser launched successfully.")
            return True, ""
        except PlaywrightError as pe:
            err_msg = f"Playwright error launching browser: {str(pe)}"
            self.logger.error(err_msg)
            self.close()
            return False, err_msg
        except Exception as e:
            err_msg = f"Unexpected error during browser launch: {str(e)}"
            self.logger.error(err_msg)
            self.close()
            return False, err_msg

    def navigate(self, url: str) -> Tuple[bool, str]:
        """Navigate to target URL with intelligent page load waits."""
        if not self.is_alive() or not self.page:
            return False, "Browser is not active or was closed."

        try:
            self.logger.info(f"Opening website: {url}")
            self.page.goto(url, wait_until="domcontentloaded", timeout=self.timeout_ms)

            # Smart wait for potential SPA hydration or network stabilization
            try:
                self.page.wait_for_load_state("load", timeout=5000)
            except PlaywrightError:
                pass  # It's okay if heavy analytics scripts don't finish loading

            return True, ""
        except PlaywrightError as pe:
            err_msg = f"Failed to load URL '{url}': {str(pe)}"
            self.logger.error(err_msg)
            return False, err_msg
        except Exception as e:
            err_msg = f"Error during navigation: {str(e)}"
            self.logger.error(err_msg)
            return False, err_msg

    def is_alive(self) -> bool:
        """Check if browser and target page are currently open and responsive."""
        try:
            if self.page and not self.page.is_closed():
                return True
        except Exception:
            pass
        return False

    def close(self) -> None:
        """Safely terminate browser, context, and Playwright session."""
        try:
            if self.page and not self.page.is_closed():
                self.page.close()
        except Exception:
            pass
        finally:
            self.page = None

        try:
            if self.context:
                self.context.close()
        except Exception:
            pass
        finally:
            self.context = None

        try:
            if self.browser and self.browser.is_connected():
                self.browser.close()
        except Exception:
            pass
        finally:
            self.browser = None

        try:
            if self.playwright:
                self.playwright.stop()
        except Exception:
            pass
        finally:
            self.playwright = None
            self.logger.info("Browser session closed cleanly.")
