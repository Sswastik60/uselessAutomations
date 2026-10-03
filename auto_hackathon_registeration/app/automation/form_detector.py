"""DOM Form Field and Navigation Control Detector."""

from typing import List, Tuple, Optional, Dict, Any
from playwright.sync_api import Page, Error as PlaywrightError
from ..models.form_field import FormField, FieldType, FieldOption
from ..models.scan_result import ScanResult
from ..services.logger import get_logger
from .human_intervention import HumanInterventionDetector


# JavaScript snippet to inspect all visible form controls and extract comprehensive metadata
DOM_INSPECTOR_JS = """
() => {
    function isVisible(el) {
        if (!el) return false;
        const style = window.getComputedStyle(el);
        if (style.display === 'none' || style.visibility === 'hidden' || style.opacity === '0') return false;
        const rect = el.getBoundingClientRect();
        return rect.width > 0 && rect.height > 0;
    }

    function getLabelText(el) {
        // 1. Explicit for attribute
        if (el.id) {
            const label = document.querySelector(`label[for="${CSS.escape(el.id)}"]`);
            if (label && label.innerText) return label.innerText.trim();
        }
        // 2. Parent label tag
        const parentLabel = el.closest('label');
        if (parentLabel && parentLabel.innerText) {
            // Remove the element's own text if any
            return parentLabel.innerText.replace(el.innerText || '', '').trim();
        }
        // 3. aria-labelledby
        const labelledBy = el.getAttribute('aria-labelledby');
        if (labelledBy) {
            const ref = document.getElementById(labelledBy);
            if (ref && ref.innerText) return ref.innerText.trim();
        }
        // 4. Preceding sibling label or text
        let prev = el.previousElementSibling;
        while (prev) {
            if (prev.tagName.toLowerCase() === 'label' && prev.innerText) {
                return prev.innerText.trim();
            }
            prev = prev.previousElementSibling;
        }
        // 5. Surrounding parent text (closest .form-group / container)
        const container = el.closest('.form-group, .field, .input-group, div');
        if (container) {
            const firstLabel = container.querySelector('label, .label, p, span');
            if (firstLabel && firstLabel.innerText && isVisible(firstLabel)) {
                return firstLabel.innerText.trim();
            }
        }
        return '';
    }

    function getSurroundingText(el) {
        const parent = el.parentElement;
        if (!parent) return '';
        const clone = parent.cloneNode(true);
        // Remove input tags from clone to isolate text
        clone.querySelectorAll('input, select, textarea, button').forEach(e => e.remove());
        return (clone.innerText || '').substring(0, 100).trim();
    }

    const fields = [];
    const elements = document.querySelectorAll('input, textarea, select');

    elements.forEach((el, index) => {
        const tag = el.tagName.toLowerCase();
        const typeAttr = (el.getAttribute('type') || (tag === 'textarea' ? 'textarea' : (tag === 'select' ? 'select' : 'text'))).toLowerCase();

        // Skip hidden, submit, button inputs here (buttons handled separately)
        if (typeAttr === 'hidden' || typeAttr === 'submit' || typeAttr === 'button' || typeAttr === 'reset') {
            return;
        }

        // Only inspect visible inputs (or radio/checkbox where styling might hide native input slightly)
        if (!isVisible(el) && typeAttr !== 'radio' && typeAttr !== 'checkbox') {
            return;
        }

        // Generate a reliable unique selector
        let selector = '';
        if (el.id) {
            selector = `#${CSS.escape(el.id)}`;
        } else if (el.name) {
            selector = `${tag}[name="${CSS.escape(el.name)}"]`;
        } else {
            selector = `${tag}:nth-of-type(${index + 1})`;
        }

        // Options for select elements
        const options = [];
        if (tag === 'select') {
            Array.from(el.options || []).forEach(opt => {
                options.push({
                    text: (opt.text || '').trim(),
                    value: (opt.value || '').trim(),
                    selected: opt.selected
                });
            });
        }

        fields.push({
            index: index,
            tag: tag,
            type: typeAttr,
            name: el.name || '',
            id_attr: el.id || '',
            placeholder: el.placeholder || el.getAttribute('placeholder') || '',
            label: getLabelText(el),
            aria_label: el.getAttribute('aria-label') || '',
            surrounding_text: getSurroundingText(el),
            required: el.required || el.getAttribute('aria-required') === 'true' || el.classList.contains('required'),
            current_value: el.value || '',
            checked: el.checked || false,
            options: options,
            selector: selector
        });
    });

    // Detect navigation & submit buttons
    const buttons = [];
    const btnElements = document.querySelectorAll('button, input[type="submit"], input[type="button"], a.btn, a.button');
    btnElements.forEach(btn => {
        if (!isVisible(btn)) return;
        const text = (btn.innerText || btn.value || '').trim();
        let selector = '';
        if (btn.id) {
            selector = `#${CSS.escape(btn.id)}`;
        } else {
            selector = btn.tagName.toLowerCase() + `:has-text("${text.substring(0, 30)}")`;
        }
        buttons.push({
            text: text,
            selector: selector,
            is_submit: (btn.getAttribute('type') === 'submit') || /submit|register|finish|complete/i.test(text),
            is_next: /next|continue|proceed|step|save & continue/i.test(text)
        });
    });

    return {
        fields: fields,
        buttons: buttons,
        has_form: document.querySelectorAll('form, .form, [role="form"]').length > 0 || fields.length > 0
    };
}
"""


