from typing import Any, Dict, List, Optional, TypedDict

class InterviewState(TypedDict, total=False):
    # INPUT DATA
    resume_text: str
    job_description: str
    # USER SETTINGS
    job_title: str
    difficulty: str
    num_questions: int
    # RAG CONTEXT
    resume_context: str
    job_description_context: str
    # RAG RESULT
    rag_result: Dict[str, Any]
    # FINAL QUESTIONS
    interview_questions: Dict[str, Any]
    # ERROR
    error: Optional[str]