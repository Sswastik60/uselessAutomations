"""Dynamic Theme Manager for Dark, Light, and System themes without app restart."""

import logging
from typing import Optional
from PySide6.QtCore import QObject, Signal
from PySide6.QtWidgets import QApplication

from app.ui.design.tokens import DarkPalette, LightPalette

logger = logging.getLogger(__name__)


class ThemeManager(QObject):
    """Singleton Theme Manager handling application-wide QSS updates live."""

    theme_changed = Signal(str)  # "dark" or "light"
    _instance: Optional["ThemeManager"] = None

    def __init__(self):
        super().__init__()
        ThemeManager._instance = self
        self.current_theme = "dark"

    @classmethod
    def get_instance(cls) -> "ThemeManager":
        if cls._instance is None:
            cls._instance = ThemeManager()
        return cls._instance

    def set_theme(self, theme_mode: str) -> None:
        """Apply theme ('dark', 'light', or 'system') to QApplication."""
        mode = theme_mode.lower().strip()
        if mode not in ("dark", "light", "system"):
            mode = "dark"

        if mode == "system":
            mode = "dark"  # Default system preference to dark on Windows 11 control center

        self.current_theme = mode
        qss = self.generate_stylesheet(mode)

        app = QApplication.instance()
        if app:
            app.setStyleSheet(qss)
            logger.info(f"Applied live theme: {mode}")

        self.theme_changed.emit(mode)

    def generate_stylesheet(self, theme_mode: str) -> str:
        """Generate high-precision QSS matching the design tokens."""
        p = DarkPalette if theme_mode == "dark" else LightPalette

        return f"""
        /* ===================================================================
           Windows 11 Personal Control Center Theme — {theme_mode.upper()}
           =================================================================== */

        QMainWindow, QDialog {{
            background-color: {p.BG_BASE};
            color: {p.TEXT_PRIMARY};
            font-family: 'Segoe UI Variable Display', 'Segoe UI', system-ui, -apple-system, sans-serif;
        }}

        QWidget {{
            color: {p.TEXT_PRIMARY};
            font-family: 'Segoe UI Variable Text', 'Segoe UI', system-ui, -apple-system, sans-serif;
            font-size: 13px;
        }}

        /* Tooltips */
        QToolTip {{
            background-color: {p.SURFACE_ELEVATED};
            color: {p.TEXT_PRIMARY};
            border: 1px solid {p.BORDER_FOCUS};
            border-radius: 6px;
            padding: 6px 10px;
            font-size: 12px;
        }}

        /* Sidebar Navigation Container */
        #SidebarWidget {{
            background-color: {p.BG_DARKEST};
            border-right: 1px solid {p.BORDER_SUBTLE};
        }}

        /* Navigation Buttons */
        QPushButton.NavButton {{
            background-color: transparent;
            border: none;
            border-radius: 8px;
            padding: 10px 14px;
            text-align: left;
            font-size: 13px;
            font-weight: 600;
            color: {p.TEXT_SECONDARY};
        }}

        QPushButton.NavButton:hover {{
            background-color: {p.SURFACE_INTERACTIVE};
            color: {p.TEXT_PRIMARY};
        }}

        QPushButton.NavButton:checked, QPushButton.NavButton.active {{
            background-color: {p.ACCENT_PRIMARY};
            color: #ffffff;
            font-weight: 700;
        }}

        /* Mode Cards */
        QFrame.ModeCard {{
            background-color: {p.SURFACE_PRIMARY};
            border: 1px solid {p.BORDER_SUBTLE};
            border-radius: 16px;
        }}

        QFrame.ModeCard:hover {{
            background-color: {p.SURFACE_ELEVATED};
            border: 1px solid {p.ACCENT_LIGHT};
        }}

        /* Standard Buttons */
        QPushButton.PrimaryButton {{
            background-color: {p.ACCENT_PRIMARY};
            color: #ffffff;
            border: none;
            border-radius: 8px;
            padding: 9px 18px;
            font-size: 13px;
            font-weight: 700;
        }}

        QPushButton.PrimaryButton:hover {{
            background-color: {p.ACCENT_HOVER};
        }}

        QPushButton.PrimaryButton:pressed {{
            background-color: #075985;
        }}

        QPushButton.SecondaryButton {{
            background-color: {p.SURFACE_ELEVATED};
            color: {p.TEXT_PRIMARY};
            border: 1px solid {p.BORDER_DEFAULT};
            border-radius: 8px;
            padding: 8px 16px;
            font-size: 13px;
            font-weight: 600;
        }}

        QPushButton.SecondaryButton:hover {{
            background-color: {p.SURFACE_INTERACTIVE};
            border-color: {p.TEXT_MUTED};
        }}

        QPushButton.DangerButton {{
            background-color: {p.ERROR_BG};
            color: #ffffff;
            border: 1px solid {p.ERROR};
            border-radius: 8px;
            padding: 8px 16px;
            font-weight: 600;
        }}

        QPushButton.DangerButton:hover {{
            background-color: {p.ERROR};
        }}

        /* Form Inputs */
        QLineEdit, QSpinBox, QComboBox, QTextEdit {{
            background-color: {p.SURFACE_PRIMARY};
            border: 1px solid {p.BORDER_DEFAULT};
            border-radius: 8px;
            padding: 8px 12px;
            color: {p.TEXT_PRIMARY};
            selection-background-color: {p.ACCENT_PRIMARY};
            font-size: 13px;
        }}

        QLineEdit:focus, QComboBox:focus, QTextEdit:focus, QSpinBox:focus {{
            border: 1px solid {p.ACCENT_LIGHT};
            background-color: {p.SURFACE_ELEVATED};
        }}

        QComboBox QAbstractItemView {{
            background-color: {p.SURFACE_ELEVATED};
            color: {p.TEXT_PRIMARY};
            border: 1px solid {p.BORDER_DEFAULT};
            selection-background-color: {p.ACCENT_PRIMARY};
            border-radius: 6px;
            padding: 4px;
        }}

        /* Checkboxes */
        QCheckBox {{
            spacing: 8px;
            font-size: 13px;
            color: {p.TEXT_PRIMARY};
        }}

        QCheckBox::indicator {{
            width: 18px;
            height: 18px;
            border-radius: 5px;
            border: 1px solid {p.BORDER_DEFAULT};
            background-color: {p.SURFACE_PRIMARY};
        }}

        QCheckBox::indicator:checked {{
            background-color: {p.ACCENT_PRIMARY};
            border: 1px solid {p.ACCENT_LIGHT};
        }}

        /* Scrollbars */
        QScrollBar:vertical {{
            background: transparent;
            width: 8px;
            margin: 0px;
        }}

        QScrollBar::handle:vertical {{
            background: {p.SURFACE_INTERACTIVE};
            min-height: 24px;
            border-radius: 4px;
        }}

        QScrollBar::handle:vertical:hover {{
            background: {p.TEXT_MUTED};
        }}

        QScrollBar::add-line:vertical, QScrollBar::sub-line:vertical {{
            height: 0px;
        }}

        /* Progress Bar */
        QProgressBar {{
            background-color: {p.SURFACE_PRIMARY};
            border: 1px solid {p.BORDER_SUBTLE};
            border-radius: 6px;
            height: 14px;
            text-align: center;
            color: transparent;
        }}

        QProgressBar::chunk {{
            background-color: {p.ACCENT_PRIMARY};
            border-radius: 5px;
        }}
        """
