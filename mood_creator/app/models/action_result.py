from dataclasses import dataclass, field
from datetime import datetime, timezone
from typing import Any, Optional


@dataclass
class ActionResult:
    """Represents the execution result of an individual automation action."""

    success: bool
    message: str
    duration: float = 0.0
    data: dict[str, Any] = field(default_factory=dict)
    error: Optional[str] = None
    timestamp: str = field(
        default_factory=lambda: datetime.now(timezone.utc).isoformat()
    )

    def to_dict(self) -> dict[str, Any]:
        return {
            "success": self.success,
            "message": self.message,
            "duration": round(self.duration, 4),
            "data": self.data,
            "error": self.error,
            "timestamp": self.timestamp,
        }