class FormDetector:
    """Detects and categorizes form fields, navigation buttons, and security challenges."""

    def __init__(self):
        self.logger = get_logger()

    def scan_page(self, page: Page, page_number: int = 1) -> ScanResult:
        """Inspect the DOM of the active page and generate a ScanResult."""
        result = ScanResult(
            url=page.url,
            page_number=page_number,
        )

        try:
            # 1. Check for manual intervention (CAPTCHA / OTP / Login)
            has_intervention, reason = HumanInterventionDetector.check(page)
            if has_intervention:
                result.has_captcha = True
                result.captcha_type = reason
                self.logger.warning(f"Human intervention barrier detected: {reason}")
                return result

            # 2. Execute DOM inspection script
            dom_data = page.evaluate(DOM_INSPECTOR_JS)

            raw_fields = dom_data.get("fields", [])
            raw_buttons = dom_data.get("buttons", [])
            result.is_registration_form = dom_data.get("has_form", False)

            # 3. Construct FormField objects
            for idx, rf in enumerate(raw_fields):
                field_type = FieldType.from_str(rf.get("tag", ""), rf.get("type", ""))
                options = [
                    FieldOption(text=opt["text"], value=opt["value"], is_selected=opt.get("selected", False))
                    for opt in rf.get("options", [])
                ]

                form_field = FormField(
                    field_id=f"field_{page_number}_{idx}",
                    tag=rf.get("tag", "input"),
                    field_type=field_type,
                    name=rf.get("name", ""),
                    id_attr=rf.get("id_attr", ""),
                    placeholder=rf.get("placeholder", ""),
                    label=rf.get("label", ""),
                    aria_label=rf.get("aria_label", ""),
                    surrounding_text=rf.get("surrounding_text", ""),
                    required=bool(rf.get("required", False)),
                    options=options,
                    current_value=rf.get("current_value", ""),
                    checked=bool(rf.get("checked", False)),
                    selector=rf.get("selector", ""),
                    page_number=page_number
                )
                result.fields.append(form_field)

            # 4. Identify Navigation / Submit buttons
            for btn in raw_buttons:
                text = btn.get("text", "")
                selector = btn.get("selector", "")
                if btn.get("is_submit") and not result.submit_button_selector:
                    result.submit_button_selector = selector
                    result.submit_button_text = text
                elif btn.get("is_next") and not result.next_button_selector:
                    result.next_button_selector = selector
                    result.next_button_text = text

            # If no explicit next or submit found, fallback heuristics
            if not result.submit_button_selector:
                import re
                for btn in raw_buttons:
                    if re.search(r"register|sign up|submit", btn.get("text", ""), re.IGNORECASE):
                        result.submit_button_selector = btn.get("selector")
                        result.submit_button_text = btn.get("text")
                        break

            self.logger.info(f"Page scan complete: Found {len(result.fields)} fields.")
            return result

        except PlaywrightError as pe:
            err = f"DOM evaluation error: {str(pe)}"
            self.logger.error(err)
            result.error_message = err
            return result
        except Exception as e:
            err = f"Unexpected error during form detection: {str(e)}"
            self.logger.error(err)
            result.error_message = err
            return result
