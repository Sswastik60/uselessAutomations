"""Tests for FormDetector and button classification."""

from pathlib import Path
import pytest
from playwright.sync_api import sync_playwright
from app.automation.form_detector import FormDetector
from app.models.form_field import FieldType


@pytest.fixture(scope="module")
def browser_instance():
    with sync_playwright() as p:
        browser = p.chromium.launch(headless=True)
        context = browser.new_context()
        page = context.new_page()
        yield page
        browser.close()


def test_detect_basic_form_fields(browser_instance):
    page = browser_instance
    basic_html_path = Path("test_pages/basic_form.html").absolute().as_uri()
    page.goto(basic_html_path)

    detector = FormDetector()
    scan_res = detector.scan_page(page, page_number=1)

    assert scan_res.is_registration_form
    assert len(scan_res.fields) == 4

    names = [f.name for f in scan_res.fields]
    assert "fullName" in names
    assert "emailAddress" in names
    assert "phoneNumber" in names
    assert "institution" in names

    # Button detection
    assert scan_res.submit_button_selector is not None
    assert "Submit" in (scan_res.submit_button_text or "")


def test_detect_dropdown_and_radio_form(browser_instance):
    page = browser_instance
    dropdown_html_path = Path("test_pages/dropdown_form.html").absolute().as_uri()
    page.goto(dropdown_html_path)

    detector = FormDetector()
    scan_res = detector.scan_page(page, page_number=1)

    select_fields = [f for f in scan_res.fields if f.field_type == FieldType.SELECT]
    assert len(select_fields) == 4  # degree, branch, year, country

    # Degree options extracted
    degree_field = next(f for f in select_fields if f.name == "degree")
    assert len(degree_field.options) >= 5
    opt_texts = [o.text for o in degree_field.options]
    assert "B.Tech / B.E." in opt_texts

    # Radios
    radio_fields = [f for f in scan_res.fields if f.field_type == FieldType.RADIO]
    assert len(radio_fields) == 3  # Male, Female, Other
