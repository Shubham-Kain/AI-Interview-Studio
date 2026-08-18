from typing import List, Literal
from pydantic import BaseModel, Field, ConfigDict

# =========================================================
# BASE STRICT MODEL
# =========================================================
class StrictModel(BaseModel):
    model_config = ConfigDict(extra="forbid", populate_by_name=True)

# =========================================================
# EXPERIENCE GAP
# =========================================================
class ExperienceGap(StrictModel):
    required: str = ""
    candidate: str = ""
    status: Literal[
        "Matched",
        "Partial",
        "Missing",
        "Unknown",
    ] = "Unknown"
    gap: str = ""

# =========================================================
# RESPONSIBILITY GAP
# =========================================================
class ResponsibilityGap(StrictModel):
    supported: List[str] = Field(
        default_factory=list
    )
    partially_supported: List[str] = Field(
        default_factory=list
    )
    not_supported: List[str] = Field(
        default_factory=list
    )

# =========================================================
# SKILL GAP ANALYSIS
# =========================================================
class SkillGapAnalysis(StrictModel):
    critical_gaps: List[str] = Field(
        default_factory=list
    )
    moderate_gaps: List[str] = Field(
        default_factory=list
    )
    minor_gaps: List[str] = Field(
        default_factory=list
    )

# =========================================================
# JOB INFORMATION
# =========================================================
class JobInformation(StrictModel):
    job_title: str = ""
    required_skills: List[str] = Field(
        default_factory=list
    )
    preferred_skills: List[str] = Field(
        default_factory=list
    )
    experience_requirements: List[str] = Field(
        default_factory=list
    )
    responsibilities: List[str] = Field(
        default_factory=list
    )
    technologies: List[str] = Field(
        default_factory=list
    )
    other_requirements: List[str] = Field(
        default_factory=list
    )

# =========================================================
# CANDIDATE INFORMATION
# =========================================================
class CandidateInformation(StrictModel):
    name: str = ""
    education: List[str] = Field(
        default_factory=list
    )
    technical_skills: List[str] = Field(
        default_factory=list
    )
    projects: List[str] = Field(
        default_factory=list
    )
    work_experience: List[str] = Field(
        default_factory=list
    )
    certifications: List[str] = Field(
        default_factory=list
    )
    tools_and_technologies: List[str] = Field(
        default_factory=list
    )

# =========================================================
# COMPARISON
# =========================================================
class ComparisonResult(StrictModel):
    matched_required_skills: List[str] = Field(
        default_factory=list
    )
    partially_matched_required_skills: List[str] = Field(
        default_factory=list
    )
    missing_required_skills: List[str] = Field(
        default_factory=list
    )
    unknown_required_skills: List[str] = Field(
        default_factory=list
    )
    matched_preferred_skills: List[str] = Field(
        default_factory=list
    )
    missing_preferred_skills: List[str] = Field(
        default_factory=list
    )
    matching_technologies: List[str] = Field(
        default_factory=list
    )
    partial_technologies: List[str] = Field(
        default_factory=list
    )
    missing_technologies: List[str] = Field(
        default_factory=list
    )
    unknown_technologies: List[str] = Field(
        default_factory=list
    )

# =========================================================
# OVERALL FIT
# =========================================================
class OverallFit(StrictModel):
    status: Literal[
        "Strong Match",
        "Good Match",
        "Moderate Match",
        "Weak Match",
        "Insufficient Evidence",
    ] = "Insufficient Evidence"
    reason: str = ""

# =========================================================
# INTERVIEW FOCUS AREA
# =========================================================
class InterviewFocusArea(StrictModel):
    topic: str = ""
    reason: str = ""
    priority: str = "Medium"

# =========================================================
# COMPLETE GAP ANALYSIS
# =========================================================
class GapAnalysisResult(StrictModel):
    job: JobInformation
    candidate: CandidateInformation
    comparison: ComparisonResult
    experience_gap: ExperienceGap
    responsibility_gap: ResponsibilityGap
    skill_gap_analysis: SkillGapAnalysis
    additional_candidate_skills: List[str] = Field(
        default_factory=list
    )
    interview_focus_areas: List[InterviewFocusArea] = Field(
        default_factory=list
    )
    overall_fit: OverallFit