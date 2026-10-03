"""Playwright Browser Lifecycle Manager supporting Chromium, Brave, Chrome, and Edge."""

import os
import shutil
import subprocess
import time
import urllib.request
from pathlib import Path
from typing import Optional, Tuple, Dict, List
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


def is_browser_running(browser_type: str = "Brave") -> bool:
    """Check if the browser executable process is currently active in the process table."""
    proc_map = {
        "brave": "brave.exe",
        "chrome": "chrome.exe",
        "edge": "msedge.exe",
        "chromium": "chrome.exe",
    }
    exe_name = proc_map.get(browser_type.lower(), f"{browser_type.lower()}.exe")
    try:
        res = subprocess.run(
            ["tasklist", "/FI", f"IMAGENAME eq {exe_name}", "/NH"],
            capture_output=True,
            text=True,
            timeout=3
        )
        return exe_name.lower() in (res.stdout or "").lower()
    except Exception:
        return False


def is_cdp_port_active(port: int = 9222) -> bool:
    """Check if the Chrome DevTools Protocol remote debugging port is open and responding."""
    try:
        req = urllib.request.Request(f"http://localhost:{port}/json/version", headers={"User-Agent": "HackFill"})
        with urllib.request.urlopen(req, timeout=1) as resp:
            return resp.status == 200
    except Exception:
        return False


def launch_or_restart_browser_with_debugging(
    browser_type: str = "Brave",
    port: int = 9222,
    custom_path: str = ""
) -> Tuple[bool, str]:
    """
    Ensure browser is running with --remote-debugging-port active.
    If it is running without the port, restarts it with --remote-debugging-port and --restore-last-session
    so that all open tabs and active login sessions are preserved.
    """
    logger = get_logger()
    exec_path = find_browser_executable(browser_type, custom_path)
    if not exec_path or not Path(exec_path).is_file():
        return False, f"Could not find executable for '{browser_type}'."

    proc_name = Path(exec_path).name

    # If already running without port, close it so we can re-open with debugging
    if is_browser_running(browser_type) and not is_cdp_port_active(port):
        logger.info(f"Restarting {browser_type} with automation debugging port {port}...")
        try:
            subprocess.run(["taskkill", "/IM", proc_name, "/F"], capture_output=True, timeout=5)
            time.sleep(1.0)
        except Exception as e:
            logger.warning(f"Note during process cleanup: {e}")

    # Launch with remote debugging and restore-last-session
    logger.info(f"Launching {proc_name} with --remote-debugging-port={port} --restore-last-session")
    try:
        subprocess.Popen(
            [exec_path, f"--remote-debugging-port={port}", "--restore-last-session"],
            creationflags=subprocess.DETACHED_PROCESS if os.name == "nt" else 0
        )
    except Exception as e:
        return False, f"Failed to spawn {browser_type}: {e}"

    # Poll port for up to 6 seconds
    start_t = time.time()
    while time.time() - start_t < 6.0:
        if is_cdp_port_active(port):
            logger.success(f"{browser_type} automation port {port} is now active!")
            return True, ""
        time.sleep(0.4)

    return False, f"Browser started, but automation port {port} did not become active in time."


