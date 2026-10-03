"""Human intervention detector for CAPTCHA, OTP, login challenges, and 2FA."""

from typing import Tuple, Optional
from playwright.sync_api import Page, Error as PlaywrightError


class HumanInterventionDetector:
    """Detects security challenges and manual verification barriers on the web page."""

    CAPTCHA_SELECTORS = [
        "iframe[src*='recaptcha']",
        ".g-recaptcha",
        "#g-recaptcha",
        "iframe[src*='hcaptcha']",
        ".h-captcha",
        "iframe[src*='challenges.cloudflare.com']",
        ".cf-turnstile",
        "div[class*='geetest']",
        "div[id*='geetest']",
        "div[class*='captcha']",
        "div[id*='captcha']",
    ]

    OTP_SELECTORS = [
        "input[autocomplete='one-time-code']",
        "input[name*='otp' i]",
        "input[id*='otp' i]",
        "input[placeholder*='otp' i]",
        "input[name*='verification_code' i]",
        "input[name*='verify_code' i]",
    ]

    @classmethod
    def check(cls, page: Page) -> Tuple[bool, Optional[str]]:
        """
        Check if the active page requires manual user intervention.
        Returns (is_required, reason_description).
        """
        if not page or page.is_closed():
            return False, None

        try:
            # 1. Check for CAPTCHA iframes / widgets
            for selector in cls.CAPTCHA_SELECTORS:
                elements = page.query_selector_all(selector)
                for el in elements:
                    if el.is_visible():
                        if "recaptcha" in selector:
                            return True, "Google reCAPTCHA verification detected."
                        elif "hcaptcha" in selector:
                            return True, "hCaptcha challenge detected."
                        elif "turnstile" in selector or "cloudflare" in selector:
                            return True, "Cloudflare Turnstile challenge detected."
                        return True, "Security CAPTCHA verification detected."

            # 2. Check for OTP / SMS / Email verification inputs
            for selector in cls.OTP_SELECTORS:
                elements = page.query_selector_all(selector)
                for el in elements:
                    if el.is_visible():
                        return True, "OTP / Security code verification required."

            # 3. Check for obvious text warnings on page
            body_text = page.inner_text("body").lower()
            if "verify you are human" in body_text:
                return True, "Cloudflare / Bot verification screen detected."
            if "enter the 6-digit code" in body_text or "enter the verification code sent" in body_text:
                return True, "Verification code sent to email/phone."

        except PlaywrightError:
            pass
        except Exception:
            pass

        return False, None
