"""Centralized Design System Tokens for Windows 11 Automation Hub."""

from PySide6.QtCore import QEasingCurve


class Spacing:
    """Consistent 4px/8px rhythm spacing scale."""
    XXS = 2
    XS = 4
    SM = 8
    MD = 12
    LG = 16
    XL = 24
    XXL = 32
    HUGE = 48


class Radius:
    """Hierarchy of corner radii for controls vs cards vs surfaces."""
    CONTROL = 6      # Inputs, small buttons, badges
    BUTTON = 8       # Standard buttons
    CARD = 14        # Interactive Mode cards, dialogs
    SURFACE = 18     # Large panels, HUD overlay
    HERO = 24        # Hero containers


class Duration:
    """Restrained animation timing (in milliseconds)."""
    MICRO = 100       # Hover elevation, active state, press compression
    BUTTON = 140      # Button state feedback
    CARD = 180        # Card hover lift & scale
    PANEL = 220       # Sidebar collapse/expand, modal overlay entrance
    PAGE = 280        # Page transitions
    EXECUTION = 350   # Action state step transition (○ -> ◌ -> ✓)


class Easing:
    """Natural easing curves for physical feel."""
    OUT_CUBIC = QEasingCurve.Type.OutCubic
    OUT_QUART = QEasingCurve.Type.OutQuart
    IN_OUT_CUBIC = QEasingCurve.Type.InOutCubic
    OUT_BACK = QEasingCurve.Type.OutBack


class TypographyScale:
    """Typography hierarchy (Segoe UI Variable / System)."""
    FONT_FAMILY = "'Segoe UI Variable Display', 'Segoe UI', -apple-system, sans-serif"
    MONO_FONT = "'Segoe UI Variable Text', 'Consolas', monospace"

    DISPLAY = 32
    PAGE_TITLE = 24
    SECTION_TITLE = 18
    CARD_TITLE = 16
    BODY = 14
    SECONDARY = 12
    CAPTION = 11


class DarkPalette:
    """True AMOLED Layered Surface Dark Theme (Pure black, high contrast, luminous cyan accents)."""
    BG_DARKEST = "#000000"
    BG_BASE = "#040405"
    SURFACE_PRIMARY = "#09090b"
    SURFACE_ELEVATED = "#111115"
    SURFACE_INTERACTIVE = "#17171d"
    SURFACE_HOVER = "#1f1f26"

    BORDER_SUBTLE = "rgba(255, 255, 255, 0.07)"
    BORDER_DEFAULT = "rgba(255, 255, 255, 0.13)"
    BORDER_FOCUS = "#38bdf8"

    TEXT_PRIMARY = "#f8fafc"
    TEXT_SECONDARY = "#94a3b8"
    TEXT_MUTED = "#64748b"

    ACCENT_PRIMARY = "#0284c7"
    ACCENT_HOVER = "#0369a1"
    ACCENT_LIGHT = "#38bdf8"
    ACCENT_GLOW = "rgba(56, 189, 248, 0.20)"

    SUCCESS = "#10b981"
    SUCCESS_BG = "#064e3b"
    WARNING = "#f59e0b"
    WARNING_BG = "#78350f"
    ERROR = "#ef4444"
    ERROR_BG = "#7f1d1d"



class LightPalette:
    """Polished light theme using layered surfaces."""
    BG_DARKEST = "#f1f5f9"
    BG_BASE = "#f8fafc"
    SURFACE_PRIMARY = "#ffffff"
    SURFACE_ELEVATED = "#f1f5f9"
    SURFACE_INTERACTIVE = "#e2e8f0"
    SURFACE_HOVER = "#cbd5e1"

    BORDER_SUBTLE = "rgba(0, 0, 0, 0.06)"
    BORDER_DEFAULT = "rgba(0, 0, 0, 0.12)"
    BORDER_FOCUS = "#0284c7"

    TEXT_PRIMARY = "#0f172a"
    TEXT_SECONDARY = "#475569"
    TEXT_MUTED = "#64748b"

    ACCENT_PRIMARY = "#0284c7"
    ACCENT_HOVER = "#0369a1"
    ACCENT_LIGHT = "#38bdf8"
    ACCENT_GLOW = "rgba(2, 132, 199, 0.12)"

    SUCCESS = "#059669"
    SUCCESS_BG = "#d1fae5"
    WARNING = "#d97706"
    WARNING_BG = "#fef3c7"
    ERROR = "#dc2626"
    ERROR_BG = "#fee2e2"
