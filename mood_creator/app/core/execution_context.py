import logging
from typing import Any, Dict, Optional


class AutomationContext:
    """
    State container passed through actions during a Mode run.
    Stores variable bindings, cancellation status, service handles, and logs.
    """

    def __init__(
        self,
        mode_id: str,
        mode_name: str,
        services: Optional[Dict[str, Any]] = None,
        logger: Optional[logging.Logger] = None,
    ):
        self.mode_id = mode_id
        self.mode_name = mode_name
        self.services: Dict[str, Any] = services or {}
        self.variables: Dict[str, Any] = {}
        self.logger = logger or logging.getLogger("AutomationEngine")
        self._cancellation_requested = False
        self.results_history: list = []

    def request_cancellation(self) -> None:
        """Signal the engine that the user requested cancellation."""
        self._cancellation_requested = True
        self.logger.info(f"Cancellation requested for mode '{self.mode_name}'")

    def is_cancelled(self) -> bool:
        """Check if cancellation has been requested."""
        return self._cancellation_requested

    def set_variable(self, key: str, value: Any) -> None:
        """Store a variable in context for downstream actions."""
        self.variables[key] = value

    def get_variable(self, key: str, default: Any = None) -> Any:
        """Retrieve a context variable."""
        return self.variables.get(key, default)

    def get_service(self, service_name: str) -> Optional[Any]:
        """Retrieve a registered system service (e.g. 'audio', 'windows', 'midi')."""
        return self.services.get(service_name)
