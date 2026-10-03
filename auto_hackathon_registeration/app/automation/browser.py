"""Playwright Browser Lifecycle Manager supporting Chromium, Brave, Chrome, and Edge."""

import os
import shutil
from pathlib import Path
from typing import Optional, Tuple, Dict
from playwright.sync_api import sync_playwright, Playwright, Browser, BrowserContext, Page, Error as PlaywrightError
from ..services.logger import get_logger


def find_browser_executable(browser_type: str, custom_path: str = "") -> Optional[str]:
    """
    Locate executable binary for the requested browser type on Windows or Linux/macOS.
    Supports Brave, Google Chrome, Microsoft Edge, and custom paths.
    """
    if custom_path and Path(custom_path).is_file():
        return str(Path(custom_path).absolute())

    browser_lower = (browser_type or "").lower().strip()

    if "brave" in browser_lower:
        candidates = [
            r"C:\Program Files\BraveSoftware\Brave-Browser\Application\brave.exe",
            r"C:\Program Files (x86)\BraveSoftware\Brave-Browser\Application\brave.exe",
            os.path.expandvars(r"%LOCALAPPDATA%\BraveSoftware\Brave-Browser\Application\brave.exe"),
            "/usr/bin/brave-browser",
            "/usr/bin/brave",
            "/Applications/Brave Browser.app/Contents/MacOS/Brave Browser"
        ]

        # Windows Registry lookup
        try:
            import winreg
            for root in (winreg.HKEY_LOCAL_MACHINE, winreg.HKEY_CURRENT_USER):
                try:
                    with winreg.OpenKey(root, r"SOFTWARE\Microsoft\Windows\CurrentVersion\App Paths\brave.exe") as key:
                        val, _ = winreg.QueryValueEx(key, "")
                        if val and Path(val).is_file():
                            return str(Path(val).absolute())
                except OSError:
                    pass
        except Exception:
            pass

        for path_str in candidates:
            if Path(path_str).is_file():
                return str(Path(path_str).absolute())

        which_path = shutil.which("brave.exe") or shutil.which("brave")
        if which_path:
            return str(Path(which_path).absolute())

    elif "chrome" in browser_lower:
        candidates = [
            r"C:\Program Files\Google\Chrome\Application\chrome.exe",
            r"C:\Program Files (x86)\Google\Chrome\Application\chrome.exe",
            os.path.expandvars(r"%LOCALAPPDATA%\Google\Chrome\Application\chrome.exe"),
            "/usr/bin/google-chrome",
            "/Applications/Google Chrome.app/Contents/MacOS/Google Chrome"
        ]
        for path_str in candidates:
            if Path(path_str).is_file():
                return str(Path(path_str).absolute())

        which_path = shutil.which("chrome.exe") or shutil.which("google-chrome") or shutil.which("chrome")
        if which_path:
            return str(Path(which_path).absolute())

    elif "edge" in browser_lower:
        candidates = [
            r"C:\Program Files (x86)\Microsoft\Edge\Application\msedge.exe",
            r"C:\Program Files\Microsoft\Edge\Application\msedge.exe",
        ]
        for path_str in candidates:
            if Path(path_str).is_file():
                return str(Path(path_str).absolute())

        which_path = shutil.which("msedge.exe") or shutil.which("msedge")
        if which_path:
            return str(Path(which_path).absolute())

    return None


def get_available_browsers() -> Dict[str, Optional[str]]:
    """Scan the local system and return a map of supported browsers to their detected paths."""
    browsers = {
        "Chromium": "Playwright Built-in",
        "Brave": find_browser_executable("Brave"),
        "Chrome": find_browser_executable("Chrome"),
        "Edge": find_browser_executable("Edge"),
    }
    return browsers


class BrowserManager:
    """Manages the lifecycle of a controlled Chromium or Brave browser instance."""

    def __init__(
        self,
        browser_type: str = "Chromium",
        custom_executable_path: str = "",
        visible: bool = True,
        timeout_seconds: int = 30
    ):
        self.browser_type = browser_type
        self.custom_executable_path = custom_executable_path
        self.visible = visible
        self.timeout_ms = timeout_seconds * 1000
        self.playwright: Optional[Playwright] = None
        self.browser: Optional[Browser] = None
        self.context: Optional[BrowserContext] = None
        self.page: Optional[Page] = None
        self.logger = get_logger()

    def launch(self) -> Tuple[bool, str]:
        """Launch Chromium or Brave browser in visible or headless mode."""
        try:
            self.logger.info("Initializing Playwright engine...")
            self.playwright = sync_playwright().start()

            resolved_exec_path = None
            browser_display = "Playwright Chromium"

            if self.browser_type.lower() != "chromium":
                resolved_exec_path = find_browser_executable(self.browser_type, self.custom_executable_path)
                if not resolved_exec_path:
                    err_msg = (
                        f"Could not locate '{self.browser_type}' executable on this system. "
                        f"Please ensure it is installed or specify its path in Settings."
                    )
                    self.logger.error(err_msg)
                    self.close()
                    return False, err_msg
                browser_display = f"{self.browser_type} ({Path(resolved_exec_path).name})"
                self.logger.info(f"Targeting external browser binary: {resolved_exec_path}")

            launch_args = [
                "--start-maximized",
                "--disable-blink-features=AutomationControlled",
            ]

            launch_kwargs = {
                "headless": not self.visible,
                "args": launch_args,
                "slow_mo": 50
            }
            if resolved_exec_path:
                launch_kwargs["executable_path"] = resolved_exec_path

            self.logger.info(f"Launching {browser_display} (Visible={self.visible})...")
            self.browser = self.playwright.chromium.launch(**launch_kwargs)

            self.context = self.browser.new_context(
                viewport={"width": 1280, "height": 850},
                user_agent="Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/122.0.0.0 Safari/537.36"
            )

            self.page = self.context.new_page()
            self.page.set_default_timeout(self.timeout_ms)
            self.logger.success(f"{browser_display} launched and ready.")
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
                pass

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
