"""TXT Profile Parser following HackFill specification."""

import os
from pathlib import Path
from typing import Tuple, List, Optional
from ..models.profile import UserProfile, ProfileField, ValidationIssue
from ..utils.helpers import normalize_field_name, sanitize_string


class ProfileParser:
    """Parses key-value TXT profile files with comment tracking and robust syntax validation."""

    @classmethod
    def parse_file(cls, filepath: str | Path) -> Tuple[UserProfile, List[ValidationIssue]]:
        """Read and parse profile from a given filesystem path."""
        path = Path(filepath)
        if not path.exists():
            issue = ValidationIssue(
                key="file",
                message=f"Profile file not found at: {path}",
                severity="ERROR"
            )
            return UserProfile(filepath=str(path)), [issue]

        try:
            with open(path, "r", encoding="utf-8") as f:
                content = f.read()
            return cls.parse_string(content, filepath=str(path))
        except UnicodeDecodeError:
            try:
                with open(path, "r", encoding="latin-1") as f:
                    content = f.read()
                return cls.parse_string(content, filepath=str(path))
            except Exception as e:
                issue = ValidationIssue(
                    key="file",
                    message=f"Failed to read file due to encoding issue: {str(e)}",
                    severity="ERROR"
                )
                return UserProfile(filepath=str(path)), [issue]
        except Exception as e:
            issue = ValidationIssue(
                key="file",
                message=f"Error reading file: {str(e)}",
                severity="ERROR"
            )
            return UserProfile(filepath=str(path)), [issue]

    @classmethod
    def parse_string(cls, content: str, filepath: Optional[str] = None) -> Tuple[UserProfile, List[ValidationIssue]]:
        """
        Parse raw string content of a TXT profile.
        
        Rules:
        - Ignore empty or whitespace-only lines.
        - Ignore comments beginning with #.
        - Track section headings from comments (e.g. '# Personal Information').
        - Split ONLY on the first '=' to preserve values containing '='.
        - Trim unnecessary whitespace.
        - Normalize keys (lowercase, snake_case).
        - Detect duplicate keys.
        - Detect malformed lines (missing '=').
        """
        user_profile = UserProfile(filepath=filepath)
        issues: List[ValidationIssue] = []
        seen_keys: set = set()
        current_section = "General"

        lines = content.splitlines()
        for line_num, raw_line in enumerate(lines, start=1):
            line = raw_line.strip()

            # Ignore empty lines
            if not line:
                continue

            # Check comments
            if line.startswith("#"):
                comment_text = line.lstrip("#").strip()
                user_profile.comments.append(comment_text)

                # Heuristic: treat short comments without punctuation as section headings
                if len(comment_text) < 40 and not comment_text.startswith("="):
                    current_section = comment_text
                continue

            # Must contain '=' delimiter
            if "=" not in line:
                issues.append(ValidationIssue(
                    key=f"line_{line_num}",
                    message=f"Malformed line {line_num}: Missing '=' delimiter in '{line}'",
                    severity="WARNING",
                    line_number=line_num
                ))
                continue

            # Split ONLY on first '='
            raw_key, raw_val = line.split("=", 1)
            raw_key = raw_key.strip()
            raw_val = raw_val.strip()

            if not raw_key:
                issues.append(ValidationIssue(
                    key=f"line_{line_num}",
                    message=f"Malformed line {line_num}: Key cannot be empty.",
                    severity="ERROR",
                    line_number=line_num
                ))
                continue

            norm_key = normalize_field_name(raw_key)

            # Check duplicate keys
            if norm_key in seen_keys:
                issues.append(ValidationIssue(
                    key=norm_key,
                    message=f"Duplicate key '{raw_key}' at line {line_num}. Previous value overwritten.",
                    severity="WARNING",
                    line_number=line_num
                ))
            else:
                seen_keys.add(norm_key)

            clean_val = sanitize_string(raw_val)

            # Store in profile
            user_profile.set(norm_key, clean_val)
            user_profile.raw_entries.append(ProfileField(
                key=norm_key,
                value=clean_val,
                line_number=line_num,
                section=current_section
            ))

        return user_profile, issues
