"""Intelligent offline field matching and confidence scoring engine."""

import re
from difflib import SequenceMatcher
from typing import Dict, List, Optional, Tuple, Set
from ..models.form_field import FormField, FieldMatch, FieldType
from ..models.profile import UserProfile
from .helpers import normalize_field_name


# Maintainable dictionary of canonical profile keys to known aliases/synonyms
CANONICAL_ALIASES: Dict[str, List[str]] = {
    "name": [
        "name", "full_name", "fullname", "first_name", "candidate_name",
        "participant_name", "applicant_name", "your_name", "student_name",
        "person_name", "display_name", "user_name"
    ],
    "first_name": [
        "first_name", "firstname", "given_name", "fname"
    ],
    "last_name": [
        "last_name", "lastname", "surname", "family_name", "lname"
    ],
    "email": [
        "email", "email_address", "emailaddress", "mail", "contact_email",
        "primary_email", "student_email", "university_email", "college_email"
    ],
    "phone": [
        "phone", "phone_number", "phonenumber", "mobile", "mobile_number",
        "mobilenumber", "contact_number", "contact_no", "cell_phone",
        "telephone", "tel", "whatsapp", "whatsapp_number"
    ],
    "college": [
        "college", "university", "institution", "school", "organization",
        "school_name", "college_name", "university_name", "institute",
        "academic_institution", "campus", "faculty"
    ],
    "degree": [
        "degree", "degree_program", "program", "course", "qualification",
        "pursuing_degree", "current_degree", "education_level", "study_program"
    ],
    "branch": [
        "branch", "department", "field_of_study", "major", "specialization",
        "discipline", "stream", "course_branch", "study_field"
    ],
    "year": [
        "year", "year_of_study", "study_year", "current_year", "academic_year",
        "class_year", "grade_level"
    ],
    "graduation_year": [
        "graduation_year", "grad_year", "batch", "passout_year", "expected_graduation"
    ],
    "gender": [
        "gender", "sex"
    ],
    "city": [
        "city", "town", "current_city", "residence_city", "location_city"
    ],
    "state": [
        "state", "province", "region"
    ],
    "country": [
        "country", "nationality", "residence_country"
    ],
    "postal_code": [
        "postal_code", "zip", "zip_code", "pincode", "pin_code"
    ],
    "github": [
        "github", "github_url", "github_profile", "github_username",
        "github_handle", "github_link", "gh_profile"
    ],
    "linkedin": [
        "linkedin", "linkedin_url", "linkedin_profile", "linkedin_link",
        "linkedin_handle"
    ],
    "portfolio": [
        "portfolio", "portfolio_url", "website", "personal_website",
        "personal_site", "blog", "portfolio_link"
    ],
    "resume": [
        "resume", "resume_url", "cv", "cv_url", "resume_link"
    ],
    "team_name": [
        "team_name", "team", "squad_name", "group_name", "team_title"
    ],
    "team_size": [
        "team_size", "number_of_members", "members", "team_count",
        "member_count", "squad_size"
    ],
    "skills": [
        "skills", "technologies", "tech_stack", "programming_languages",
        "expertise", "tools", "competencies"
    ],
    "hackathon_experience": [
        "hackathon_experience", "prior_hackathons", "hackathons_attended",
        "participated_before", "experience_level"
    ],
    "why_participate": [
        "why_participate", "motivation", "why_attend", "why_join",
        "reason_to_participate", "why_do_you_want_to_participate",
        "essay_motivation", "learning_goals"
    ],
    "project_idea": [
        "project_idea", "project_description", "proposed_project",
        "idea_summary", "project_pitch", "hack_concept", "what_will_you_build"
    ],
    "tshirt_size": [
        "tshirt_size", "t_shirt_size", "shirt_size", "apparel_size", "swag_size"
    ],
    "dietary_restrictions": [
        "dietary_restrictions", "diet", "food_preference", "meal_preference",
        "dietary_requirements"
    ],
    "emergency_contact_name": [
        "emergency_contact_name", "emergency_contact", "guardian_name"
    ],
    "emergency_contact_phone": [
        "emergency_contact_phone", "emergency_phone", "guardian_phone"
    ]
}