class BrowserManager:
    """Manages the lifecycle of a controlled Chromium or Brave browser instance, including CDP attachment."""

    def __init__(
        self,
        browser_type: str = "Brave",
        custom_executable_path: str = "",
        visible: bool = True,
        timeout_seconds: int = 30,
        connect_to_existing_browser: bool = True,
        cdp_port: int = 9222,
        auto_restart_browser_with_debugging: bool = True
    ):
        self.browser_type = browser_type
        self.custom_executable_path = custom_executable_path
        self.visible = visible
        self.timeout_ms = timeout_seconds * 1000
        self.connect_to_existing_browser = connect_to_existing_browser
        self.cdp_port = cdp_port
        self.auto_restart_browser_with_debugging = auto_restart_browser_with_debugging
        self.is_connected_via_cdp = False
        self.playwright: Optional[Playwright] = None
        self.browser: Optional[Browser] = None
        self.context: Optional[BrowserContext] = None
        self.page: Optional[Page] = None
        self.logger = get_logger()

    def launch(self) -> Tuple[bool, str]:
        """Attach to existing open browser via CDP or launch a new instance."""
        try:
            self.logger.info("Initializing Playwright engine...")
            self.playwright = sync_playwright().start()

            # 1. Attempt connection to already-running browser via CDP
            if self.connect_to_existing_browser and self.visible:
                # Check if CDP port is open
                if not is_cdp_port_active(self.cdp_port):
                    if is_browser_running(self.browser_type):
                        if self.auto_restart_browser_with_debugging:
                            self.logger.info(
                                f"Existing {self.browser_type} is running without automation port. "
                                f"Restarting with automation port (restoring all tabs and logins)..."
                            )
                            ok, err = launch_or_restart_browser_with_debugging(
                                self.browser_type, self.cdp_port, self.custom_executable_path
                            )
                            if not ok:
                                self.logger.warning(f"Could not enable automation port on running browser: {err}")
                        else:
                            self.logger.warning(f"{self.browser_type} is running, but port {self.cdp_port} is not open.")
                    else:
                        # Browser wasn't running, start it with CDP
                        self.logger.info(f"Starting {self.browser_type} with automation port {self.cdp_port}...")
                        launch_or_restart_browser_with_debugging(
                            self.browser_type, self.cdp_port, self.custom_executable_path
                        )

                # Now connect over CDP if port is active
                if is_cdp_port_active(self.cdp_port):
                    self.logger.info(f"Connecting to already-open {self.browser_type} on port {self.cdp_port}...")
                    self.browser = self.playwright.chromium.connect_over_cdp(f"http://localhost:{self.cdp_port}")
                    self.is_connected_via_cdp = True
                    if self.browser.contexts:
                        self.context = self.browser.contexts[0]
                    else:
                        self.context = self.browser.new_context()

                    # Pick active page or create one
                    if self.context.pages:
                        self.page = self.context.pages[-1]
                    else:
                        self.page = self.context.new_page()

                    self.page.set_default_timeout(self.timeout_ms)
                    self.logger.success(f"Attached to already-open {self.browser_type} successfully! (Zero new instances)")
                    return True, ""
                else:
                    self.logger.warning(f"Could not connect via CDP on port {self.cdp_port}. Falling back to standard browser launch...")

            # 2. Standard Launch Fallback (if CDP disabled or unavailable)
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
        """Navigate to target URL, attaching to existing open tab if available."""
        if not self.is_alive() or not self.page:
            return False, "Browser is not active or was closed."

        try:
            # If connected via CDP, inspect if the URL is already open in ANY existing tab!
            if self.is_connected_via_cdp and self.context:
                target_clean = url.split("?")[0].rstrip("/")
                for p in self.context.pages:
                    p_clean = (p.url or "").split("?")[0].rstrip("/")
                    if target_clean and p_clean and target_clean in p_clean:
                        self.page = p
                        self.logger.info(f"Re-using already open tab: {p.url}")
                        try:
                            self.page.bring_to_front()
                        except Exception:
                            pass
                        return True, ""

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
        """Safely terminate Playwright session without closing user's open browser."""
        if self.is_connected_via_cdp:
            self.logger.info("Detaching from user's open browser session cleanly...")
            try:
                if self.browser:
                    self.browser.close()
            except Exception:
                pass
            finally:
                self.browser = None
                self.context = None
                self.page = None

            try:
                if self.playwright:
                    self.playwright.stop()
            except Exception:
                pass
            finally:
                self.playwright = None
            self.logger.info("Cleanly detached. Your browser and tabs remain open.")
            return

        # Standard launch cleanup
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
