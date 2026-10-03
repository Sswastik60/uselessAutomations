"""End-to-End browser tests executing automated form filling against local HTML test forms."""

from pathlib import Path
import pytest
from playwright.sync_api import sync_playwright

from app.models.profile import UserProfile
from app.automation.form_detector import FormDetector
from app.automation.field_matcher import AutomationFieldMatcher
from app.automation.form_filler import FormFiller
from app.automation.navigation import MultiPageNavigator


@pytest.fixture(scope="module")
def browser_context():
    with sync_playwright() as p:
        browser = p.chromium.launch(headless=True)
        context = browser.new_context()
        page = context.new_page()
        yield page
        browser.close()


@pytest.fixture
def test_profile():
    profile = UserProfile()
    profile.set("name", "Swastik")
    profile.set("email", "swastik@example.com")
    profile.set("phone", "9876543210")
    profile.set("college", "Example University")
    profile.set("degree", "B.Tech")
    profile.set("branch", "Computer Science and Engineering")
    profile.set("year", "3")
    profile.set("country", "India")
    profile.set("gender", "Male")
    profile.set("team_name", "ByteForce")
    profile.set("team_size", "3")
    profile.set("github", "https://github.com/example")
    profile.set("why_participate", "I want to build practical applications and learn.")
    profile.set("project_idea", "Autonomous hackathon registration assistant.")
    profile.set("hackathon_experience", "Yes")
    profile.set("subscribe_newsletter", "yes")
    return profile


def test_e2e_fill_basic_form(browser_context, test_profile):
    page = browser_context
    url = Path("test_pages/basic_form.html").absolute().as_uri()
    page.goto(url)

    detector = FormDetector()
    scan_res = detector.scan_page(page)

    matcher = AutomationFieldMatcher()
    matches = matcher.process_scan(scan_res, test_profile)

    filler = FormFiller()
    filled_count = filler.fill_all(page, matches)

    assert filled_count == 4

    # Verify directly in DOM
    assert page.input_value("#fullName") == "Swastik"
    assert page.input_value("#emailAddress") == "swastik@example.com"
    assert page.input_value("#phoneNumber") == "9876543210"
    assert page.input_value("#institution") == "Example University"


def test_e2e_fill_dropdown_and_radio(browser_context, test_profile):
    page = browser_context
    url = Path("test_pages/dropdown_form.html").absolute().as_uri()
    page.goto(url)

    detector = FormDetector()
    scan_res = detector.scan_page(page)

    matcher = AutomationFieldMatcher()
    matches = matcher.process_scan(scan_res, test_profile)

    filler = FormFiller()
    filled_count = filler.fill_all(page, matches)

    assert filled_count >= 4

    # Check DOM select values
    assert page.input_value("#degree_select") == "B.Tech"
    assert page.input_value("#branch_select") == "Computer Science and Engineering"
    assert page.input_value("#study_year") == "3"
    assert page.input_value("#country_field") == "India"

    # Check Male radio button is checked
    assert page.is_checked('input[type="radio"][value="Male"]')


def test_e2e_fill_custom_questions(browser_context, test_profile):
    page = browser_context
    url = Path("test_pages/custom_questions.html").absolute().as_uri()
    page.goto(url)

    detector = FormDetector()
    scan_res = detector.scan_page(page)

    matcher = AutomationFieldMatcher()
    matches = matcher.process_scan(scan_res, test_profile)

    filler = FormFiller()
    filler.fill_all(page, matches)

    assert "build practical applications" in page.input_value("#why_participate_input")
    assert "Autonomous hackathon" in page.input_value("#project_idea_input")
    assert page.input_value("#hackathon_exp") == "Yes"

    # Unrecognized secret question was not blindly filled with wrong info
    assert page.input_value("#custom_secret_question") == ""


def test_e2e_checkbox_legal_protection(browser_context, test_profile):
    page = browser_context
    url = Path("test_pages/checkbox_form.html").absolute().as_uri()
    page.goto(url)

    detector = FormDetector()
    scan_res = detector.scan_page(page)

    matcher = AutomationFieldMatcher()
    matches = matcher.process_scan(scan_res, test_profile)

    filler = FormFiller()
    filler.fill_all(page, matches)

    # Name was filled
    assert page.input_value("#applicant_name") == "Swastik"

    # Mandatory Legal checkbox MUST NOT be automatically checked
    assert not page.is_checked("#code_of_conduct")


