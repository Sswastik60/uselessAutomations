"""Centralized Design System Tokens for Windows 11 Automation Hub."""

from PySide6.QtCore import QEasingCurve


class Spacing:
    XS = 4
    SM = 8
    MD = 16
    LG = 24
    XL = 32


class Radius:
    SM = 6
    MD = 10
    LG = 14
    XL = 20


class AnimationDuration:
    FAST = 120    # Micro-interactions (hover, active state, press)
    NORMAL = 200  # Card hover, button state transition, toast slide
    PANEL = 250   # Sidebar collapse/expand, modal overlay
    PAGE = 300    # Page transitions, command palette
    SLOW = 400    # Mode completion pulse, success checkmark reveal


class AnimationEasing:
    FAST_OUT = QEasingCurve.Type.OutCubic
    SMOOTH = QEasingCurve.Type.OutQuart
    BOUNCE_SUBTLE = QEasingCurve.Type.OutBack
    EASE_IN_OUT = QEasingCurve.Type.InOutCubic


class Typography:
    FONT_FAMILY = "'Segoe UI Variable Display', 'Segoe UI', -apple-system, sans-serif"
    MONO_FONT = "'Consolas', 'Segoe UI Mono', monospace"

    DISPLAY = 24
    TITLE = 20
    HEADING = 16
    SUBHEADING = 14
    BODY = 13
    CAPTION = 11
    MICRO = 10


class DarkPalette:
    BG_DARKEST = "#000000"
    BG_BASE = "#050505"
    BG_SURFACE = "#0a0a0a"
    BG_CARD = "#0d0d0d"
    BG_HOVER = "#141824"
    BG_ACTIVE = "#1e293b"

    BORDER_SUBTLE = "#181818"
    BORDER_DEFAULT = "#262626"
    BORDER_FOCUS = "#0284c7"
    BORDER_ACCENT = "#38bdf8"

    TEXT_PRIMARY = "#f8fafc"
    TEXT_SECONDARY = "#94a3b8"
    TEXT_MUTED = "#64748b"

    ACCENT_PRIMARY = "#0284c7"
    ACCENT_HOVER = "#0369a1"
    ACCENT_LIGHT = "#38bdf8"
    ACCENT_GRADIENT = "qlineargradient(x1:0, y1:0, x2:1, y2:0, stop:0 #0284c7, stop:1 #06b6d4)"

    SUCCESS = "#10b981"
    SUCCESS_BG = "#064e3b"
    WARNING = "#f59e0b"
    WARNING_BG = "#78350f"
    ERROR = "#ef4444"
    ERROR_BG = "#7f1d1d"


class LightPalette:
    BG_DARKEST = "#f8fafc"
    BG_BASE = "#ffffff"
    BG_SURFACE = "#f1f5f9"
    BG_CARD = "#ffffff"
    BG_HOVER = "#e2e8f0"
    BG_ACTIVE = "#cbd5e1"

    BORDER_SUBTLE = "#e2e8f0"
    BORDER_DEFAULT = "#cbd5e1"
    BORDER_FOCUS = "#0284c7"
    BORDER_ACCENT = "#0284c7"

    TEXT_PRIMARY = "#0f172a"
    TEXT_SECONDARY = "#475569"
    TEXT_MUTED = "#64748b"

    ACCENT_PRIMARY = "#0284c7"
    ACCENT_HOVER = "#0369a1"
    ACCENT_LIGHT = "#38bdf8"
    ACCENT_GRADIENT = "qlineargradient(x1:0, y1:0, x2:1, y2:0, stop:0 #0284c7, stop:1 #0284c7)"

    SUCCESS = "#10b981"
    SUCCESS_BG = "#d1fae5"
    WARNING = "#d97706"
    WARNING_BG = "#fef3c7"
    ERROR = "#dc2626"
    ERROR_BG = "#fee2e2"
