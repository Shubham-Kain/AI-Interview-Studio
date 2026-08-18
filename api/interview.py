from typing import Literal
from fastapi import APIRouter, HTTPException
from pydantic import BaseModel, Field
from resume_jd_rag import ResumeJDRAG
from question_generator import InterviewQuestionGenerator
# ROUTER
router = APIRouter(
    prefix="/api/interview",
    tags=["Interview Generator"],
)

def ensure_services():
    global rag, question_generator
    if rag is not None and question_generator is not None:
        return
    from main import llm
    if rag is None:
        rag = ResumeJDRAG(
            llm=llm,
            persist_directory="./chroma_db",
            resume_k=2,
            jd_k=2,
        )
    if question_generator is None:
        question_generator = InterviewQuestionGenerator(
            llm=llm,
        )
    initialize_services(
        rag_service=rag,
        question_generator_service=question_generator,
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
# SERVICES
rag = None
question_generator = None
def initialize_services(
    rag_service: ResumeJDRAG,
    question_generator_service: InterviewQuestionGenerator,
):
    global rag
    global question_generator
    rag = rag_service
    question_generator = (
        question_generator_service
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
    ensure_services()
    if rag is None:
        raise HTTPException(
            status_code=500,
            detail="RAG service is not initialized.",
        )
    if question_generator is None:
        raise HTTPException(
            status_code=500,
            detail="Question generator is not initialized.",
        )
    try:
        # CLEAR PREVIOUS DATA
        rag.clear_collections()
        # ADD RESUME
        rag.add_resume(
            resume_text=request.resume_text,
            candidate_id="api_candidate",
        )
        # ADD JOB DESCRIPTION
        rag.add_job_description(
            job_description=request.job_description,
            job_id="api_job",
        )
        # GAP ANALYSIS
        gap_result = rag.analyze()
        # JOB TITLE
        final_job_title = (
            gap_result.job.job_title.strip()
            if gap_result.job.job_title
            else request.job_title.strip()
        )
        # GENERATE QUESTIONS
        question_result = (
            question_generator.generate(
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