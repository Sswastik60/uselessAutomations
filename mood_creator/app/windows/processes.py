import glob
import logging
import os
import subprocess
import time
import winreg
from pathlib import Path
from typing import Dict, List, Optional
import psutil

logger = logging.getLogger(__name__)


class ProcessManager:
    """Windows process control, search, and lifecycle management helper."""

    @staticmethod
    def is_process_running(process_name: str) -> bool:
        """Check if any process matching process_name (case-insensitive) is active."""
        target_name = process_name.lower()
        if not target_name.endswith(".exe"):
            target_name += ".exe"

        for proc in psutil.process_iter(["name"]):
            try:
                if proc.info["name"] and proc.info["name"].lower() == target_name:
                    return True
            except (psutil.NoSuchProcess, psutil.AccessDenied, psutil.ZombieProcess):
                continue
        return False

    @staticmethod
    def get_process_by_name(process_name: str) -> Optional[psutil.Process]:
        """Find the first matching psutil.Process instance."""
        target_name = process_name.lower()
        if not target_name.endswith(".exe"):
            target_name += ".exe"

        for proc in psutil.process_iter(["name"]):
            try:
                if proc.info["name"] and proc.info["name"].lower() == target_name:
                    return proc
            except (psutil.NoSuchProcess, psutil.AccessDenied, psutil.ZombieProcess):
                continue
        return None

    @staticmethod
    def launch_process(
        executable_path: str,
        arguments: Optional[List[str]] = None,
        working_dir: Optional[str] = None,
    ) -> subprocess.Popen:
        """Launch an application executable."""
        exec_path = os.path.expandvars(executable_path)
        if not os.path.exists(exec_path):
            raise FileNotFoundError(f"Executable path not found: {exec_path}")

        cmd = [exec_path] + (arguments or [])
        cwd = working_dir or os.path.dirname(exec_path)

        logger.info(f"Launching process: {cmd} (cwd={cwd})")
        process = subprocess.Popen(cmd, cwd=cwd, shell=False)
        return process

    @staticmethod
    def terminate_process(process_name: str, force: bool = False) -> bool:
        """Terminate processes matching process_name."""
        proc = ProcessManager.get_process_by_name(process_name)
        if not proc:
            return False

        try:
            if force:
                proc.kill()
            else:
                proc.terminate()
            proc.wait(timeout=5)
            logger.info(f"Terminated process '{process_name}'")
            return True
        except (psutil.TimeoutExpired, psutil.NoSuchProcess, psutil.AccessDenied) as e:
            logger.warning(f"Error terminating process '{process_name}': {e}")
            if not force:
                return ProcessManager.terminate_process(process_name, force=True)
            return False

    @staticmethod
    def wait_for_process(process_name: str, timeout: float = 30.0, check_interval: float = 0.5) -> bool:
        """Poll until a process matching process_name appears or timeout expires."""
        start_time = time.time()
        while time.time() - start_time < timeout:
            if ProcessManager.is_process_running(process_name):
                return True
            time.sleep(check_interval)
        return False

    @staticmethod
    def auto_discover_app_path(app_key: str) -> Optional[str]:
        """Try discovering executable path or shortcut for well-known applications on Windows."""
        key = app_key.lower().strip()
        local_appdata = os.environ.get("LOCALAPPDATA", "")
        appdata = os.environ.get("APPDATA", "")
        program_files = os.environ.get("ProgramFiles", r"C:\Program Files")
        program_files_x86 = os.environ.get("ProgramFiles(x86)", r"C:\Program Files (x86)")

        # Step 0: Check DEDICATED_MODES directory in workspace
        root_dir = Path(__file__).resolve().parent.parent.parent
        dedicated_dir = root_dir / "DEDICATED_MODES"
        if dedicated_dir.exists():
            for root_path, _, files in os.walk(dedicated_dir):
                for f in files:
                    if key in f.lower():
                        full_f = os.path.join(root_path, f)
                        logger.info(f"Discovered '{app_key}' in DEDICATED_MODES: {full_f}")
                        return full_f

        candidate_paths = []

        # 1. Discord
        if "discord" in key:
            if local_appdata:
                # Find latest app-1.0.xxxx/Discord.exe
                matches = glob.glob(os.path.join(local_appdata, "Discord", "app-*", "Discord.exe"))
                if matches:
                    matches.sort(reverse=True)
                    return matches[0]
                update_exe = os.path.join(local_appdata, "Discord", "Update.exe")
                if os.path.exists(update_exe):
                    return update_exe

        # 2. Steam
        if "steam" in key:
            try:
                with winreg.OpenKey(winreg.HKEY_CURRENT_USER, r"SOFTWARE\Valve\Steam") as k:
                    spath, _ = winreg.QueryValueEx(k, "SteamPath")
                    sexe = os.path.join(spath, "steam.exe")
                    if os.path.exists(sexe):
                        return sexe
            except Exception:
                pass

            candidate_paths.extend([
                os.path.join(program_files_x86, r"Steam\steam.exe"),
                os.path.join(program_files, r"Steam\steam.exe"),
                r"D:\Steam\steam.exe",
                r"D:\Program Files (x86)\Steam\steam.exe",
                r"E:\Steam\steam.exe",
            ])

        # 3. Spotify
        if "spotify" in key:
            candidate_paths.extend([
                os.path.join(appdata, r"Spotify\Spotify.exe"),
                os.path.join(local_appdata, r"Microsoft\WindowsApps\Spotify.exe"),
            ])

        # 4. VS Code
        if "vscode" in key or "code" in key:
            candidate_paths.extend([
                os.path.join(local_appdata, r"Programs\Microsoft VS Code\Code.exe"),
                os.path.join(program_files, r"Microsoft VS Code\Code.exe"),
            ])

        # 5. FL Studio
        if "fl" in key or "studio" in key:
            candidate_paths.extend([
                r"C:\Program Files\Image-Line\FL Studio 2024\FL64.exe",
                r"C:\Program Files\Image-Line\FL Studio 21\FL64.exe",
                r"C:\Program Files\Image-Line\FL Studio 20\FL64.exe",
                r"C:\Program Files (x86)\Image-Line\FL Studio 20\FL.exe",
                r"D:\Program Files\Image-Line\FL Studio 2024\FL64.exe",
            ])

        # Check candidate paths
        for path in candidate_paths:
            if path and os.path.exists(path):
                return path

        # 6. Windows App Paths Registry Search
        exe_name = key if key.endswith(".exe") else f"{key}.exe"
        for root in [winreg.HKEY_CURRENT_USER, winreg.HKEY_LOCAL_MACHINE]:
            try:
                reg_path = rf"SOFTWARE\Microsoft\Windows\CurrentVersion\App Paths\{exe_name}"
                with winreg.OpenKey(root, reg_path) as k:
                    val, _ = winreg.QueryValueEx(k, "")
                    if val and os.path.exists(val):
                        return val
            except Exception:
                pass

        # 7. Start Menu shortcuts (.lnk search)
        start_menu_dirs = [
            os.path.join(appdata, r"Microsoft\Windows\Start Menu\Programs"),
            r"C:\ProgramData\Microsoft\Windows\Start Menu\Programs",
        ]
        for sm_dir in start_menu_dirs:
            if os.path.exists(sm_dir):
                for root_path, _, files in os.walk(sm_dir):
                    for f in files:
                        if f.lower().endswith(".lnk") and key in f.lower():
                            full_f = os.path.join(root_path, f)
                            logger.info(f"Discovered '{app_key}' in Start Menu: {full_f}")
                            return full_f

        return None
