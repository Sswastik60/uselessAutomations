"""Profile data validator for email, URLs, numbers, and core required fields."""

import re
from typing import List
from ..models.profile import UserProfile, ValidationIssue, ProfileValidationResult
from ..utils.helpers import validate_url


EMAIL_REGEX = re.compile(r"^[a-zA-Z0-9_.+-]+@[a-zA-Z0-9-]+\.[a-zA-Z0-9-.]+$")
PHONE_REGEX = re.compile(r"^\+?[0-9\s\-\(\)]{7,20}$")


class ProfileValidator:
    """Validates user profiles against semantic data formats and required fields."""

    @classmethod
    def validate(cls, profile: UserProfile, strict: bool = False) -> ProfileValidationResult:
        issues: List[ValidationIssue] = []

        if len(profile) == 0:
            issues.append(ValidationIssue(
                key="profile",
                message="Profile is empty. Please add registration details.",
                severity="ERROR"
            ))
            return ProfileValidationResult(is_valid=False, issues=issues, fields_count=0)

        # Check essential required fields
        required_keys = ["name", "email", "phone", "college"]
        for req in required_keys:
            if not profile.has(req):
                # Also check common aliases
                found = False
                if req == "name" and (profile.has("full_name") or profile.has("first_name")):
                    found = True
                elif req == "phone" and (profile.has("mobile") or profile.has("contact_number")):
                    found = True
                elif req == "college" and (profile.has("university") or profile.has("institution")):
                    found = True

                if not found:
                    issues.append(ValidationIssue(
                        key=req,
                        message=f"Missing recommended field '{req}'.",
                        severity="ERROR" if strict else "WARNING"
                    ))

        # Validate Email
        email_val = profile.email
        if email_val and not EMAIL_REGEX.match(email_val):
            issues.append(ValidationIssue(
                key="email",
                message=f"Invalid email address format: '{email_val}'",
                severity="ERROR"
            ))

        # Validate Phone
        phone_val = profile.get("phone") or profile.get("mobile")
        if phone_val and not PHONE_REGEX.match(phone_val):
            issues.append(ValidationIssue(
                key="phone",
                message=f"Phone number '{phone_val}' may contain invalid characters.",
                severity="WARNING"
            ))

        # Validate URLs
        for url_field in ("github", "linkedin", "portfolio", "resume"):
            val = profile.get(url_field)
            if val:
                # If user typed github.com/xyz without https://, accept and warn or check
                if not val.startswith("http://") and not val.startswith("https://"):
                    val = "https://" + val
                    profile.set(url_field, val)
                valid, msg = validate_url(val, allow_local_file=False)
                if not valid:
                    issues.append(ValidationIssue(
                        key=url_field,
                        message=f"Invalid URL for '{url_field}': {msg}",
                        severity="WARNING"
                    ))

        # Validate Team Size
        size_val = profile.get("team_size")
        if size_val:
            try:
                parsed_size = int(size_val)
                if parsed_size <= 0:
                    issues.append(ValidationIssue(
                        key="team_size",
                        message=f"Team size must be a positive number (got {parsed_size}).",
                        severity="WARNING"
                    ))
            except ValueError:
                issues.append(ValidationIssue(
                    key="team_size",
                    message=f"Team size '{size_val}' is not a valid integer.",
                    severity="WARNING"
                ))

        has_errors = any(i.severity == "ERROR" for i in issues)
        return ProfileValidationResult(
            is_valid=not has_errors,
            issues=issues,
            fields_count=len(profile)
        )
