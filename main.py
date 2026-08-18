from fastapi import FastAPI
from langchain_openai import ChatOpenAI
from config import OPENROUTER_API_KEY
from resume_jd_rag import ResumeJDRAG
from question_generator import InterviewQuestionGenerator
from api.interview import router as interview_router
from api.ai_interview import router as ai_interview_router

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
###  GLOBAL SERVICES (initialized at startup)  ###
rag_service = None
question_generator_service = None
interview_graph_service = None
###  STARTUP EVENT   ###
@app.on_event("startup")
async def startup():
    global rag_service, question_generator_service, interview_graph_service
    try:
        rag_service = ResumeJDRAG(
            llm=llm,
            persist_directory="./chroma_db",
            resume_k=2,
            jd_k=2,
        )
        question_generator_service = InterviewQuestionGenerator(
            llm=llm
        )
        from interview_ai.graph import AIInterviewGraph
        interview_graph_service = AIInterviewGraph(
            llm=llm
        )
        print("✓ Services initialized at startup")
    except Exception as e:
        print(f"✗ Startup error: {e}")
        raise
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
