# 🎙️ AI Interview Studio
AI-powered interview preparation platform combining **Resume-JD analysis, RAG-based skill-gap detection, personalized question generation, and a separate AI mock interview with voice interaction**.

## Overview
The project has two main modules:

### 📝 Interview Question Generator
**Input:** Resume + Job Description + Job Title + Difficulty + 6–30 questions.

**Pipeline:**

```
Resume + JD
   ↓
Text Extraction
   ↓
Embeddings + ChromaDB
   ↓
Resume/JD Retrieval Queries
   ↓
RAG Gap Analysis
   ↓
Personalized Questions
```
The generator covers **Basic, Technical, Resume-Based, Project-Based, Scenario-Based, and Skill Gap** questions. Each question includes difficulty, expected answer, and key points.

### 🎙️ Interview with AI
The user selects a role and difficulty and starts a maximum **5-question** mock interview.

```
Start
 ↓
AI Question → TTS
 ↓
Candidate Voice → STT
 ↓
LangGraph Evaluation
 ↓
Next Question
 ↓
Repeat up to 5 questions
 ↓
Final Evaluation Report
```
If the user quits early, the final report uses only completed answers.

## ✨ Key Features

- Resume upload: PDF, TXT, MD
- Job Description text input
- Semantic Resume-JD retrieval
- Required, preferred, partial, and missing skill analysis
- Technology and experience gap detection
- Personalized questions from 6 categories
- Easy / Medium / Hard difficulty
- 6–30 generated questions
- Expected answers and key points
- Separate AI mock-interview module
- Local Speech-to-Text with faster-whisper
- Text-to-Speech with edge-tts
- LangGraph-based interview state management
- Adaptive follow-up questions
- Maximum 5 live questions
- Quit anytime
- Final evaluation based only on answered questions

## 🏗️ Architecture

```
                   Streamlit
                       │
                       ▼
                    FastAPI
                 ┌─────┴─────┐
                 │           │
                 ▼           ▼
          Question Gen.   Interview AI
                 │           │
                 ▼           ▼
              RAG       LangGraph
                 │       ┌───┼───┐
                 ▼       ▼   ▼   ▼
             ChromaDB  STT LLM TTS
                 │       │   │   │
                 ▼       └───┼───┘
           Gap Analysis      ▼
                        Final Report
```

## 🔄 RAG Workflow

```
Resume → Chunking → Embeddings → ChromaDB
JD     → Chunking → Embeddings → ChromaDB
                         ↓
                Focused Retrieval Queries
                         ↓
                   Relevant Context
                         ↓
                   Gap Analysis LLM
                         ↓
                  GapAnalysisResult
                         ↓
               Interview Question Set
```
The RAG layer retrieves resume information such as candidate details, education, skills, projects, experience, certifications, and technologies. It retrieves JD information such as title, required/preferred skills, experience, responsibilities, technologies, and other requirements.

## 🧠 LangGraph Interview Workflow

```
START
  ↓
route_action
  ├── start → first_question → speak_question
  ├── answer → transcribe → evaluate
  │                         ↓
  │                  check_completion
  │                  ├─ next → next_question → speak
  │                  └─ final → final_evaluation
  └── final → final_evaluation
```
The interview state tracks role, difficulty, question number, current/previous questions, conversation history, transcript, scores, and final report.

## 🛠️ Tech Stack

| Area | Technology |
|------|-----------|
| Frontend | Streamlit |
| Backend | FastAPI, Uvicorn |
| LLM | OpenRouter free models |
| AI Framework | LangChain, LangGraph |
| Vector DB | ChromaDB |
| Embeddings | `sentence-transformers/all-MiniLM-L6-v2` |
| STT | faster-whisper |
| TTS | edge-tts |
| Validation | Pydantic |
| PDF | pypdf |

## 📁 Project Structure

```
AI Interview Question Generator/
│
├── app.py
├── main.py
├── config.py
├── requirements.txt
├── resume_jd_rag.py
├── question_generator.py
├── gap_schema.py
├── interview_schema.py
├── validators.py
│
├── api/
│   ├── interview.py
│   └── ai_interview.py
│
├── interview_ai/
│   ├── state.py
│   ├── schemas.py
│   ├── prompts.py
│   └── graph.py
│
├── speech/
│   ├── stt.py
│   └── tts.py
│
└── chroma_db/
```

## 🔌 API Endpoints

### Question Generator

```
POST /api/interview/generate
```
Generates Resume-JD gap analysis and personalized questions.

### Interview with AI

```
POST /api/ai-interview/start
POST /api/ai-interview/answer
POST /api/ai-interview/quit
GET  /api/ai-interview/health
```
`/start` creates the session and first question. `/answer` processes candidate audio, STT, evaluation, next question, and TTS. `/quit` stops the interview and generates the final report.

## 📊 Final Evaluation
Example after two completed questions:

```
Questions Completed: 2
Average Score: 7.5/10

Strengths:
- Python fundamentals
- Clear technical explanation

Areas to Improve:
- System design
- Advanced RAG concepts

Recommendation:
Practice more scenario-based questions.
```

## ⚙️ Installation

### 1. Create environment

```
python -m venv myenv
```
Windows:

```
myenv\Scripts\activate
```

### 2. Install dependencies

```
pip install -r requirements.txt
```

### 3. Configure `.env`

```
OPENROUTER_API_KEY=your_openrouter_api_key
```

### 4. Start FastAPI

```
uvicorn main:app --reload
```
Docs:

```
http://127.0.0.1:8000/docs
```

### 5. Start Streamlit
In another terminal:

```
streamlit run app.py
```
Open:

```
http://localhost:8501
```

## ⚠️ Challenges

- **Free-model rate limits:** OpenRouter free providers can temporarily return 429 errors.
- **LLM output formatting:** Defensive parsing is needed when models return Markdown or tag-based output instead of strict JSON.
- **RAG quality:** Retrieval quality directly affects skill-gap analysis.
- **Speech recognition:** Noise and microphone quality can affect transcription.
- **Browser autoplay:** TTS playback can be affected by browser autoplay policies.
- **Interview state:** Multi-turn interviews require controlled state and routing, handled with LangGraph.

## 💼 Use Cases

- Personalized interview preparation
- Technical mock interviews
- Resume-JD skill-gap discovery
- Project-based interview practice
- Recruiter/JD-aligned question generation
- AI-powered interview training platforms

## 🔮 Future Improvements

- Authentication
- Interview history
- Candidate dashboard
- Score trends and analytics
- Resume-personalized live interviews
- Persistent LangGraph checkpoints
- Better answer-quality metrics
- Docker/cloud deployment
- RAG and interview evaluation benchmarks

## 🔐 Security

- Keep API keys in environment variables.
- Validate uploaded files and input sizes.
- Restrict API access in production.
- Avoid exposing internal exceptions to users.
- Protect resume and interview data.

## 🎯 Project Goal
The goal is to build an end-to-end AI interview platform that connects **document intelligence, semantic retrieval, skill-gap analysis, personalized question generation, stateful AI interviewing, voice interaction, and interview evaluation**.

```
Resume + JD
    ↓
Gap Analysis
    ↓
Personalized Questions
    ↓
AI Mock Interview
    ↓
Answer Evaluation
    ↓
Final Report
```

## 👨‍💻 Author
**Shubham Kain** — AI/ML • Generative AI • RAG • LangChain • LangGraph • FastAPI