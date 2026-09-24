from abc import ABC, abstractmethod
from typing import Optional
from app.models.action_result import ActionResult


class ApplicationAdapter(ABC):
    """Abstract plugin adapter interface for desktop application integrations."""

    @property
    @abstractmethod
    def app_key(self) -> str:
        """Unique application key (e.g. 'fl_studio')."""
        pass

    @property
    @abstractmethod
    def display_name(self) -> str:
        """Human-readable application name."""
        pass

    @abstractmethod
    def is_installed(self) -> bool:
        """Check if application executable exists on system."""
        pass

    @abstractmethod
    def is_running(self) -> bool:
        """Check if application process is currently active."""
        pass

    @abstractmethod
    def launch(self, extra_args: Optional[list] = None) -> ActionResult:
        """Launch the application."""
        pass

    @abstractmethod
    def focus(self) -> ActionResult:
        """Bring application window to front and focus."""
        pass

    @abstractmethod
    def close(self, force: bool = False) -> ActionResult:
        """Close application."""
        pass
