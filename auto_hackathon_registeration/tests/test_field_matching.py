"""Unit tests for offline field matching, aliases, and confidence scoring."""

import pytest
from app.models.form_field import FormField, FieldType
from app.models.profile import UserProfile
from app.utils.matching import FieldMatcherEngine, CANONICAL_ALIASES


@pytest.fixture
def sample_profile() -> UserProfile:
    p = UserProfile()
    p.set("name", "Swastik")
    p.set("email", "swastik@example.com")
    p.set("phone", "9876543210")
    p.set("college", "Example University")
    p.set("github", "https://github.com/example")
    p.set("linkedin", "https://linkedin.com/in/example")
    p.set("team_name", "ByteForce")
    p.set("degree", "B.Tech")
    p.set("why_participate", "I want to build practical applications.")
    return p


def test_exact_name_match(sample_profile):
    engine = FieldMatcherEngine()
    field = FormField(
        field_id="f1",
        tag="input",
        field_type=FieldType.TEXT,
        name="name",
        label="Name"
    )
    match = engine.match_field(field, sample_profile)
    assert match.matched_key == "name"
    assert match.matched_value == "Swastik"
    assert match.confidence >= 0.90
    assert match.status == "FILLED"


def test_alias_matching_variants(sample_profile):
    engine = FieldMatcherEngine()

    # fullName -> name
    f_fullname = FormField(field_id="f2", tag="input", field_type=FieldType.TEXT, name="fullName", label="Full Name")
    m2 = engine.match_field(f_fullname, sample_profile)
    assert m2.matched_key == "name"
    assert m2.matched_value == "Swastik"
    assert m2.confidence >= 0.85

    # emailAddress -> email
    f_email = FormField(field_id="f3", tag="input", field_type=FieldType.EMAIL, name="emailAddress", label="Email Address")
    m3 = engine.match_field(f_email, sample_profile)
    assert m3.matched_key == "email"
    assert m3.matched_value == "swastik@example.com"

    # institution -> college
    f_college = FormField(field_id="f4", tag="input", field_type=FieldType.TEXT, name="institution", label="University Name")
    m4 = engine.match_field(f_college, sample_profile)
    assert m4.matched_key == "college"
    assert m4.matched_value == "Example University"

    # mobileNumber -> phone
    f_phone = FormField(field_id="f5", tag="input", field_type=FieldType.TEL, name="mobileNumber", label="Contact No")
    m5 = engine.match_field(f_phone, sample_profile)
    assert m5.matched_key == "phone"
    assert m5.matched_value == "9876543210"

    # githubUrl -> github
    f_gh = FormField(field_id="f6", tag="input", field_type=FieldType.URL, name="githubUrl", label="GitHub Profile")
    m6 = engine.match_field(f_gh, sample_profile)
    assert m6.matched_key == "github"


def test_legal_checkbox_safety(sample_profile):
    engine = FieldMatcherEngine()
    field = FormField(
        field_id="f_legal",
        tag="input",
        field_type=FieldType.CHECKBOX,
        name="agree_terms",
        label="I agree to the Hackathon Terms and Conditions"
    )
    match = engine.match_field(field, sample_profile)
    # Must refuse to auto-fill legal agreements and require manual confirmation
    assert match.status == "MANUAL_REQUIRED"
    assert match.confidence == 0.0
    assert field.is_terms_or_legal


def test_unrecognized_custom_question(sample_profile):
    engine = FieldMatcherEngine()
    field = FormField(
        field_id="f_custom",
        tag="input",
        field_type=FieldType.TEXT,
        name="favorite_dev_snack",
        label="What is your favorite snack during late night coding?"
    )
    match = engine.match_field(field, sample_profile)
    assert match.status == "UNRESOLVED"
    assert match.confidence < 0.40


def test_dropdown_option_matcher():
    options = ["B.Tech / B.E.", "B.Sc Computer Science", "MCA", "Other"]
    target = "B.Tech"
    best = FieldMatcherEngine.match_option_value(options, target)
    assert best == "B.Tech / B.E."

    year_options = ["1st Year", "2nd Year", "3rd Year", "4th Year"]
    best_year = FieldMatcherEngine.match_option_value(year_options, "3")
    assert best_year == "3rd Year"
