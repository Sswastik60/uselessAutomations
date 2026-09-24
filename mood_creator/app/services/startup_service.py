import sys
import winreg
import logging

logger = logging.getLogger(__name__)

REG_PATH = r"Software\Microsoft\Windows\CurrentVersion\Run"
APP_NAME = "AutomationHub"


class StartupService:
    """Manages Windows startup registry autostart entry."""

    @staticmethod
    def set_start_with_windows(enable: bool) -> bool:
        """Add or remove Windows startup registry entry."""
        try:
            key = winreg.OpenKey(winreg.HKEY_CURRENT_USER, REG_PATH, 0, winreg.KEY_ALL_ACCESS)
            if enable:
                # Resolve current python executable or built exe
                exe_path = sys.executable
                if not getattr(sys, 'frozen', False):
                    # Running from python script, launch pythonw run.py
                    script_path = sys.argv[0]
                    cmd = f'"{exe_path}" "{script_path}" --minimized'
                else:
                    cmd = f'"{exe_path}" --minimized'

                winreg.SetValueEx(key, APP_NAME, 0, winreg.REG_SZ, cmd)
                logger.info(f"Registered Windows startup command: {cmd}")
            else:
                try:
                    winreg.DeleteValue(key, APP_NAME)
                    logger.info("Removed Windows startup registry entry")
                except FileNotFoundError:
                    pass
            winreg.CloseKey(key)
            return True
        except Exception as e:
            logger.error(f"Failed to update Windows autostart registry setting: {e}")
            return False

    @staticmethod
    def is_autostart_enabled() -> bool:
        """Check if startup registry value exists."""
        try:
            key = winreg.OpenKey(winreg.HKEY_CURRENT_USER, REG_PATH, 0, winreg.KEY_READ)
            val, _ = winreg.QueryValueEx(key, APP_NAME)
            winreg.CloseKey(key)
            return bool(val)
        except FileNotFoundError:
            return False
        except Exception:
            return False
