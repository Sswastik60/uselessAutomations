"""Unit tests for TXT profile parser and validator."""

import pytest
from app.profile.parser import ProfileParser
from app.profile.validator import ProfileValidator
from app.models.profile import UserProfile


def test_parse_valid_profile():
    content = """
    # Personal Info
    name=Swastik
    email=swastik@example.com
    phone=9876543210

    # Education
    college=Example University
    degree=B.Tech
    year=3
    """
    profile, issues = ProfileParser.parse_string(content)
    assert profile.get("name") == "Swastik"
    assert profile.get("email") == "swastik@example.com"
    assert profile.get("phone") == "9876543210"
    assert profile.get("college") == "Example University"
    assert profile.get("degree") == "B.Tech"
    assert profile.get("year") == "3"
    assert len(profile) == 6


def test_parser_ignores_comments_and_empty_lines():
    content = """
    # This is a comment
    
    # Another comment
    name=Jane Doe

    # Empty lines above and below
    
    email=jane@example.com
    """
    profile, issues = ProfileParser.parse_string(content)
    assert len(profile) == 2
    assert profile.get("name") == "Jane Doe"
    assert profile.get("email") == "jane@example.com"
    assert "This is a comment" in profile.comments


def test_parser_preserves_multiple_equals_signs():
    content = """
    search_query=filter=active&sort=desc
    profile_url=https://site.com?user=123&token=abc=xyz
    """
    profile, issues = ProfileParser.parse_string(content)
    assert profile.get("search_query") == "filter=active&sort=desc"
    assert profile.get("profile_url") == "https://site.com?user=123&token=abc=xyz"


def test_parser_normalizes_keys():
    content = """
    Full Name=Alex Rivers
    Email-Address=alex@example.com
    COLLEGE NAME=Tech Institute
    team_size=4
    """
    profile, issues = ProfileParser.parse_string(content)
    assert profile.get("full_name") == "Alex Rivers"
    assert profile.get("email_address") == "alex@example.com"
    assert profile.get("college_name") == "Tech Institute"
    assert profile.get("team_size") == "4"


def test_parser_detects_duplicate_keys():
    content = """
    name=First Name
    name=Second Name
    """
    profile, issues = ProfileParser.parse_string(content)
    # The last value overwrites
    assert profile.get("name") == "Second Name"
    # An issue is generated
    assert any("Duplicate key" in issue.message for issue in issues)


def test_parser_detects_malformed_lines():
    content = """
    name=Valid Name
    this is a malformed line without equals
    =empty key
    """
    profile, issues = ProfileParser.parse_string(content)
    assert profile.get("name") == "Valid Name"
    assert any("Missing '='" in issue.message for issue in issues)
    assert any("Key cannot be empty" in issue.message for issue in issues)


def test_validator_detects_invalid_email_and_urls():
    content = """
    name=Test User
    email=not-an-email
    phone=1234567890
    college=Tech University
    github=invalid-url-format
    team_size=-5
    """
    profile, _ = ProfileParser.parse_string(content)
    res = ProfileValidator.validate(profile)
    assert not res.is_valid
    assert any(i.key == "email" for i in res.issues)
    assert any(i.key == "github" for i in res.issues)
    assert any(i.key == "team_size" for i in res.issues)


def test_validator_passes_for_complete_profile():
    content = """
    name=Jane Doe
    email=jane@example.com
    phone=+1 9876543210
    college=Global University
    github=https://github.com/janedoe
    linkedin=https://linkedin.com/in/janedoe
    portfolio=https://janedoe.me
    team_size=3
    """
    profile, _ = ProfileParser.parse_string(content)
    res = ProfileValidator.validate(profile)
    assert res.is_valid
    assert res.error_count == 0