def test_e2e_multi_page_navigation(browser_context, test_profile):
    page = browser_context
    url = Path("test_pages/multi_page_form.html").absolute().as_uri()
    page.goto(url)

    detector = FormDetector()
    matcher = AutomationFieldMatcher()
    filler = FormFiller()
    navigator = MultiPageNavigator(max_pages=5)

    # Step 1
    scan1 = detector.scan_page(page, page_number=1)
    matches1 = matcher.process_scan(scan1, test_profile)
    filler.fill_all(page, matches1)
    assert page.input_value("#step1-name") == "Swastik"
    assert page.input_value("#step1-email") == "swastik@example.com"

    # Advance to Step 2
    assert navigator.can_advance(scan1)
    ok = navigator.advance(page, scan1)
    assert ok

    # Step 2
    scan2 = detector.scan_page(page, page_number=2)
    matches2 = matcher.process_scan(scan2, test_profile)
    filler.fill_all(page, matches2)
    assert page.input_value("#step2-team") == "ByteForce"
    assert page.input_value("#step2-size") == "3"

    # Advance to Step 3
    assert navigator.can_advance(scan2)
    ok = navigator.advance(page, scan2)
    assert ok

    # Step 3
    scan3 = detector.scan_page(page, page_number=3)
    matches3 = matcher.process_scan(scan3, test_profile)
    filler.fill_all(page, matches3)
    assert page.input_value("#step3-college") == "Example University"
    assert page.input_value("#step3-github") == "https://github.com/example"


def test_invalid_url_validation():
    from app.utils.helpers import validate_url
    
    # Empty
    valid, msg = validate_url("")
    assert not valid
    assert "empty" in msg.lower()

    # No scheme
    valid, msg = validate_url("www.google.com")
    assert not valid
    assert "http" in msg.lower()

    # FTP scheme
    valid, msg = validate_url("ftp://example.com/file")
    assert not valid

    # Valid HTTP/HTTPS
    valid, msg = validate_url("https://hackathon.devpost.com/register")
    assert valid

    # Local file URL
    valid, msg = validate_url("file:///C:/test/form.html")
    assert valid


def test_crawler_stop_request():
    from app.automation.crawler import FormCrawler
    from app.services.settings import AppSettings
    from app.models.scan_result import AutomationStatus

    settings = AppSettings(browser_visible=False)
    crawler = FormCrawler(settings=settings)

    # Immediately request stop
    crawler.request_stop()
    assert crawler.status == AutomationStatus.STOPPED
    assert crawler._stop_requested.is_set()


def test_autopilot_mode_checks_all_checkboxes(browser_context, test_profile):
    from app.utils.matching import FieldMatcherEngine
    page = browser_context
    url = Path("test_pages/checkbox_form.html").absolute().as_uri()
    page.goto(url)

    detector = FormDetector()
    scan_res = detector.scan_page(page)

    # In Auto-Pilot mode, both legal agreements and regular checkboxes are automatically approved
    engine = FieldMatcherEngine(auto_check_checkboxes=True)
    matcher = AutomationFieldMatcher(engine=engine)
    matches = matcher.process_scan(scan_res, test_profile)

    filler = FormFiller(auto_check_checkboxes=True)
    filled_count = filler.fill_all(page, matches)

    assert filled_count >= 2
    assert page.input_value("#applicant_name") == "Swastik"
    assert page.is_checked("#code_of_conduct")
    assert page.is_checked("#newsletter")


def test_autopilot_smart_fallbacks(browser_context, test_profile):
    from app.utils.matching import FieldMatcherEngine
    page = browser_context
    url = Path("test_pages/custom_questions.html").absolute().as_uri()
    page.goto(url)

    detector = FormDetector()
    scan_res = detector.scan_page(page)

    # In Auto-Pilot mode, unmapped custom questions receive smart profile-derived answers
    engine = FieldMatcherEngine(smart_fallback_for_unknown=True)
    matcher = AutomationFieldMatcher(engine=engine)
    matches = matcher.process_scan(scan_res, test_profile)

    filler = FormFiller()
    filler.fill_all(page, matches)

    assert "build practical applications" in page.input_value("#why_participate_input")
    assert "Autonomous hackathon" in page.input_value("#project_idea_input")
    # Smart fallback filled the unmapped question automatically
    assert page.input_value("#custom_secret_question") != ""


