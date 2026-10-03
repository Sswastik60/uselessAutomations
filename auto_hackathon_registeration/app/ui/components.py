"""AMOLED Monochrome Design System and Custom PySide6 Components for HackFill."""

from PySide6.QtWidgets import (
    QWidget, QPushButton, QLabel, QFrame, QVBoxLayout, QHBoxLayout,
    QProgressBar, QTableWidget, QTableWidgetItem, QHeaderView, QLineEdit,
    QComboBox, QSpinBox, QCheckBox
)
from PySide6.QtCore import Qt, Signal
from PySide6.QtGui import QFont, QColor


# Strict Monochrome AMOLED Color Palette (No purple, no blue, no neon, no gradients)
COLOR_BG_BLACK = "#09090B"       # Deep AMOLED black
COLOR_BG_SURFACE = "#121215"     # Primary surface
COLOR_BG_CARD = "#18181B"        # Card background
COLOR_BG_HOVER = "#27272A"       # Subtle hover
COLOR_BORDER = "#27272A"         # Subtle border
COLOR_BORDER_LIGHT = "#3F3F46"   # Active/focus border
COLOR_TEXT_WHITE = "#FAFAFA"     # Primary text
COLOR_TEXT_MUTED = "#A1A1AA"     # Secondary text
COLOR_TEXT_DIM = "#71717A"       # Tertiary / placeholder text
COLOR_WHITE = "#FFFFFF"          # High-contrast action white
COLOR_DARK = "#000000"           # Pure black text for white buttons

GLOBAL_STYLE_SHEET = f"""
QMainWindow, QWidget {{
    background-color: {COLOR_BG_BLACK};
    color: {COLOR_TEXT_WHITE};
    font-family: -apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, Helvetica, Arial, sans-serif;
    font-size: 13px;
}}

/* Scrollbars */
QScrollBar:vertical {{
    background: {COLOR_BG_BLACK};
    width: 8px;
    margin: 0;
}}
QScrollBar::handle:vertical {{
    background: {COLOR_BORDER};
    min-height: 20px;
    border-radius: 4px;
}}
QScrollBar::handle:vertical:hover {{
    background: {COLOR_TEXT_DIM};
}}
QScrollBar::add-line:vertical, QScrollBar::sub-line:vertical {{
    height: 0px;
}}

/* Line Edits */
QLineEdit {{
    background-color: {COLOR_BG_SURFACE};
    color: {COLOR_TEXT_WHITE};
    border: 1px solid {COLOR_BORDER};
    border-radius: 6px;
    padding: 10px 14px;
    font-size: 13px;
    selection-background-color: {COLOR_TEXT_MUTED};
    selection-color: {COLOR_DARK};
}}
QLineEdit:focus {{
    border: 1px solid {COLOR_TEXT_MUTED};
}}
QLineEdit:disabled {{
    background-color: {COLOR_BG_BLACK};
    color: {COLOR_TEXT_DIM};
    border-color: {COLOR_BG_SURFACE};
}}

/* Combo Boxes */
QComboBox {{
    background-color: {COLOR_BG_SURFACE};
    color: {COLOR_TEXT_WHITE};
    border: 1px solid {COLOR_BORDER};
    border-radius: 6px;
    padding: 8px 12px;
    font-size: 13px;
}}
QComboBox:hover {{
    border-color: {COLOR_BORDER_LIGHT};
}}
QComboBox::drop-down {{
    border: none;
    padding-right: 10px;
}}
QComboBox QAbstractItemView {{
    background-color: {COLOR_BG_CARD};
    color: {COLOR_TEXT_WHITE};
    border: 1px solid {COLOR_BORDER};
    selection-background-color: {COLOR_BG_HOVER};
    selection-color: {COLOR_WHITE};
    padding: 4px;
}}

/* Spin Boxes */
QSpinBox {{
    background-color: {COLOR_BG_SURFACE};
    color: {COLOR_TEXT_WHITE};
    border: 1px solid {COLOR_BORDER};
    border-radius: 6px;
    padding: 8px 12px;
}}

/* Checkboxes */
QCheckBox {{
    color: {COLOR_TEXT_WHITE};
    spacing: 8px;
}}
QCheckBox::indicator {{
    width: 18px;
    height: 18px;
    border: 1px solid {COLOR_BORDER};
    border-radius: 4px;
    background-color: {COLOR_BG_SURFACE};
}}
QCheckBox::indicator:hover {{
    border-color: {COLOR_BORDER_LIGHT};
}}
QCheckBox::indicator:checked {{
    background-color: {COLOR_WHITE};
    border-color: {COLOR_WHITE};
    image: none;
}}

/* Tables */
QTableWidget {{
    background-color: {COLOR_BG_SURFACE};
    border: 1px solid {COLOR_BORDER};
    border-radius: 8px;
    gridline-color: {COLOR_BORDER};
    color: {COLOR_TEXT_WHITE};
    selection-background-color: {COLOR_BG_HOVER};
    selection-color: {COLOR_WHITE};
}}
QHeaderView::section {{
    background-color: {COLOR_BG_CARD};
    color: {COLOR_TEXT_MUTED};
    padding: 8px 12px;
    border: none;
    border-bottom: 1px solid {COLOR_BORDER};
    font-weight: 600;
    font-size: 12px;
    text-transform: uppercase;
    letter-spacing: 0.5px;
}}
"""


