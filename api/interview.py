from typing import Literal
from fastapi import APIRouter, HTTPException
from pydantic import BaseModel, Field

# ROUTER
router = APIRouter(
    prefix="/api/interview",
    tags=["Interview Generator"],
)

# REQUEST MODEL
class InterviewGenerateRequest(BaseModel):
    resume_text: str = Field(
        ...,
        min_length=1,
    )
    job_description: str = Field(
        ...,
        min_length=1,
    )
    job_title: str = Field(
        ...,
        min_length=1,
    )
    difficulty: Literal[
        "Easy",
        "Medium",
        "Hard",
    ]
    num_questions: int = Field(
        ...,
        ge=6,
        le=30,
    )

# HEALTH
@router.get("/health")
def health():
    return {
        "status": "ok",
        "service": "Interview Generator",
    }

# GENERATE INTERVIEW QUESTIONS
@router.post("/generate")
def generate_interview(
    request: InterviewGenerateRequest,
):
    # Lazy-load services from main to avoid circular import
    # and to prevent heavy models loading at server startup
    import main
    try:
        local_rag = main.get_rag_service()
        local_question_generator = main.get_question_generator_service()
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Service initialization failed: {str(e)}",
        )

    if local_rag is None:
        raise HTTPException(
            status_code=500,
            detail="RAG service is not initialized.",
        )
    if local_question_generator is None:
        raise HTTPException(
            status_code=500,
            detail="Question generator is not initialized.",
        )
    try:
        # CLEAR PREVIOUS DATA
        local_rag.clear_collections()
        # ADD RESUME
        local_rag.add_resume(
            resume_text=request.resume_text,
            candidate_id="api_candidate",
        )
        # ADD JOB DESCRIPTION
        local_rag.add_job_description(
            job_description=request.job_description,
            job_id="api_job",
        )
        # GAP ANALYSIS
        gap_result = local_rag.analyze()
        # JOB TITLE
        final_job_title = (
            gap_result.job.job_title.strip()
            if gap_result.job.job_title
            else request.job_title.strip()
        )
        # GENERATE QUESTIONS
        question_result = (
            local_question_generator.generate(
                rag_result=gap_result,
                job_title=final_job_title,
                difficulty=request.difficulty,
                num_questions=request.num_questions,
            )
        )
        # RESPONSE
        return {
            "success": True,
            "job_title": final_job_title,
            "gap_analysis": gap_result.model_dump(),
            "interview_questions": (
                question_result.model_dump()
            ),
        }
    except ValueError as e:
        raise HTTPException(
            status_code=400,
            detail=str(e),
        )
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=str(e),
        )