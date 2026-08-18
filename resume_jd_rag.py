from typing import List, Tuple
from langchain_core.documents import Document
from langchain_core.prompts import ChatPromptTemplate
from langchain_huggingface import HuggingFaceEmbeddings
from langchain_chroma import Chroma
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
class ResumeJDRAG:
    def __init__(
        self,
        llm,
        persist_directory: str = "./chroma_db",
        resume_k: int = 2,
        jd_k: int = 2,
    ):
        self.llm = llm
        self.persist_directory = persist_directory
        self.resume_k = resume_k
        self.jd_k = jd_k
        self.embedding = None
        # CREATE VECTOR STORES
        self._create_vectorstores()

    def _get_embedding(self):
        if self.embedding is None:
            self.embedding = HuggingFaceEmbeddings(
                model_name="sentence-transformers/all-MiniLM-L6-v2"
            )
        return self.embedding
        # STRUCTURED LLM
        self.structured_llm = (
            self.llm.with_structured_output(
                GapAnalysisResult
            )
        )
        # PROMPT
        self.prompt = ChatPromptTemplate.from_template(
            RAG_GAP_ANALYSIS_PROMPT
        )
        self.chain = self.prompt | self.structured_llm
    # CREATE / RECREATE VECTOR STORES
    def _create_vectorstores(self):
        embedding = self._get_embedding()
        self.resume_vectorstore = Chroma(
            collection_name="resume_collection",
            embedding_function=embedding,
            persist_directory=(
                f"{self.persist_directory}/resume"
            ),
        )
        self.jd_vectorstore = Chroma(
            collection_name="jd_collection",
            embedding_function=embedding,
            persist_directory=(
                f"{self.persist_directory}/job_description"
            ),
        )
        # RETRIEVERS
        self.resume_retriever = (
            self.resume_vectorstore.as_retriever(
                search_type="similarity",
                search_kwargs={
                    "k": self.resume_k
                },
            )
        )
        self.jd_retriever = (
            self.jd_vectorstore.as_retriever(
                search_type="similarity",
                search_kwargs={
                    "k": self.jd_k
                },
            )
        )
    # CHANGE 3:
    # CLEAR OLD RESUME + JD COLLECTIONS
    def clear_collections(self) -> None:
        try:
            self.resume_vectorstore.delete_collection()
        except Exception:
            pass
        try:
            self.jd_vectorstore.delete_collection()
        except Exception:
            pass
        self._create_vectorstores()
    # ADD RESUME
    def add_resume(
        self,
        resume_text: str,
        candidate_id: str = "default_candidate",
    ) -> None:
        if not resume_text.strip():
            raise ValueError(
                "Resume text cannot be empty."
            )
        chunks = self._create_chunks(
            text=resume_text,
            source="resume",
            document_id=candidate_id,
        )
        if not chunks:
            raise ValueError(
                "No resume chunks were created."
            )
        ids = [
            f"resume_{candidate_id}_{index}"
            for index in range(len(chunks))
        ]
        self.resume_vectorstore.add_documents(
            documents=chunks,
            ids=ids,
        )
    # ADD JOB DESCRIPTION
    def add_job_description(
        self,
        job_description: str,
        job_id: str = "default_job",
    ) -> None:
        if not job_description.strip():
            raise ValueError(
                "Job description cannot be empty."
            )
        chunks = self._create_chunks(
            text=job_description,
            source="job_description",
            document_id=job_id,
        )
        if not chunks:
            raise ValueError(
                "No JD chunks were created."
            )
        ids = [
            f"jd_{job_id}_{index}"
            for index in range(len(chunks))
        ]
        self.jd_vectorstore.add_documents(
            documents=chunks,
            ids=ids,
        )

    # CHUNKING

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
        chunks = []
        start = 0
        chunk_id = 0
        text_length = len(text)
        while start < text_length:
            end = min(
                start + chunk_size,
                text_length,
            )
            chunk_text = text[
                start:end
            ].strip()
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
            if end >= text_length:
                break
            start = max(
                0,
                end - chunk_overlap,
            )
        return chunks
    # RETRIEVE RESUME + JD
    def retrieve(
        self,
    ) -> Tuple[str, str]:
        resume_documents = []
        jd_documents = []
        # RESUME RETRIEVAL
        for query in RESUME_QUERIES:
            docs = self.resume_retriever.invoke(
                query
            )
            resume_documents.extend(docs)
        # JD RETRIEVAL
        for query in JD_QUERIES:
            docs = self.jd_retriever.invoke(
                query
            )
            jd_documents.extend(docs)
        # REMOVE DUPLICATES
        resume_documents = self._remove_duplicates(
            resume_documents
        )
        jd_documents = self._remove_duplicates(
            jd_documents
        )
        # CHANGE 1:
        # LIMIT CONTEXT SIZE
        resume_documents = resume_documents[:20]
        jd_documents = jd_documents[:20]
        # FORMAT CONTEXT
        resume_context = self._format_documents(
            resume_documents
        )
        jd_context = self._format_documents(
            jd_documents
        )
        return (
            resume_context,
            jd_context,
        )

    # REMOVE DUPLICATES

    @staticmethod
    def _remove_duplicates(
        documents: List[Document],
    ) -> List[Document]:
        unique_documents = []
        seen = set()
        for doc in documents:
            content = doc.page_content.strip()
            if not content:
                continue
            if content in seen:
                continue
            seen.add(content)
            unique_documents.append(doc)
        return unique_documents
    
    # FORMAT DOCUMENTS
    
    @staticmethod
    def _format_documents(
        documents: List[Document],
    ) -> str:
        if not documents:
            return (
                "No relevant information "
                "was retrieved."
            )
        formatted_chunks = []
        for index, doc in enumerate(
            documents,
            start=1,
        ):
            formatted_chunks.append(
                f"""
--- Retrieved Chunk {index} ---
{doc.page_content}
Source Metadata:
{doc.metadata}
"""
            )
        return "\n".join(
            formatted_chunks
        )

    # GAP ANALYSIS

    def analyze(self) -> GapAnalysisResult:
        resume_context, jd_context = self.retrieve()
        result = self.chain.invoke(
            {
                "resume_context": resume_context,
                "job_description_context": jd_context,
            }
        )
        return result