class CardFrame(QFrame):
    """Clean, restrained card container with subtle monochrome border."""
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setStyleSheet(f"""
            CardFrame {{
                background-color: {COLOR_BG_CARD};
                border: 1px solid {COLOR_BORDER};
                border-radius: 8px;
            }}
        """)


class PrimaryButton(QPushButton):
    """High-contrast solid white action button with black text."""
    def __init__(self, text: str, parent=None):
        super().__init__(text, parent)
        self.setCursor(Qt.PointingHandCursor)
        self.setFont(QFont("-apple-system", 11, QFont.DemiBold))
        self.setStyleSheet(f"""
            QPushButton {{
                background-color: {COLOR_WHITE};
                color: {COLOR_DARK};
                border: none;
                border-radius: 6px;
                padding: 10px 20px;
                font-weight: 600;
            }}
            QPushButton:hover {{
                background-color: #E4E4E7;
            }}
            QPushButton:pressed {{
                background-color: #D4D4D8;
            }}
            QPushButton:disabled {{
                background-color: {COLOR_BORDER};
                color: {COLOR_TEXT_DIM};
            }}
        """)


class SecondaryButton(QPushButton):
    """Subtle outline monochrome button."""
    def __init__(self, text: str, parent=None):
        super().__init__(text, parent)
        self.setCursor(Qt.PointingHandCursor)
        self.setFont(QFont("-apple-system", 10, QFont.Medium))
        self.setStyleSheet(f"""
            QPushButton {{
                background-color: {COLOR_BG_SURFACE};
                color: {COLOR_TEXT_WHITE};
                border: 1px solid {COLOR_BORDER};
                border-radius: 6px;
                padding: 8px 16px;
            }}
            QPushButton:hover {{
                background-color: {COLOR_BG_HOVER};
                border-color: {COLOR_BORDER_LIGHT};
            }}
            QPushButton:pressed {{
                background-color: {COLOR_BG_BLACK};
            }}
            QPushButton:disabled {{
                background-color: {COLOR_BG_BLACK};
                color: {COLOR_TEXT_DIM};
                border-color: {COLOR_BG_SURFACE};
            }}
        """)


class DangerButton(QPushButton):
    """Restrained danger/stop button adhering strictly to monochrome aesthetic."""
    def __init__(self, text: str, parent=None):
        super().__init__(text, parent)
        self.setCursor(Qt.PointingHandCursor)
        self.setFont(QFont("-apple-system", 10, QFont.DemiBold))
        self.setStyleSheet(f"""
            QPushButton {{
                background-color: {COLOR_BG_SURFACE};
                color: {COLOR_WHITE};
                border: 1px solid {COLOR_BORDER_LIGHT};
                border-radius: 6px;
                padding: 8px 18px;
                font-weight: 600;
            }}
            QPushButton:hover {{
                background-color: {COLOR_BORDER_LIGHT};
                color: {COLOR_WHITE};
            }}
            QPushButton:pressed {{
                background-color: {COLOR_BG_BLACK};
            }}
        """)


class BadgeLabel(QLabel):
    """Monochrome badge indicator for statuses."""
    def __init__(self, text: str, level: str = "INFO", parent=None):
        super().__init__(text, parent)
        self.setAlignment(Qt.AlignCenter)
        self.setFont(QFont("Consolas", 9, QFont.Bold))
        self.set_level(level, text)

    def set_level(self, level: str, text: str = ""):
        if text:
            self.setText(text)

        if level == "SUCCESS":
            self.setStyleSheet(f"""
                QLabel {{
                    background-color: {COLOR_WHITE};
                    color: {COLOR_DARK};
                    border-radius: 4px;
                    padding: 3px 8px;
                    font-weight: bold;
                }}
            """)
        elif level == "WARNING":
            self.setStyleSheet(f"""
                QLabel {{
                    background-color: {COLOR_BG_HOVER};
                    color: {COLOR_TEXT_WHITE};
                    border: 1px solid {COLOR_BORDER_LIGHT};
                    border-radius: 4px;
                    padding: 3px 8px;
                    font-weight: bold;
                }}
            """)
        elif level == "ERROR":
            self.setStyleSheet(f"""
                QLabel {{
                    background-color: {COLOR_BG_SURFACE};
                    color: {COLOR_WHITE};
                    border: 1px solid {COLOR_WHITE};
                    border-radius: 4px;
                    padding: 3px 8px;
                    font-weight: bold;
                }}
            """)
        else:  # INFO / READY
            self.setStyleSheet(f"""
                QLabel {{
                    background-color: {COLOR_BG_SURFACE};
                    color: {COLOR_TEXT_MUTED};
                    border: 1px solid {COLOR_BORDER};
                    border-radius: 4px;
                    padding: 3px 8px;
                }}
            """)


class MonochromeProgressBar(QProgressBar):
    """Minimal progress bar using pure monochrome styling."""
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setTextVisible(False)
        self.setFixedHeight(6)
        self.setStyleSheet(f"""
            QProgressBar {{
                background-color: {COLOR_BG_SURFACE};
                border: 1px solid {COLOR_BORDER};
                border-radius: 3px;
            }}
            QProgressBar::chunk {{
                background-color: {COLOR_WHITE};
                border-radius: 2px;
            }}
        """)
