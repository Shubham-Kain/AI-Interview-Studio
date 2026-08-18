import uuid
from typing import Literal
from fastapi import (
    APIRouter,
    File,
    Form,
    HTTPException,
    UploadFile,
)
from pydantic import BaseModel

# ROUTER
router = APIRouter(
    prefix="/api/ai-interview",
    tags=["Interview with AI"],
)

# SESSION STORAGE (in-memory per-process)
interviews = {}

# START RESPONSE
class StartInterviewResponse(
    BaseModel
):
    interview_id: str
    role: str
    difficulty: str
    question_number: int
    total_questions: int
    question: str
    audio_base64: str

# ANSWER RESPONSE
class AnswerResponse(
    BaseModel
):
    interview_id: str
    question_number: int
    completed_questions: int
    total_questions: int
    transcript: str
    evaluation: str
    score: float
    next_question: str
    audio_base64: str
    interview_completed: bool

# FINAL RESPONSE
class FinalReportResponse(
    BaseModel
):
    interview_id: str
    completed_questions: int
    total_questions: int
    average_score: float
    final_report: str

# START
@router.post(
    "/start",
    response_model=StartInterviewResponse,
)
def start_interview(
    role: str = Form(...),
    difficulty: Literal[
        "Easy",
        "Medium",
        "Hard",
    ] = Form("Medium"),
):
    import main
    try:
        graph = main.get_interview_graph_service()
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Interview graph initialization failed: {str(e)}",
        )

    if graph is None:
        raise HTTPException(
            status_code=500,
            detail="Interview graph is not initialized.",
        )
    interview_id = str(
        uuid.uuid4()
    )
    try:
        result = (
            graph.start(
                role=role,
                difficulty=difficulty,
                interview_id=interview_id,
            )
        )
        interviews[
            interview_id
        ] = {
            "role": role,
            "difficulty": difficulty,
            "question_number": (
                result["question_number"]
            ),
            "completed_questions": 0,
            "current_question": (
                result["current_question"]
            ),
            "previous_questions": (
                result.get(
                    "previous_questions",
                    [],
                )
            ),
            "conversation": (
                result.get(
                    "conversation",
                    [],
                )
            ),
            "status": "running",
        }
        return {
            "interview_id": interview_id,
            "role": role,
            "difficulty": difficulty,
            "question_number": (
                result["question_number"]
            ),
            "total_questions": 5,
            "question": (
                result["current_question"]
            ),
            "audio_base64": (
                result["audio_base64"]
            ),
        }
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=(
                f"Could not start AI interview: "
                f"{str(e)}"
            ),
        )

# ANSWER
@router.post(
    "/answer",
    response_model=AnswerResponse,
)
async def answer_interview(
    interview_id: str = Form(...),
    audio: UploadFile = File(...),
):
    import main
    try:
        graph = main.get_interview_graph_service()
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Interview graph initialization failed: {str(e)}",
        )

    if graph is None:
        raise HTTPException(
            status_code=500,
            detail="Interview graph is not initialized.",
        )
    if interview_id not in interviews:
        raise HTTPException(
            status_code=404,
            detail="Interview session not found.",
        )
    session = interviews[
        interview_id
    ]
    if session["status"] != "running":
        raise HTTPException(
            status_code=400,
            detail="Interview is not active.",
        )
    try:
        audio_bytes = await audio.read()
        result = (
            graph.answer(
                interview_id=interview_id,
                role=session["role"],
                difficulty=session["difficulty"],
                question_number=session[
                    "question_number"
                ],
                current_question=session[
                    "current_question"
                ],
                previous_questions=session[
                    "previous_questions"
                ],
                conversation=session[
                    "conversation"
                ],
                completed_questions=session[
                    "completed_questions"
                ],
                audio_bytes=audio_bytes,
            )
        )
        # UPDATE
        completed_questions = result[
            "completed_questions"
        ]
        session[
            "completed_questions"
        ] = completed_questions
        session[
            "question_number"
        ] = result[
            "question_number"
        ]
        session[
            "current_question"
        ] = result[
            "current_question"
        ]
        session[
            "previous_questions"
        ] = result.get(
            "previous_questions",
            [],
        )
        session[
            "conversation"
        ] = result.get(
            "conversation",
            [],
        )
        # CHECK FINAL
        interview_completed = (
            completed_questions >= 5
        )
        if interview_completed:
            session[
                "status"
            ] = "completed"
        return {
            "interview_id": interview_id,
            "question_number": (
                result["question_number"]
            ),
            "completed_questions": (
                completed_questions
            ),
            "total_questions": 5,
            "transcript": (
                result["transcript"]
            ),
            "evaluation": (
                result["evaluation"]
            ),
            "score": result.get(
                "score",
                0,
            ),
            "next_question": (
                ""
                if interview_completed
                else result["current_question"]
            ),
            "audio_base64": (
                ""
                if interview_completed
                else result["audio_base64"]
            ),
            "interview_completed": (
                interview_completed
            ),
        }
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=(
                f"Could not process interview answer: "
                f"{str(e)}"
            ),
        )

# QUIT / FINALIZE EARLY
@router.post(
    "/quit",
    response_model=FinalReportResponse,
)
def quit_interview(
    interview_id: str,
):
    import main
    try:
        graph = main.get_interview_graph_service()
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Interview graph initialization failed: {str(e)}",
        )

    if graph is None:
        raise HTTPException(
            status_code=500,
            detail="Interview graph is not initialized.",
        )
    if interview_id not in interviews:
        return {
            "interview_id": interview_id,
            "completed_questions": 0,
            "total_questions": 5,
            "average_score": 0,
            "final_report": (
                "No interview answers were completed."
            ),
        }
    session = interviews[
        interview_id
    ]
    try:
        # GENERATE FINAL REPORT
        result = (
            graph.finalize(
                interview_id=interview_id,
                role=session["role"],
                difficulty=session["difficulty"],
                question_number=session[
                    "question_number"
                ],
                previous_questions=session[
                    "previous_questions"
                ],
                conversation=session[
                    "conversation"
                ],
                completed_questions=session[
                    "completed_questions"
                ],
            )
        )
        # REMOVE SESSION
        session["status"] = "stopped"
        del interviews[
            interview_id
        ]
        return {
            "interview_id": interview_id,
            "completed_questions": (
                session[
                    "completed_questions"
                ]
            ),
            "total_questions": 5,
            "average_score": (
                result.get(
                    "final_average_score",
                    0,
                )
            ),
            "final_report": (
                result.get(
                    "final_report",
                    "",
                )
            ),
        }
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=(
                f"Could not generate final interview report: "
                f"{str(e)}"
            ),
        )

# HEALTH
@router.get(
    "/health"
)
def health():
    return {
        "status": "ok",
        "service": "Interview with AI",
        "workflow": "LangGraph",
        "max_questions": 5,
        "stt": "faster-whisper",
        "tts": "edge-tts",
    }