from typing import List, Literal
from pydantic import BaseModel, Field, ConfigDict

###  CATEGORY DISTRIBUTION MODEL (avoids untyped Dict schema 422 errors) ###
class CategoryDistribution(BaseModel):
    model_config = ConfigDict(populate_by_name=True, extra="allow")
    Basic: int = Field(default=0)
    Technical: int = Field(default=0)
    Resume_Based: int = Field(default=0, alias="Resume-Based")
    Project_Based: int = Field(default=0, alias="Project-Based")
    Scenario_Based: int = Field(default=0, alias="Scenario-Based")
    Skill_Gap: int = Field(default=0, alias="Skill Gap")

###  SINGLE INTERVIEW QUESTION   ###
class InterviewQuestion(BaseModel):
    question_id: int
    category: Literal[
        "Basic",
        "Technical",
        "Resume-Based",
        "Project-Based",
        "Scenario-Based",
        "Skill Gap",
    ]
    difficulty: Literal[
        "Easy",
        "Medium",
        "Hard",
    ]
    question: str
    expected_answer: str
    key_points: List[str] = Field(
        default_factory=list
    )

###  COMPLETE QUESTION SET   ###
class InterviewQuestionSet(BaseModel):
    job_title: str
    total_questions: int
    category_distribution: CategoryDistribution = Field(
        default_factory=CategoryDistribution
    )
    questions: List[InterviewQuestion]