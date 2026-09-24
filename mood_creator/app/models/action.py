from typing import Any, Literal, Optional
from pydantic import BaseModel, Field


class ActionConfig(BaseModel):
    """Configuration for an individual automation action inside a Mode."""

    id: Optional[str] = None
    type: str = Field(..., description="Action type identifier, e.g. process.launch")
    name: Optional[str] = Field(None, description="Human friendly custom action name")
    params: dict[str, Any] = Field(default_factory=dict, description="Action specific parameters")
    on_failure: Literal["stop", "continue", "retry"] = Field(
        "stop", description="Policy when this action fails: stop mode, continue, or retry"
    )
    retry_count: int = Field(0, description="Number of retry attempts if on_failure is retry")

    def get_display_name(self) -> str:
        if self.name:
            return self.name
        parts = self.type.split(".")
        category = parts[0].capitalize()
        name = parts[1].replace("_", " ").title() if len(parts) > 1 else self.type
        return f"{category}: {name}"
