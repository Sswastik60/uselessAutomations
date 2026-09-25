import argparse
import logging
import os
import sys
import time
from pathlib import Path

from PySide6.QtCore import Qt
from PySide6.QtGui import QIcon
from PySide6.QtNetwork import QLocalServer, QLocalSocket
from PySide6.QtWidgets import QApplication, QMessageBox

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


def setup_crash_handler(log_dir: Path) -> None:
    crash_file = log_dir / "crash.log"

    def excepthook(exc_type, exc_value, exc_traceback):
        if issubclass(exc_type, KeyboardInterrupt):
            sys.__excepthook__(exc_type, exc_value, exc_traceback)
            return

        import traceback
        err_msg = "".join(traceback.format_exception(exc_type, exc_value, exc_traceback))
        logging.critical(f"Unhandled Exception:\n{err_msg}")
        try:
            with open(crash_file, "a", encoding="utf-8") as f:
                f.write(f"\n--- CRASH AT {time.ctime()} ---\n")
                f.write(err_msg)
        except Exception:
            pass

        if QApplication.instance():
            try:
                QMessageBox.critical(
                    None,
                    "Automation Hub Error",
                    f"An unexpected error occurred:\n\n{exc_value}\n\nCheck logs for details:\n{crash_file}",
                )
            except Exception:
                pass

    sys.excepthook = excepthook


def main() -> None:
    parser = argparse.ArgumentParser(description="Windows 11 Automation Hub")
    parser.add_argument("--minimized", action="store_true", help="Start application minimized in system tray")
    args = parser.parse_args()

    # Enable High DPI scaling
    QApplication.setHighDpiScaleFactorRoundingPolicy(
        Qt.HighDpiScaleFactorRoundingPolicy.PassThrough
    )

    app = QApplication(sys.argv)
    app.setQuitOnLastWindowClosed(False)
    app.setApplicationName("Windows 11 Automation Hub")
    app.setOrganizationName("AutomationHub")

    if getattr(sys, "frozen", False) and hasattr(sys, "_MEIPASS"):
        app_dir = Path(sys._MEIPASS)
    else:
        app_dir = Path(__file__).resolve().parent.parent

    user_appdata = Path(os.environ.get("APPDATA", ".")) / "AutomationHub"
    logs_dir = user_appdata / "logs"
    setup_logging(logs_dir)
    setup_crash_handler(logs_dir)

    # Single-instance enforcement via local socket
    pipe_name = "AutomationHub_SingleInstance_Pipe"
    socket = QLocalSocket()
    socket.connectToServer(pipe_name)
    if socket.waitForConnected(500):
        logging.info("Existing instance detected. Requesting window activation and exiting.")
        socket.write(b"show\n")
        socket.waitForBytesWritten(500)
        socket.disconnectFromServer()
        sys.exit(0)

    # Set Application Icon
    icon_path = app_dir / "assets" / "app_icon.png"
    if not icon_path.exists():
        icon_path = app_dir / "assets" / "app_icon.ico"
    if icon_path.exists():
        app.setWindowIcon(QIcon(str(icon_path)))

    window = MainWindow(app_dir=app_dir)

    # Primary instance: listen for wake-up requests from secondary launches
    server = QLocalServer()
    QLocalServer.removeServer(pipe_name)
    server.listen(pipe_name)

    def _on_new_connection():
        client = server.nextPendingConnection()
        if client:
            client.waitForReadyRead(500)
            msg = bytes(client.readAll()).decode("utf-8").strip()
            if "show" in msg or not msg:
                window.show_window()
            client.disconnectFromServer()

    server.newConnection.connect(_on_new_connection)

    if not args.minimized and not window.settings_store.settings.launch_minimized:
        window.show_window()
    else:
        logging.info("Application started minimized in system tray.")

    ret = app.exec()
    try:
        server.close()
    except Exception:
        pass
    sys.exit(0 if ret == 0 else ret)



if __name__ == "__main__":
    main()
