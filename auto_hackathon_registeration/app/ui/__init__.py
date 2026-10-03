"""UI package for HackFill."""

from .main_window import MainWindow
from .dashboard import DashboardView
from .automation_view import AutomationView
from .review_view import ReviewView
from .profile_view import ProfileView
from .settings_view import SettingsView

__all__ = [
    "MainWindow",
    "DashboardView",
    "AutomationView",
    "ReviewView",
    "ProfileView",
    "SettingsView",
]
