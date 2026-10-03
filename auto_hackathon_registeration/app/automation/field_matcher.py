"""Field Matching Coordinator between FormFields and UserProfile."""

from typing import List
from ..models.form_field import FormField, FieldMatch
from ..models.profile import UserProfile
from ..models.scan_result import ScanResult
from ..utils.matching import FieldMatcherEngine
from ..services.logger import get_logger


class AutomationFieldMatcher:
    """Coordinates field matching algorithms and decorates ScanResult with FieldMatch objects."""

    def __init__(self, engine: FieldMatcherEngine = None):
        self.engine = engine or FieldMatcherEngine()
        self.logger = get_logger()

    def process_scan(self, scan_result: ScanResult, profile: UserProfile) -> List[FieldMatch]:
        """Match all fields in a scan result against user profile."""
        matches: List[FieldMatch] = []
        auto_fillable_count = 0
        uncertain_count = 0
        unmatched_count = 0

        for field in scan_result.fields:
            match = self.engine.match_field(field, profile)
            matches.append(match)

            if match.status == "FILLED":
                auto_fillable_count += 1
            elif match.status == "PENDING_CONFIRMATION":
                uncertain_count += 1
            else:
                unmatched_count += 1

        scan_result.matches = matches
        self.logger.info(
            f"Matching completed: {auto_fillable_count} ready to fill, "
            f"{uncertain_count} pending confirmation, {unmatched_count} unresolved."
        )
        return matches
