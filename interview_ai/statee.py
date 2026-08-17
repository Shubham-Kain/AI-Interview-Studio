from typing import List, TypedDict

class InterviewState(TypedDict, total=False):
    # SESSION
    interview_id: str
    role: str
    difficulty: str
    status: str
    # QUESTION CONTROL
    question_number: int
    max_questions: int
    completed_questions: int
    current_question: str
    previous_questions: List[str]
    # CONVERSATION
    conversation: List[str]
    # CURRENT ANSWER
    audio_bytes: bytes
    transcript: str
    # CURRENT EVALUATION
    evaluation: str
    score: float
    strengths: List[str]
    weaknesses: List[str]
    # NEXT QUESTION
    next_question: str
    # TTS
    audio_base64: str
    # FINAL REPORT
    final_report: str
    final_average_score: float
    final_strengths: List[str]
    final_improvements: List[str]
    # GRAPH ACTION
    action: str