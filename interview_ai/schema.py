from typing import List
from pydantic import BaseModel, Field

class InterviewEvaluation(BaseModel):
    evaluation: str = Field(
        description="Brief evaluation of the candidate's answer."
    )
    strengths: List[str] = Field(
        default_factory=list,
        description="Strong points in the candidate answer."
    )
    weaknesses: List[str] = Field(
        default_factory=list,
        description="Weak or missing points in the candidate answer."
    )
    score: float = Field(
        ge=0,
        le=10,
        description="Answer score from 0 to 10."
    )
    next_question: str = Field(
        description="The next interview question."
    )