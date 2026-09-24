import logging
from typing import Any, Dict, List, Type, TYPE_CHECKING

if TYPE_CHECKING:
    from app.actions.base import BaseAction

logger = logging.getLogger(__name__)


class ActionRegistry:
    """Central registry for discovering, inspecting, and instantiating automation actions."""

    _instance = None
    _registry: Dict[str, Type["BaseAction"]] = {}
    _metadata: Dict[str, Dict[str, Any]] = {}

    def __new__(cls):
        if cls._instance is None:
            cls._instance = super(ActionRegistry, cls).__new__(cls)
        return cls._instance

    @classmethod
    def _ensure_actions_loaded(cls) -> None:
        if not cls._registry:
            try:
                import app.actions  # noqa: F401
            except Exception as e:
                logger.error(f"Failed to load built-in actions: {e}")

    @classmethod
    def register(
        cls,
        action_type: str,
        action_class: Type["BaseAction"],
        category: str = "General",
        display_name: str = "",
        description: str = "",
        param_schema: Dict[str, Any] | None = None,
    ) -> None:
        """Register an action class under a unique type key."""
        cls._registry[action_type] = action_class
        cls._metadata[action_type] = {
            "type": action_type,
            "category": category,
            "display_name": display_name or action_type,
            "description": description or action_class.__doc__ or "",
            "param_schema": param_schema or getattr(action_class, "PARAM_SCHEMA", {}),
        }
        logger.debug(f"Registered action type: '{action_type}' ({action_class.__name__})")

    @classmethod
    def get_action_class(cls, action_type: str) -> Type["BaseAction"]:
        """Retrieve the action class for an action type string."""
        cls._ensure_actions_loaded()
        if action_type not in cls._registry:
            raise KeyError(f"Action type '{action_type}' is not registered in ActionRegistry.")
        return cls._registry[action_type]

    @classmethod
    def create_action(cls, action_type: str, params: Dict[str, Any]) -> "BaseAction":
        """Instantiate an action object given its type and parameters."""
        cls._ensure_actions_loaded()
        action_cls = cls.get_action_class(action_type)
        return action_cls(**params)

    @classmethod
    def list_actions(cls) -> List[Dict[str, Any]]:
        """Return list of metadata for all registered actions."""
        cls._ensure_actions_loaded()
        return list(cls._metadata.values())

    @classmethod
    def get_categories(cls) -> List[str]:
        """Return unique list of registered action categories."""
        cls._ensure_actions_loaded()
        categories = set(meta["category"] for meta in cls._metadata.values())
        return sorted(list(categories))

    @classmethod
    def is_registered(cls, action_type: str) -> bool:
        """Check if an action type is registered."""
        cls._ensure_actions_loaded()
        return action_type in cls._registry


action_registry = ActionRegistry()
import app.actions  # noqa: F401
