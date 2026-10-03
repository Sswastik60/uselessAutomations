"""Robust form filling execution engine across text, textareas, selects, radios, and checkboxes."""

from typing import List, Optional
from playwright.sync_api import Page, Error as PlaywrightError
from ..models.form_field import FormField, FieldMatch, FieldType
from ..utils.matching import FieldMatcherEngine
from ..services.logger import get_logger


class FormFiller:
    """Executes DOM element population with Playwright locators."""

    def __init__(self, auto_check_checkboxes: bool = False):
        self.auto_check_checkboxes = auto_check_checkboxes
        self.logger = get_logger()

    def fill_all(self, page: Page, matches: List[FieldMatch]) -> int:
        """Fill all eligible matches and return count of successfully filled fields."""
        success_count = 0
        for match in matches:
            if match.status == "FILLED" and match.final_value:
                ok = self.fill_single_field(page, match)
                if ok:
                    success_count += 1
        return success_count

    def fill_single_field(self, page: Page, match: FieldMatch) -> bool:
        """Fill an individual field according to its type and matched value."""
        field = match.field
        value = match.final_value

        if not value:
            return False

        if not page or page.is_closed():
            self.logger.warning("Cannot fill field: Browser is closed.")
            return False

        try:
            locator = page.locator(field.selector).first

            # 1. Text Inputs and Textareas
            if field.field_type in (
                FieldType.TEXT, FieldType.EMAIL, FieldType.TEL,
                FieldType.NUMBER, FieldType.URL, FieldType.TEXTAREA
            ):
                locator.click(timeout=3000)
                locator.fill(str(value), timeout=3000)
                self.logger.info(f"Filled '{field.display_name}' -> {value[:30] + ('...' if len(value) > 30 else '')}")
                match.status = "FILLED"
                return True

            # 2. Select Dropdowns
            elif field.field_type == FieldType.SELECT:
                option_texts = [opt.text for opt in field.options if opt.text]
                option_values = [opt.value for opt in field.options if opt.value]

                # Match against visible text first
                best_text = FieldMatcherEngine.match_option_value(option_texts, value)
                if best_text:
                    try:
                        locator.select_option(label=best_text, timeout=3000)
                    except Exception:
                        page.evaluate("""([sel, txt]) => {
                            const el = document.querySelector(sel);
                            if (el) {
                                for (let opt of el.options) {
                                    if (opt.text.trim().toLowerCase() === txt.trim().toLowerCase()) {
                                        el.value = opt.value;
                                        el.dispatchEvent(new Event('change', { bubbles: true }));
                                        break;
                                    }
                                }
                                if (window.$ && $(el).data('select2')) {
                                    $(el).select2('val', el.value);
                                }
                            }
                        }""", [field.selector, best_text])

                    self.logger.info(f"Selected '{best_text}' for dropdown '{field.display_name}'")
                    match.status = "FILLED"
                    return True

                # Fallback to value match
                best_val = FieldMatcherEngine.match_option_value(option_values, value)
                if best_val:
                    try:
                        locator.select_option(value=best_val, timeout=3000)
                    except Exception:
                        page.evaluate("""([sel, val]) => {
                            const el = document.querySelector(sel);
                            if (el) {
                                el.value = val;
                                el.dispatchEvent(new Event('change', { bubbles: true }));
                                if (window.$ && $(el).data('select2')) {
                                    $(el).select2('val', val);
                                }
                            }
                        }""", [field.selector, best_val])

                    self.logger.info(f"Selected option value '{best_val}' for dropdown '{field.display_name}'")
                    match.status = "FILLED"
                    return True

                self.logger.warning(f"Could not find matching option for '{value}' in dropdown '{field.display_name}'")
                return False

            # 3. Radio Buttons
            elif field.field_type == FieldType.RADIO:
                val_lower = value.strip().lower()
                field_val_lower = (field.current_value or "").strip().lower()
                label_lower = field.label.strip().lower()

                if val_lower in field_val_lower or val_lower in label_lower or not field_val_lower:
                    try:
                        locator.check(timeout=3000, force=True)
                    except Exception:
                        try:
                            locator.click(timeout=3000, force=True)
                        except Exception:
                            page.evaluate("""(sel) => {
                                const el = document.querySelector(sel);
                                if (el) {
                                    el.checked = true;
                                    el.dispatchEvent(new Event('input', { bubbles: true }));
                                    el.dispatchEvent(new Event('change', { bubbles: true }));
                                }
                            }""", field.selector)

                    self.logger.info(f"Selected radio option '{field.display_name}'")
                    match.status = "FILLED"
                    return True

            # 4. Checkboxes
            elif field.field_type == FieldType.CHECKBOX:
                if field.is_terms_or_legal and not self.auto_check_checkboxes:
                    self.logger.warning(f"Skipped legal checkbox '{field.display_name}' (requires explicit confirmation).")
                    return False

                # Check if user profile value is positive or auto-pilot checkbox clicking is active
                if str(value).strip().lower() in ("yes", "true", "1", "checked", "agree") or self.auto_check_checkboxes:
                    try:
                        locator.check(timeout=3000, force=True)
                    except Exception:
                        try:
                            locator.click(timeout=3000, force=True)
                        except Exception:
                            page.evaluate("""(sel) => {
                                const el = document.querySelector(sel);
                                if (el) {
                                    el.checked = true;
                                    el.dispatchEvent(new Event('input', { bubbles: true }));
                                    el.dispatchEvent(new Event('change', { bubbles: true }));
                                }
                            }""", field.selector)

                    self.logger.info(f"Checked box '{field.display_name}'")
                    match.status = "FILLED"
                    return True

        except PlaywrightError as pe:
            self.logger.warning(f"Failed to fill field '{field.display_name}': {str(pe)}")
            return False
        except Exception as e:
            self.logger.warning(f"Unexpected error filling '{field.display_name}': {str(e)}")
            return False

        return False
