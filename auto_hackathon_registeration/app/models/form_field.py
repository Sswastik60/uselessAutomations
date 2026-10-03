"""FormField, FieldType, FieldOption, and FieldMatch models."""

from dataclasses import dataclass, field
from enum import Enum
from typing import List, Optional, Any


class FieldType(str, Enum):
    """Categorization of web form fields."""
    TEXT = "text"
    EMAIL = "email"
    TEL = "tel"
    NUMBER = "number"
    URL = "url"
    TEXTAREA = "textarea"
    SELECT = "select"
    RADIO = "radio"
    CHECKBOX = "checkbox"
    BUTTON = "button"
    FILE = "file"
    PASSWORD = "password"
    HIDDEN = "hidden"
    UNKNOWN = "unknown"

    @classmethod
    def from_str(cls, tag: str, type_attr: str = "") -> "FieldType":
        tag = (tag or "").lower().strip()
        type_attr = (type_attr or "").lower().strip()

        if tag == "textarea":
            return cls.TEXTAREA
        elif tag == "select":
            return cls.SELECT
        elif tag == "input":
            if type_attr in ("text", "search"):
                return cls.TEXT
            elif type_attr == "email":
                return cls.EMAIL
            elif type_attr in ("tel", "phone"):
                return cls.TEL
            elif type_attr == "number":
                return cls.NUMBER
            elif type_attr == "url":
                return cls.URL
            elif type_attr == "radio":
                return cls.RADIO
            elif type_attr == "checkbox":
                return cls.CHECKBOX
            elif type_attr == "file":
                return cls.FILE
            elif type_attr == "password":
                return cls.PASSWORD
            elif type_attr == "hidden":
                return cls.HIDDEN
            elif type_attr in ("button", "submit", "reset"):
                return cls.BUTTON
            return cls.TEXT
        elif tag == "button":
            return cls.BUTTON
        return cls.UNKNOWN


@dataclass
class FieldOption:
    """Represents an option in a <select> or radio group."""
    text: str
    value: str
    is_selected: bool = False


@dataclass
class FormField:
    """Internal model representing an inspected DOM form element."""
    field_id: str
    tag: str
    field_type: FieldType
    name: str = ""
    id_attr: str = ""
    placeholder: str = ""
    label: str = ""
    aria_label: str = ""
    surrounding_text: str = ""
    required: bool = False
    options: List[FieldOption] = field(default_factory=list)
    current_value: str = ""
    checked: bool = False
    selector: str = ""
    page_number: int = 1
    is_terms_or_legal: bool = False

    @property
    def display_name(self) -> str:
        """Best available human-readable name for display."""
        if self.label:
            return self.label.replace("*", "").strip()
        if self.placeholder:
            return self.placeholder.strip()
        if self.aria_label:
            return self.aria_label.strip()
        if self.name:
            return self.name.replace("_", " ").replace("-", " ").title()
        if self.id_attr:
            return self.id_attr.replace("_", " ").replace("-", " ").title()
        return f"{self.field_type.value.capitalize()} Field"

    @property
    def identifier_context(self) -> str:
        """Concatenated lowercased string of all attributes for semantic matching."""
        tokens = [
            self.name,
            self.id_attr,
            self.label,
            self.placeholder,
            self.aria_label,
            self.surrounding_text,
        ]
        return " ".join(t.lower() for t in tokens if t)


@dataclass
class FieldMatch:
    """Represents the matching result between a FormField and UserProfile."""
    field: FormField
    matched_key: Optional[str] = None
    matched_value: Optional[str] = None
    confidence: float = 0.0  # 0.0 to 1.0 (e.g. 0.95 = 95%)
    match_reason: str = "unmatched"
    is_confirmed: bool = False
    user_override_value: Optional[str] = None
    status: str = "UNRESOLVED"  # "FILLED", "PENDING_CONFIRMATION", "UNRESOLVED", "MANUAL_REQUIRED", "SKIPPED"

    @property
    def final_value(self) -> str:
        if self.user_override_value is not None:
            return self.user_override_value
        return self.matched_value or ""

    @property
    def confidence_percent(self) -> int:
        return int(round(self.confidence * 100))
