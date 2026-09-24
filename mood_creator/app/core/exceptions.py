class AutomationHubError(Exception):
    """Base exception class for Windows 11 Automation Hub."""
    pass


class ActionExecutionError(AutomationHubError):
    """Raised when an automation action fails to execute."""
    def __init__(self, message: str, action_type: str, details: str | None = None):
        super().__init__(message)
        self.action_type = action_type
        self.details = details


class DeviceNotFoundError(AutomationHubError):
    """Raised when a requested audio or MIDI device is not connected."""
    pass


class ModeNotFoundError(AutomationHubError):
    """Raised when a specified mode ID does not exist."""
    pass


class HotkeyConflictError(AutomationHubError):
    """Raised when registering a hotkey that is already bound or reserved."""
    pass


class ModeValidationError(AutomationHubError):
    """Raised when mode JSON schema or action configuration is invalid."""
    pass
