from typing import List, Literal, Any
from pydantic import BaseModel, Field, ConfigDict, field_validator


def _clean_list(v: Any) -> List[str]:
    if not isinstance(v, list):
        return [str(v)] if v else []
    return [str(item) for item in v]


class CategoryDistribution(BaseModel):
    model_config = ConfigDict(extra="allow", populate_by_name=True)
    Basic: int = Field(default=0)
    Technical: int = Field(default=0)
    Resume_Based: int = Field(default=0, alias="Resume-Based")
    Project_Based: int = Field(default=0, alias="Project-Based")
    Scenario_Based: int = Field(default=0, alias="Scenario-Based")
    Skill_Gap: int = Field(default=0, alias="Skill Gap")


class InterviewQuestion(BaseModel):
    model_config = ConfigDict(extra="allow", populate_by_name=True)
    question_id: int = 1
    category: str = "Technical"
    difficulty: str = "Medium"
    question: str = ""
    expected_answer: str = ""
    key_points: List[str] = Field(default_factory=list)

    @field_validator("key_points", mode="before")
    @classmethod
    def clean_key_points(cls, v):
        return _clean_list(v)


class InterviewQuestionSet(BaseModel):
    model_config = ConfigDict(extra="allow", populate_by_name=True)
    job_title: str = "Technical Role"
    total_questions: int = 6
    category_distribution: CategoryDistribution = Field(
        default_factory=CategoryDistribution
    )
    questions: List[InterviewQuestion] = Field(default_factory=list)