import math
import re
from collections import Counter
from typing import List, Tuple
from langchain_core.documents import Document
from langchain_core.prompts import ChatPromptTemplate
from gap_schema import GapAnalysisResult

RAG_GAP_ANALYSIS_PROMPT = """
You are an expert AI Recruitment Analyst and Technical Hiring Specialist.

Your task is to perform a complete comparison between a candidate Resume
and a Job Description using ONLY the retrieved document context.

============================================================
RESUME CONTEXT
============================================================

{resume_context}

============================================================
JOB DESCRIPTION CONTEXT
============================================================

{job_description_context}

============================================================
CANDIDATE RESUME INFORMATION
============================================================

Extract, where available:

- Candidate Name
- Education
- Technical Skills
- Projects
- Work Experience
- Certifications
- Tools and Technologies

For Projects, identify where available:

- Project name
- Project purpose
- Technologies used
- Frameworks and libraries used
- Candidate contribution
- Technical skills demonstrated

For Work Experience, identify where available:

- Company
- Job title
- Duration
- Responsibilities
- Technologies used
- Achievements

============================================================
JOB DESCRIPTION INFORMATION
============================================================

Identify, where available:

- Job Title
- Required Skills
- Preferred Skills
- Experience Requirements
- Responsibilities
- Technologies
- Other Important Requirements

For Required Skills, prioritize requirements explicitly described as:

- Required
- Mandatory
- Must have
- Essential
- Minimum requirement

For Preferred Skills, prioritize:

- Preferred
- Nice to have
- Bonus
- Plus
- Desired
- Advantage

For Experience Requirements, identify:

- Years of experience
- Relevant technical experience
- Domain experience
- Specific project experience
- Leadership experience

For Responsibilities, identify the major duties and expected activities.

For Technologies, identify:

- Programming languages
- Frameworks
- Libraries
- Databases
- Cloud platforms
- AI/ML technologies
- APIs
- DevOps tools
- Development tools
- Infrastructure technologies

For Other Important Requirements, identify:

- Education
- Certifications
- Soft skills
- Communication requirements
- Domain knowledge
- Security/compliance requirements
- Location/work requirements
- Other explicit requirements

============================================================
COMPARISON
============================================================

Compare the candidate against the job requirements.

Classify required skills as:

MATCHED:
The resume explicitly demonstrates the required skill.

PARTIALLY_MATCHED:
The resume contains related knowledge, project exposure,
or indirect evidence but does not strongly demonstrate the requirement.

MISSING:
The requirement is not present in the available resume evidence.

UNKNOWN:
The retrieved resume context is insufficient to determine whether
the candidate has the skill.

Perform the same comparison for technologies where appropriate.

============================================================
SKILL GAP ANALYSIS
============================================================

Identify:

Critical Gaps:
Important required skills or requirements that are missing.

Moderate Gaps:
Required skills that are only partially demonstrated.

Minor Gaps:
Preferred or bonus skills that are missing.

============================================================
EXPERIENCE GAP
============================================================

Compare the experience required by the JD with the candidate's
demonstrated experience.

Never invent years of experience.

Use "Unknown" when the retrieved information is insufficient.

============================================================
RESPONSIBILITY GAP
============================================================

Compare the JD responsibilities with the candidate's projects
and work experience.

Classify responsibilities as:

- Supported
- Partially Supported
- Not Supported

============================================================
ADDITIONAL CANDIDATE SKILLS
============================================================

Identify relevant skills present in the resume but not specifically
required by the JD.

============================================================
INTERVIEW FOCUS AREAS
============================================================

Identify topics that should later be tested during the interview.

Prioritize:

1. Missing required skills
2. Partially matched required skills
3. Important JD technologies
4. Relevant candidate skills
5. Relevant candidate projects
6. Responsibilities with weak evidence

============================================================
STRICT RAG RULES
============================================================

1. Use ONLY the provided retrieved context.
2. Do not use outside information.
3. Never invent candidate skills.
4. Never invent projects.
5. Never invent work experience.
6. Never invent certifications.
7. Never invent technologies.
8. Never invent years of experience.
9. Do not treat lack of retrieved evidence as definite absence.
10. Use UNKNOWN when the retrieved information is insufficient.
11. Normalize equivalent skill names before comparison.
12. Give higher importance to required skills.
13. Give higher importance to demonstrated projects/work experience.
14. Do not duplicate skills.
15. Ignore irrelevant retrieved chunks.

Return the result using the provided structured output schema.
"""

# RESUME RETRIEVAL QUERIES
RESUME_QUERIES = [
    "candidate name education certifications academic background",
    "candidate technical skills programming languages frameworks libraries",
    "candidate projects project technologies responsibilities contributions",
    "candidate work experience companies roles responsibilities achievements",
    "candidate tools technologies databases cloud platforms AI ML",
]

# JOB DESCRIPTION RETRIEVAL QUERIES
JD_QUERIES = [
    "job title required skills mandatory qualifications",
    "job preferred skills nice to have bonus skills",
    "job experience requirements years experience domain experience",
    "job responsibilities duties role expectations",
    "job technologies tools frameworks databases cloud platforms",
    "job education certifications soft skills other requirements",
]


