from fastapi import FastAPI
from langchain_openai import ChatOpenAI
from config import OPENROUTER_API_KEY
from api.interview import (
    router as interview_router,
)
from api.ai_interview import (
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
