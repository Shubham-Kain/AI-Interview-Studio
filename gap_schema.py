from typing import List, Literal, Union, Any
from pydantic import BaseModel, Field, ConfigDict, field_validator


def _stringify_item(v: Any) -> str:
    if isinstance(v, dict):
        # Flatten dict to string summary e.g. "Senior Python Developer at XYZ"
        parts = []
        for key in ["title", "role", "name", "company", "description"]:
            if key in v and v[key]:
                parts.append(str(v[key]))
        return " - ".join(parts) if parts else str(v)
    return str(v)


def _clean_list(v: Any) -> List[str]:
    if not isinstance(v, list):
        return [_stringify_item(v)] if v else []
    return [_stringify_item(item) for item in v]


# =========================================================
# BASE FLEXIBLE MODEL (extra="allow" for resilient prompt-based JSON)
# =========================================================
class FlexibleModel(BaseModel):
    model_config = ConfigDict(extra="allow", populate_by_name=True)


# =========================================================
# EXPERIENCE GAP
# =========================================================
class ExperienceGap(FlexibleModel):
    required: str = ""
    candidate: str = ""
    status: str = "Unknown"
    gap: str = ""


# =========================================================
# RESPONSIBILITY GAP
# =========================================================
class ResponsibilityGap(FlexibleModel):
    supported: List[str] = Field(default_factory=list)
    partially_supported: List[str] = Field(default_factory=list)
    not_supported: List[str] = Field(default_factory=list)

    @field_validator("supported", "partially_supported", "not_supported", mode="before")
    @classmethod
    def clean_lists(cls, v):
        return _clean_list(v)


# =========================================================
# SKILL GAP ANALYSIS
# =========================================================
class SkillGapAnalysis(FlexibleModel):
    critical_gaps: List[str] = Field(default_factory=list)
    moderate_gaps: List[str] = Field(default_factory=list)
    minor_gaps: List[str] = Field(default_factory=list)

    @field_validator("critical_gaps", "moderate_gaps", "minor_gaps", mode="before")
    @classmethod
    def clean_lists(cls, v):
        return _clean_list(v)


# =========================================================
# JOB INFORMATION
# =========================================================
class JobInformation(FlexibleModel):
    job_title: str = ""
    required_skills: List[str] = Field(default_factory=list)
    preferred_skills: List[str] = Field(default_factory=list)
    experience_requirements: List[str] = Field(default_factory=list)
    responsibilities: List[str] = Field(default_factory=list)
    technologies: List[str] = Field(default_factory=list)
    other_requirements: List[str] = Field(default_factory=list)

    @field_validator(
        "required_skills",
        "preferred_skills",
        "experience_requirements",
        "responsibilities",
        "technologies",
        "other_requirements",
        mode="before",
    )
    @classmethod
    def clean_lists(cls, v):
        return _clean_list(v)


# =========================================================
# CANDIDATE INFORMATION
# =========================================================
class CandidateInformation(FlexibleModel):
    name: str = ""
    education: List[str] = Field(default_factory=list)
    technical_skills: List[str] = Field(default_factory=list)
    projects: List[str] = Field(default_factory=list)
    work_experience: List[str] = Field(default_factory=list)
    certifications: List[str] = Field(default_factory=list)
    tools_and_technologies: List[str] = Field(default_factory=list)

    @field_validator(
        "education",
        "technical_skills",
        "projects",
        "work_experience",
        "certifications",
        "tools_and_technologies",
        mode="before",
    )
    @classmethod
    def clean_lists(cls, v):
        return _clean_list(v)


# =========================================================
# COMPARISON
# =========================================================
class ComparisonResult(FlexibleModel):
    matched_required_skills: List[str] = Field(default_factory=list)
    partially_matched_required_skills: List[str] = Field(default_factory=list)
    missing_required_skills: List[str] = Field(default_factory=list)
    unknown_required_skills: List[str] = Field(default_factory=list)
    matched_preferred_skills: List[str] = Field(default_factory=list)
    missing_preferred_skills: List[str] = Field(default_factory=list)
    matching_technologies: List[str] = Field(default_factory=list)
    partial_technologies: List[str] = Field(default_factory=list)
    missing_technologies: List[str] = Field(default_factory=list)
    unknown_technologies: List[str] = Field(default_factory=list)

    @field_validator(
        "matched_required_skills",
        "partially_matched_required_skills",
        "missing_required_skills",
        "unknown_required_skills",
        "matched_preferred_skills",
        "missing_preferred_skills",
        "matching_technologies",
        "partial_technologies",
        "missing_technologies",
        "unknown_technologies",
        mode="before",
    )
    @classmethod
    def clean_lists(cls, v):
        return _clean_list(v)


# =========================================================
# OVERALL FIT
# =========================================================
class OverallFit(FlexibleModel):
    status: str = "Good Match"
    reason: str = ""


# =========================================================
# INTERVIEW FOCUS AREA
# =========================================================
class InterviewFocusArea(FlexibleModel):
    topic: str = ""
    reason: str = ""
    priority: str = "Medium"


# =========================================================
# COMPLETE GAP ANALYSIS
# =========================================================
class GapAnalysisResult(FlexibleModel):
    job: JobInformation = Field(default_factory=JobInformation)
    candidate: CandidateInformation = Field(default_factory=CandidateInformation)
    comparison: ComparisonResult = Field(default_factory=ComparisonResult)
    experience_gap: ExperienceGap = Field(default_factory=ExperienceGap)
    responsibility_gap: ResponsibilityGap = Field(default_factory=ResponsibilityGap)
    skill_gap_analysis: SkillGapAnalysis = Field(default_factory=SkillGapAnalysis)
    additional_candidate_skills: List[str] = Field(default_factory=list)
    interview_focus_areas: List[InterviewFocusArea] = Field(default_factory=list)
    overall_fit: OverallFit = Field(default_factory=OverallFit)

    @field_validator("additional_candidate_skills", mode="before")
    @classmethod
    def clean_skills(cls, v):
        return _clean_list(v)