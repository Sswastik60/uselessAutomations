"""Helper functions for URL validation, string normalization, and sanitization."""

import re
from urllib.parse import urlparse
from typing import Tuple


def validate_url(url: str, allow_local_file: bool = True) -> Tuple[bool, str]:
    """
    Validate that the supplied URL is syntactically valid and uses HTTP/HTTPS (or file:// for local tests).
    Returns (is_valid, error_message).
    """
    if not url or not url.strip():
        return False, "URL cannot be empty. Please enter a valid registration link."

    url = url.strip()

    try:
        parsed = urlparse(url)
    except Exception as e:
        return False, f"Malformed URL syntax: {str(e)}"

    scheme = (parsed.scheme or "").lower()

    if allow_local_file and scheme == "file":
        if not parsed.path and not parsed.netloc:
            return False, "Invalid local file URL path."
        return True, ""

    if scheme not in ("http", "https"):
        return False, "URL must begin with 'http://' or 'https://'."

    netloc = parsed.netloc or ""
    if not netloc:
        return False, "URL must specify a valid host/domain (e.g. example.com)."

    # Basic hostname validation (allow localhost, ip, or domain with dots)
    host_part = netloc.split(":")[0]  # Strip port if present
    if host_part == "localhost" or host_part == "127.0.0.1":
        return True, ""

    # Must contain at least one dot in domain name
    if "." not in host_part:
        return False, f"'{host_part}' does not appear to be a valid domain."

    return True, ""


def normalize_field_name(name: str) -> str:
    """
    Normalizes a field label, attribute, or key:
    - converts camelCase to snake_case
    - lowercases
    - strips symbols and non-alphanumeric chars (except underscores)
    - collapses redundant spaces/underscores
    """
    if not name:
        return ""

    # Split camelCase e.g. fullName -> full_name, emailAddress -> email_address
    s1 = re.sub(r'(.)([A-Z][a-z]+)', r'\1_\2', name)
    s2 = re.sub(r'([a-z0-9])([A-Z])', r'\1_\2', s1).lower()

    # Replace punctuation and whitespace with underscores
    clean = re.sub(r'[^a-z0-9_]+', '_', s2)
    clean = re.sub(r'_+', '_', clean).strip('_')
    return clean


def sanitize_string(value: str) -> str:
    """Trim whitespace and strip dangerous control characters."""
    if not value:
        return ""
    # Strip null bytes and non-printable control characters
    return "".join(c for c in value.strip() if c.isprintable() or c in ("\n", "\t"))