class FastBM25Store:
    """
    Lightweight, high-performance in-memory BM25 / TF-IDF text search store.
    - Zero external heavy dependencies (no PyTorch, no HuggingFace downloads).
    - Sub-millisecond execution time.
    - Uses ~0 extra RAM.
    """

    def __init__(self):
        self.docs: List[Document] = []
        self.doc_freqs = Counter()
        self.total_docs = 0

    @staticmethod
    def _tokenize(text: str) -> List[str]:
        return re.findall(r"\w+", text.lower())

    def add_documents(self, documents: List[Document]) -> None:
        self.docs.extend(documents)
        self.total_docs = len(self.docs)
        self.doc_freqs = Counter()
        for doc in self.docs:
            tokens = set(self._tokenize(doc.page_content))
            for t in tokens:
                self.doc_freqs[t] += 1

    def similarity_search(self, query: str, k: int = 3) -> List[Document]:
        if not self.docs:
            return []
        q_tokens = self._tokenize(query)
        scores = []
        for i, doc in enumerate(self.docs):
            doc_tokens = self._tokenize(doc.page_content)
            doc_counts = Counter(doc_tokens)
            score = 0.0
            for qt in q_tokens:
                if qt in doc_counts:
                    tf = doc_counts[qt] / (len(doc_tokens) or 1)
                    idf = math.log((self.total_docs + 1) / (self.doc_freqs[qt] + 1)) + 1
                    score += tf * idf
            scores.append((score, i))
        scores.sort(key=lambda x: x[0], reverse=True)
        return [self.docs[i] for score, i in scores[:k]]


class ResumeJDRAG:
    """
    High-performance, lightweight Resume-JD RAG pipeline.
    Uses FastBM25Store for instant, zero-RAM in-memory text retrieval.
    """

    def __init__(
        self,
        llm,
        resume_k: int = 3,
        jd_k: int = 3,
        persist_directory: str = "./chroma_db",
    ):
        self.llm = llm
        self.resume_k = resume_k
        self.jd_k = jd_k

        # STRUCTURED LLM — builds the LangChain chain
        self.structured_llm = self.llm.with_structured_output(
            GapAnalysisResult
        )
        self.prompt = ChatPromptTemplate.from_template(
            RAG_GAP_ANALYSIS_PROMPT
        )
        self.chain = self.prompt | self.structured_llm

        # Fast in-memory stores
        self.resume_store = FastBM25Store()
        self.jd_store = FastBM25Store()

    # ── PUBLIC API ─────────────────────────────────────────────────────────────

    def clear_collections(self) -> None:
        """Reset stores before processing a new request."""
        self.resume_store = FastBM25Store()
        self.jd_store = FastBM25Store()

    def add_resume(
        self,
        resume_text: str,
        candidate_id: str = "default_candidate",
    ) -> None:
        if not resume_text.strip():
            raise ValueError("Resume text cannot be empty.")
        chunks = self._create_chunks(
            text=resume_text,
            source="resume",
            document_id=candidate_id,
        )
        if not chunks:
            raise ValueError("No resume chunks were created.")
        self.resume_store.add_documents(chunks)

    def add_job_description(
        self,
        job_description: str,
        job_id: str = "default_job",
    ) -> None:
        if not job_description.strip():
            raise ValueError("Job description cannot be empty.")
        chunks = self._create_chunks(
            text=job_description,
            source="job_description",
            document_id=job_id,
        )
        if not chunks:
            raise ValueError("No JD chunks were created.")
        self.jd_store.add_documents(chunks)

    def analyze(self) -> GapAnalysisResult:
        resume_context, jd_context = self.retrieve()
        result = self.chain.invoke(
            {
                "resume_context": resume_context,
                "job_description_context": jd_context,
            }
        )
        return result

    # ── RETRIEVAL ──────────────────────────────────────────────────────────────

    def retrieve(self) -> Tuple[str, str]:
        resume_docs: List[Document] = []
        jd_docs: List[Document] = []

        for query in RESUME_QUERIES:
            resume_docs.extend(
                self.resume_store.similarity_search(query, k=self.resume_k)
            )
        for query in JD_QUERIES:
            jd_docs.extend(
                self.jd_store.similarity_search(query, k=self.jd_k)
            )

        resume_docs = self._deduplicate(resume_docs)[:20]
        jd_docs = self._deduplicate(jd_docs)[:20]

        return (
            self._format_documents(resume_docs),
            self._format_documents(jd_docs),
        )

    # ── HELPERS ────────────────────────────────────────────────────────────────

    @staticmethod
    def _create_chunks(
        text: str,
        source: str,
        document_id: str,
        chunk_size: int = 1000,
        chunk_overlap: int = 150,
    ) -> List[Document]:
        text = text.strip()
        if not text:
            return []
        chunks: List[Document] = []
        start = 0
        chunk_id = 0
        length = len(text)
        while start < length:
            end = min(start + chunk_size, length)
            chunk_text = text[start:end].strip()
            if chunk_text:
                chunks.append(
                    Document(
                        page_content=chunk_text,
                        metadata={
                            "source": source,
                            "document_id": document_id,
                            "chunk_id": chunk_id,
                        },
                    )
                )
                chunk_id += 1
            if end >= length:
                break
            start = max(0, end - chunk_overlap)
        return chunks

    @staticmethod
    def _deduplicate(docs: List[Document]) -> List[Document]:
        seen: set = set()
        unique: List[Document] = []
        for doc in docs:
            content = doc.page_content.strip()
            if content and content not in seen:
                seen.add(content)
                unique.append(doc)
        return unique

    @staticmethod
    def _format_documents(docs: List[Document]) -> str:
        if not docs:
            return "No relevant information was retrieved."
        parts = []
        for i, doc in enumerate(docs, start=1):
            parts.append(
                f"--- Retrieved Chunk {i} ---\n"
                f"{doc.page_content}\n"
                f"Source Metadata: {doc.metadata}\n"
            )
        return "\n".join(parts)