from typing import Dict, List, Literal
from pydantic import BaseModel, Field
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
    category_distribution: Dict[str, int]
    questions: List[InterviewQuestion]