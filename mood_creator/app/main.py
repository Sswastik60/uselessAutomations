import argparse
import logging
import os
import sys
from pathlib import Path

from PySide6.QtCore import Qt
from PySide6.QtWidgets import QApplication

import app.actions  # Ensure all automation actions are registered
from app.ui.main_window import MainWindow


def setup_logging(log_dir: Path) -> None:
    log_dir.mkdir(parents=True, exist_ok=True)
    log_file = log_dir / "automation_hub.log"

    logging.basicConfig(
        level=logging.INFO,
        format="%(asctime)s [%(levelname)s] %(name)s: %(message)s",
        handlers=[
            logging.FileHandler(log_file, encoding="utf-8"),
            logging.StreamHandler(sys.stdout),
        ],
    )
    logging.info("Initializing Windows 11 Automation Hub")


def main() -> None:
    parser = argparse.ArgumentParser(description="Windows 11 Automation Hub")
    parser.add_argument("--minimized", action="store_true", help="Start application minimized in system tray")
    args = parser.parse_args()

    # Enable High DPI scaling
    QApplication.setHighDpiScaleFactorRoundingPolicy(
        Qt.HighDpiScaleFactorRoundingPolicy.PassThrough
    )
    
    app = QApplication(sys.argv)
    app.setApplicationName("Windows 11 Automation Hub")
    app.setOrganizationName("AutomationHub")

    if getattr(sys, "frozen", False) and hasattr(sys, "_MEIPASS"):
        app_dir = Path(sys._MEIPASS)
    else:
        app_dir = Path(__file__).resolve().parent.parent
    user_appdata = Path(os.environ.get("APPDATA", ".")) / "AutomationHub"
    setup_logging(user_appdata / "logs")

    window = MainWindow(app_dir=app_dir)

    if not args.minimized and not window.settings_store.settings.launch_minimized:
        window.show()
    else:
        logging.info("Application started minimized in system tray.")

    sys.exit(app.exec())


if __name__ == "__main__":
    main()
