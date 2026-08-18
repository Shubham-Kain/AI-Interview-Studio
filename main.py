from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from config import OPENROUTER_API_KEY, MODEL_NAME, OPENROUTER_BASE_URL

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

###  CORS MIDDLEWARE (required for Streamlit Cloud → Render cross-origin calls) ###
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

###  LLM (lazy singleton — created once on first use) ###
_llm = None

def get_llm():
    global _llm
    if _llm is None:
        if not OPENROUTER_API_KEY:
            raise RuntimeError(
                "OPENROUTER_API_KEY environment variable is not set. "
                "Add it to your Render environment variables."
            )
        from langchain_openai import ChatOpenAI
        _llm = ChatOpenAI(
            model_name=MODEL_NAME,
            temperature=0.5,
            openai_api_base=OPENROUTER_BASE_URL,
            openai_api_key=OPENROUTER_API_KEY,
        )
    return _llm

###  GLOBAL SERVICES (lazy-loaded on first use)  ###
rag_service = None
question_generator_service = None
interview_graph_service = None

def get_rag_service():
    global rag_service
    if rag_service is None:
        from resume_jd_rag import ResumeJDRAG
        rag_service = ResumeJDRAG(
            llm=get_llm(),
            persist_directory="./chroma_db",
            resume_k=2,
            jd_k=2,
        )
    return rag_service

def get_question_generator_service():
    global question_generator_service
    if question_generator_service is None:
        from question_generator import InterviewQuestionGenerator
        question_generator_service = InterviewQuestionGenerator(
            llm=get_llm()
        )
    return question_generator_service

def get_interview_graph_service():
    global interview_graph_service
    if interview_graph_service is None:
        from interview_ai.graph import AIInterviewGraph
        interview_graph_service = AIInterviewGraph(
            llm=get_llm()
        )
    return interview_graph_service

###  ROUTERS (imported AFTER middleware is set up) ###
from api.interview import router as interview_router
from api.ai_interview import router as ai_interview_router

app.include_router(interview_router)
app.include_router(ai_interview_router)

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
