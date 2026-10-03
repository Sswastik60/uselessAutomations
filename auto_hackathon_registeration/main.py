"""HackFill - Hackathon Form Filler.
Tagline: Fill hackathon registrations in seconds.

Main desktop application entry point.
"""

import sys
import os
from pathlib import Path
from PySide6.QtWidgets import QApplication
from PySide6.QtCore import Qt

# Ensure local project root is on Python sys.path
PROJECT_ROOT = Path(__file__).resolve().parent
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from app.ui.main_window import MainWindow
from app.services.logger import get_logger


def main():
    # Enable high-DPI awareness
    os.environ["QT_AUTO_SCREEN_SCALE_FACTOR"] = "1"

    app = QApplication(sys.argv)
    app.setApplicationName("HackFill")
    app.setOrganizationName("HackFill")
    app.setApplicationVersion("1.0.0")

    logger = get_logger()
    logger.info("Initializing HackFill Desktop Application...")

    window = MainWindow()
    window.show()

    logger.info("HackFill ready. Engine initialized.")
    sys.exit(app.exec())


if __name__ == "__main__":
    main()
