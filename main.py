from fastapi import FastAPI
from langchain_openai import ChatOpenAI
from config import OPENROUTER_API_KEY
from resume_jd_rag import ResumeJDRAG
from question_generator import InterviewQuestionGenerator
from api.interview import (
    initialize_services,
    router as interview_router,
)
from api.ai_interview import (
    initialize_ai_interview_services,
    router as ai_interview_router,
)

###  FASTAPI APP   ###
app = FastAPI(
    title="AI Interview Generator API",
    description=(
        "Backend for Resume-JD analysis, "
        "interview question generation, "
        "and AI mock interviews."
    ),
    version="2.0.0",
)
###  LLM   ###
llm = ChatOpenAI(
    model_name="dots-studio/dots-3-note-preview:free",
    temperature=0.5,
    openai_api_base="https://openrouter.ai/api/v1",
    openai_api_key=OPENROUTER_API_KEY,
)
###  QUESTION GENERATOR SERVICES   ###
rag = ResumeJDRAG(
    llm=llm,
    persist_directory="./chroma_db",
    resume_k=2,
    jd_k=2,
)
question_generator = InterviewQuestionGenerator(
    llm=llm
)
###  INITIALIZE QUESTION GENERATOR SERVICES   ###
initialize_services(
    rag_service=rag,
    question_generator_service=question_generator,
)
###  INITIALIZE AI INTERVIEW LANGGRAPH   ###
initialize_ai_interview_services(
    llm=llm
)
###  ROUTERS   ###
app.include_router(
    interview_router
)
app.include_router(
    ai_interview_router
)
###  ROOT   ###
@app.get("/")
def root():
    return {
        "status": "running",
        "service": "AI Interview Generator API",
    }
###  HEALTH   ###
@app.get("/health")
def health():
    return {
        "status": "ok"
    }
