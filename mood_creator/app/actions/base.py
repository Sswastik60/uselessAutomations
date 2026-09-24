from abc import ABC, abstractmethod
from typing import Any, Dict
from app.core.execution_context import AutomationContext
from app.models.action_result import ActionResult


class BaseAction(ABC):
    """Abstract base class for all automation actions."""

    # Schema defining parameter types for UI form generation in Mode Editor
    PARAM_SCHEMA: Dict[str, Any] = {}

    def __init__(self, **kwargs):
        """Store action arguments."""
        self.params = kwargs

    @abstractmethod
    def execute(self, context: AutomationContext) -> ActionResult:
        """
        Execute the action logic.
        Must return an ActionResult instance.
        """
        pass
