"""UserProfile and ProfileField models."""

from dataclasses import dataclass, field
from typing import Dict, List, Optional, Any
from pathlib import Path


@dataclass
class ProfileField:
    """Represents an individual entry in a user profile."""
    key: str
    value: str
    line_number: int = 0
    section: str = ""
    is_sensitive: bool = False

    def __repr__(self) -> str:
        masked = "***" if self.is_sensitive else self.value
        return f"ProfileField(key='{self.key}', value='{masked}', line={self.line_number})"


@dataclass
class ValidationIssue:
    """Represents a warning or error discovered in a profile."""
    key: str
    message: str
    severity: str = "ERROR"  # "ERROR" or "WARNING"
    line_number: Optional[int] = None


@dataclass
class ProfileValidationResult:
    """Encapsulates the outcome of validating a UserProfile."""
    is_valid: bool
    issues: List[ValidationIssue] = field(default_factory=list)
    fields_count: int = 0

    @property
    def error_count(self) -> int:
        return sum(1 for i in self.issues if i.severity == "ERROR")

    @property
    def warning_count(self) -> int:
        return sum(1 for i in self.issues if i.severity == "WARNING")


@dataclass
class UserProfile:
    """Encapsulates all extracted data from a user's TXT profile."""
    filepath: Optional[str] = None
    fields: Dict[str, str] = field(default_factory=dict)
    raw_entries: List[ProfileField] = field(default_factory=list)
    comments: List[str] = field(default_factory=list)

    def get(self, key: str, default: str = "") -> str:
        """Fetch normalized field value, fallback to default."""
        return self.fields.get(key.lower().strip(), default)

    def set(self, key: str, value: str) -> None:
        """Set or update a normalized field value."""
        norm_key = key.lower().strip()
        self.fields[norm_key] = value

    def has(self, key: str) -> bool:
        """Check if key exists and has a non-empty value."""
        norm_key = key.lower().strip()
        return bool(self.fields.get(norm_key, "").strip())

    @property
    def name(self) -> str:
        return self.get("name") or self.get("full_name") or self.get("first_name", "")

    @property
    def email(self) -> str:
        return self.get("email") or self.get("email_address", "")

    @property
    def filename(self) -> str:
        if self.filepath:
            return Path(self.filepath).name
        return "Untitled Profile"

    def to_dict(self) -> Dict[str, str]:
        return dict(self.fields)

    def __len__(self) -> int:
        return len(self.fields)
