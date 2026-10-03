"""Profile schema definition and metadata."""

from dataclasses import dataclass
from typing import Dict, List, Optional


@dataclass
class SchemaFieldDef:
    key: str
    label: str
    section: str
    description: str
    is_required: bool = False
    expected_type: str = "string"  # "string", "email", "phone", "url", "integer"


STANDARD_SCHEMA_FIELDS: Dict[str, SchemaFieldDef] = {
    "name": SchemaFieldDef("name", "Full Name", "Personal", "Participant's full name", is_required=True),
    "email": SchemaFieldDef("email", "Email Address", "Personal", "Primary contact email address", is_required=True, expected_type="email"),
    "phone": SchemaFieldDef("phone", "Phone Number", "Personal", "Mobile or contact number", is_required=True, expected_type="phone"),
    "gender": SchemaFieldDef("gender", "Gender", "Personal", "Gender identity", is_required=False),
    "city": SchemaFieldDef("city", "City", "Personal", "Current city of residence", is_required=False),
    "country": SchemaFieldDef("country", "Country", "Personal", "Country of residence", is_required=False),

    "college": SchemaFieldDef("college", "College / University", "Education", "Current academic institution", is_required=True),
    "degree": SchemaFieldDef("degree", "Degree", "Education", "Degree program (e.g. B.Tech, B.Sc)", is_required=False),
    "branch": SchemaFieldDef("branch", "Branch / Major", "Education", "Field or department of study", is_required=False),
    "year": SchemaFieldDef("year", "Year of Study", "Education", "Current year (e.g. 1, 2, 3, 4)", is_required=False),
    "graduation_year": SchemaFieldDef("graduation_year", "Graduation Year", "Education", "Expected year of graduation", is_required=False, expected_type="integer"),

    "github": SchemaFieldDef("github", "GitHub Profile", "Links", "GitHub profile or repository URL", is_required=False, expected_type="url"),
    "linkedin": SchemaFieldDef("linkedin", "LinkedIn Profile", "Links", "LinkedIn profile URL", is_required=False, expected_type="url"),
    "portfolio": SchemaFieldDef("portfolio", "Portfolio Website", "Links", "Personal website or portfolio URL", is_required=False, expected_type="url"),
    "resume": SchemaFieldDef("resume", "Resume Link", "Links", "URL to resume or hosted CV", is_required=False, expected_type="url"),

    "team_name": SchemaFieldDef("team_name", "Team Name", "Team", "Name of hackathon squad or team", is_required=False),
    "team_size": SchemaFieldDef("team_size", "Team Size", "Team", "Total number of members in team", is_required=False, expected_type="integer"),

    "skills": SchemaFieldDef("skills", "Technical Skills", "Hackathon", "Comma-separated programming skills", is_required=False),
    "hackathon_experience": SchemaFieldDef("hackathon_experience", "Hackathon Experience", "Hackathon", "Past hackathon participation (Yes/No)", is_required=False),
    "why_participate": SchemaFieldDef("why_participate", "Motivation Essay", "Hackathon", "Reason for participating in the hackathon", is_required=False),
    "project_idea": SchemaFieldDef("project_idea", "Project Idea", "Hackathon", "Summary of hackathon project concept", is_required=False),
}


class ProfileSchema:
    @staticmethod
    def get_field(key: str) -> Optional[SchemaFieldDef]:
        return STANDARD_SCHEMA_FIELDS.get(key.lower().strip())

    @staticmethod
    def all_sections() -> List[str]:
        sections: List[str] = []
        for f in STANDARD_SCHEMA_FIELDS.values():
            if f.section not in sections:
                sections.append(f.section)
        return sections
