import logging
from typing import Optional
from PySide6.QtWidgets import QSystemTrayIcon

logger = logging.getLogger(__name__)


class NotificationService:
    """Dispatches desktop toast / tray notifications."""

    def __init__(self, tray_icon: Optional[QSystemTrayIcon] = None):
        self.tray_icon = tray_icon

    def set_tray_icon(self, tray_icon: QSystemTrayIcon) -> None:
        self.tray_icon = tray_icon

    def show_notification(
        self,
        title: str,
        message: str,
        icon: QSystemTrayIcon.MessageIcon = QSystemTrayIcon.Information,
        timeout_ms: int = 4000,
    ) -> None:
        logger.info(f"NOTIFICATION [{title}]: {message}")
        if self.tray_icon and self.tray_icon.supportsMessages():
            try:
                self.tray_icon.showMessage(title, message, icon, timeout_ms)
            except Exception as e:
                logger.error(f"Error displaying tray notification: {e}")
