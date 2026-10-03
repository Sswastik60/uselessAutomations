"""ScanResult, PageState, and AutomationStatus models."""

from dataclasses import dataclass, field
from enum import Enum
from typing import List, Optional, Dict, Any
from .form_field import FormField, FieldMatch


class AutomationStatus(str, Enum):
    """Current state of the automation engine."""
    IDLE = "IDLE"
    CONNECTING = "CONNECTING"
    SCANNING = "SCANNING"
    MATCHING = "MATCHING"
    FILLING = "FILLING"
    WAITING_MANUAL = "WAITING_MANUAL"        # CAPTCHA, OTP, Login
    WAITING_CONFIRMATION = "WAITING_CONFIRMATION"  # Uncertain field or custom question
    WAITING_REVIEW = "WAITING_REVIEW"        # Mandatory pre-submission review
    SUBMITTING = "SUBMITTING"
    COMPLETED = "COMPLETED"
    STOPPED = "STOPPED"
    ERROR = "ERROR"


@dataclass
class PageState:
    """Snapshot of a scanned web page."""
    url: str
    title: str
    page_number: int = 1
    form_detected: bool = False
    fields_count: int = 0
    matched_count: int = 0
    filled_count: int = 0


@dataclass
class ScanResult:
    """Comprehensive outcome of inspecting a webpage DOM."""
    url: str
    page_number: int = 1
    is_registration_form: bool = False
    fields: List[FormField] = field(default_factory=list)
    matches: List[FieldMatch] = field(default_factory=list)
    
    # Navigation controls
    next_button_selector: Optional[str] = None
    next_button_text: Optional[str] = None
    submit_button_selector: Optional[str] = None
    submit_button_text: Optional[str] = None
    
    # Security & Verification
    has_captcha: bool = False
    captcha_type: Optional[str] = None
    has_login_wall: bool = False
    has_legal_checkboxes: bool = False
    
    # Diagnostics
    error_message: Optional[str] = None

    @property
    def total_fields(self) -> int:
        return len(self.fields)

    @property
    def filled_fields(self) -> List[FieldMatch]:
        return [m for m in self.matches if m.status == "FILLED"]

    @property
    def pending_fields(self) -> List[FieldMatch]:
        return [m for m in self.matches if m.status in ("PENDING_CONFIRMATION", "UNRESOLVED")]

    @property
    def unfilled_fields(self) -> List[FieldMatch]:
        return [m for m in self.matches if m.status in ("UNRESOLVED", "SKIPPED")]
