from typing import Optional
from pydantic import BaseModel, Field
from app.models.action import ActionConfig


class Mode(BaseModel):
    """User-defined automation Mode recipe."""

    schema_version: int = Field(1, description="Schema version of the mode specification")
    id: str = Field(..., description="Unique identifier for the mode, e.g. guitar_mode")
    name: str = Field(..., description="Display name for the mode")
    description: str = Field("", description="Detailed explanation of what the mode does")
    icon: str = Field("⚡", description="Emoji or icon identifier")
    background: Optional[str] = Field(None, description="Background artwork preset name, asset filename, or custom image file path")
    hotkey: Optional[str] = Field(None, description="Global hotkey shortcut, e.g. CTRL+ALT+G")
    enabled: bool = Field(True, description="Whether this mode is active and triggerable")
    actions: list[ActionConfig] = Field(default_factory=list, description="Sequence of actions to execute")

    def to_dict(self) -> dict:
        return self.model_dump(mode="json")
