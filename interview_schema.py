from typing import List, Literal
from pydantic import BaseModel, Field, ConfigDict

###  BASE MODEL WITH STRICT SCHEMA (OpenAI/Darkbloom compatible) ###
class StrictModel(BaseModel):
    model_config = ConfigDict(extra="forbid", populate_by_name=True)

###  CATEGORY DISTRIBUTION MODEL ###
class CategoryDistribution(StrictModel):
    Basic: int = Field(default=0)
    Technical: int = Field(default=0)
    Resume_Based: int = Field(default=0, alias="Resume-Based")
    Project_Based: int = Field(default=0, alias="Project-Based")
    Scenario_Based: int = Field(default=0, alias="Scenario-Based")
    Skill_Gap: int = Field(default=0, alias="Skill Gap")

###  SINGLE INTERVIEW QUESTION   ###
class InterviewQuestion(StrictModel):
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
class InterviewQuestionSet(StrictModel):
    job_title: str
    total_questions: int
    category_distribution: CategoryDistribution = Field(
        default_factory=CategoryDistribution
    )
    questions: List[InterviewQuestion]