class FieldMatcherEngine:
    """Intelligent offline field matching and confidence assessment."""

    CONFIDENCE_EXACT = 0.95
    CONFIDENCE_STRONG_ALIAS = 0.88
    CONFIDENCE_PROBABLE = 0.72
    CONFIDENCE_UNCERTAIN = 0.45
    AUTO_FILL_THRESHOLD = 0.70  # Fields with confidence >= 0.70 are safe to auto-fill

    def __init__(self, custom_aliases: Optional[Dict[str, List[str]]] = None):
        self.aliases: Dict[str, List[str]] = dict(CANONICAL_ALIASES)
        if custom_aliases:
            for key, val in custom_aliases.items():
                if key in self.aliases:
                    self.aliases[key].extend(val)
                else:
                    self.aliases[key] = val

    def match_field(self, field: FormField, profile: UserProfile) -> FieldMatch:
        """
        Evaluate a single FormField against a UserProfile to determine the best match
        and compute its confidence score.
        """
        # Flag legal agreements, terms of service, declarations
        legal_keywords = {"terms", "condition", "conduct", "agree", "declaration", "policy", "privacy", "consent"}
        field_context = field.identifier_context.lower()
        if any(kw in field_context for kw in legal_keywords) and field.field_type == FieldType.CHECKBOX:
            field.is_terms_or_legal = True
            return FieldMatch(
                field=field,
                matched_key=None,
                matched_value=None,
                confidence=0.0,
                match_reason="Legal agreement / declaration requires explicit user confirmation",
                status="MANUAL_REQUIRED"
            )

        best_key: Optional[str] = None
        best_confidence = 0.0
        best_reason = "unmatched"

        # Candidate identifiers to inspect
        norm_name = normalize_field_name(field.name)
        norm_id = normalize_field_name(field.id_attr)
        norm_label = normalize_field_name(field.label)
        norm_placeholder = normalize_field_name(field.placeholder)
        norm_aria = normalize_field_name(field.aria_label)

        attributes_to_check = [
            (norm_name, 1.0),
            (norm_id, 0.95),
            (norm_label, 0.98),
            (norm_placeholder, 0.85),
            (norm_aria, 0.90)
        ]

        # Check against available profile keys
        for profile_key, profile_val in profile.fields.items():
            if not profile_val:
                continue

            # 1. Exact canonical key match
            for attr_val, weight in attributes_to_check:
                if not attr_val:
                    continue
                if attr_val == profile_key:
                    conf = self.CONFIDENCE_EXACT * weight
                    if conf > best_confidence:
                        best_confidence = conf
                        best_key = profile_key
                        best_reason = f"Exact key match on '{attr_val}'"

            # 2. Alias match
            known_aliases = self.aliases.get(profile_key, [profile_key])
            for alias in known_aliases:
                norm_alias = normalize_field_name(alias)
                for attr_val, weight in attributes_to_check:
                    if not attr_val:
                        continue
                    if attr_val == norm_alias:
                        conf = self.CONFIDENCE_STRONG_ALIAS * weight
                        if conf > best_confidence:
                            best_confidence = conf
                            best_key = profile_key
                            best_reason = f"Alias match '{attr_val}' -> '{profile_key}'"
                    elif norm_alias in attr_val or attr_val in norm_alias:
                        # Substring overlap
                        overlap_ratio = len(norm_alias) / max(len(attr_val), 1)
                        if overlap_ratio >= 0.5:
                            conf = self.CONFIDENCE_PROBABLE * weight * min(1.0, overlap_ratio)
                            if conf > best_confidence:
                                best_confidence = conf
                                best_key = profile_key
                                best_reason = f"Probable alias substring in '{attr_val}'"

            # 3. String similarity (SequenceMatcher) on label and name
            for target_text in (field.label, field.name, field.placeholder):
                if not target_text:
                    continue
                sim = SequenceMatcher(None, profile_key.replace("_", " "), target_text.lower()).ratio()
                if sim >= 0.75:
                    conf = max(self.CONFIDENCE_UNCERTAIN, sim * 0.85)
                    if conf > best_confidence:
                        best_confidence = conf
                        best_key = profile_key
                        best_reason = f"Semantic similarity ({int(sim*100)}%) on '{target_text}'"

        # Determine matched value and status
        matched_value = profile.get(best_key) if best_key else None
        status = "UNRESOLVED"

        if best_confidence >= self.AUTO_FILL_THRESHOLD and matched_value:
            status = "FILLED"
        elif best_confidence >= self.CONFIDENCE_UNCERTAIN and matched_value:
            status = "PENDING_CONFIRMATION"
        else:
            status = "UNRESOLVED"

        return FieldMatch(
            field=field,
            matched_key=best_key,
            matched_value=matched_value,
            confidence=round(best_confidence, 2),
            match_reason=best_reason,
            status=status
        )

    def match_all(self, fields: List[FormField], profile: UserProfile) -> List[FieldMatch]:
        """Match all inspected DOM fields against the given profile."""
        return [self.match_field(f, profile) for f in fields]

    @staticmethod
    def match_option_value(options: List[str], target_value: str) -> Optional[str]:
        """
        Find best matching option string from a list of select/radio choices.
        Tolerates case, punctuation, and common suffixes (e.g. '3' matches '3rd Year').
        """
        if not options or not target_value:
            return None

        target_norm = normalize_field_name(target_value)

        # 1. Exact match
        for opt in options:
            if opt.strip().lower() == target_value.strip().lower():
                return opt

        # 2. Normalized match
        for opt in options:
            if normalize_field_name(opt) == target_norm:
                return opt

        # 3. Substring match
        for opt in options:
            norm_opt = normalize_field_name(opt)
            if target_norm in norm_opt or norm_opt in target_norm:
                return opt

        # 4. Fuzzy match
        best_opt = None
        best_ratio = 0.0
        for opt in options:
            ratio = SequenceMatcher(None, target_norm, normalize_field_name(opt)).ratio()
            if ratio > best_ratio and ratio >= 0.60:
                best_ratio = ratio
                best_opt = opt

        return best_opt
