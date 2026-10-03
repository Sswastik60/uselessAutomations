"""Browser automation package powered by Playwright."""

from .browser import BrowserManager
from .form_detector import FormDetector
from .field_matcher import AutomationFieldMatcher
from .form_filler import FormFiller
from .navigation import MultiPageNavigator
from .human_intervention import HumanInterventionDetector
from .crawler import FormCrawler

__all__ = [
    "BrowserManager",
    "FormDetector",
    "AutomationFieldMatcher",
    "FormFiller",
    "MultiPageNavigator",
    "HumanInterventionDetector",
    "FormCrawler",
]
