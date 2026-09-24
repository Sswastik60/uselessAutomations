import logging
from collections import defaultdict
from typing import Any, Callable, Dict, List

logger = logging.getLogger(__name__)


class EventBus:
    """Central event bus for application-wide publish/subscribe event notifications."""

    _instance = None

    def __new__(cls):
        if cls._instance is None:
            cls._instance = super(EventBus, cls).__new__(cls)
            cls._instance._subscribers = defaultdict(list)
        return cls._instance

    def subscribe(self, event_name: str, callback: Callable[..., None]) -> None:
        """Subscribe a callback to an event."""
        if callback not in self._subscribers[event_name]:
            self._subscribers[event_name].append(callback)

    def unsubscribe(self, event_name: str, callback: Callable[..., None]) -> None:
        """Unsubscribe a callback from an event."""
        if callback in self._subscribers[event_name]:
            self._subscribers[event_name].remove(callback)

    def publish(self, event_name: str, **data: Any) -> None:
        """Publish an event to all subscribers."""
        subscribers = list(self._subscribers.get(event_name, []))
        for callback in subscribers:
            try:
                callback(**data)
            except Exception as e:
                logger.error(f"Error executing event subscriber for '{event_name}': {e}", exc_info=True)


# Global singleton convenience instance
event_bus = EventBus()
