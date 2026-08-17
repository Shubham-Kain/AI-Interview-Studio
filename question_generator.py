from langchain_core.prompts import ChatPromptTemplate
from interview_prompt import INTERVIEW_QUESTION_PROMPT
from gap_schema import GapAnalysisResult
from interview_schema import InterviewQuestionSet
from validators import (
    calculate_category_distribution,
    validate_question_set,
)
class InterviewQuestionGenerator:
    def __init__(
        self,
        llm,
    ):
        ###  STRUCTURED OUTPUT   ###
        self.structured_llm = (
            llm.with_structured_output(
                InterviewQuestionSet
            )
        )
        ###  PROMPT   ###
        self.prompt = ChatPromptTemplate.from_template(
            INTERVIEW_QUESTION_PROMPT
        )
        self.chain = self.prompt | self.structured_llm
    ###  GENERATE QUESTIONS   ###
    def generate(
        self,
        rag_result: GapAnalysisResult,
        job_title: str,
        difficulty: str,
        num_questions: int,
    ) -> InterviewQuestionSet:
        ###  VALIDATE DIFFICULTY   ###
        allowed_difficulties = {
            "Easy",
            "Medium",
            "Hard",
        }
        if difficulty not in allowed_difficulties:
            raise ValueError(
                "Difficulty must be Easy, Medium, or Hard."
            )
        ###  VALIDATE QUESTION COUNT   ###
        if not 6 <= num_questions <= 30:
            raise ValueError(
                "Number of questions must be between 6 and 30."
            )
        ### CATEGORY DISTRIBUTION   ###
        category_distribution = (
            calculate_category_distribution(
                num_questions
            )
        )
        ###  USE RAG JOB TITLE WHEN AVAILABLE   ###
        final_job_title = (
            rag_result.job.job_title.strip()
            if rag_result.job.job_title
            else job_title.strip()
        )
        if not final_job_title:
            final_job_title = "Technical Role"
        ###  RAG RESULT   ###
        rag_json = rag_result.model_dump_json(
            indent=2
        )
        ###  GENERATE   ###
        result = self.chain.invoke(
            {
                "job_title": final_job_title,
                "difficulty": difficulty,
                "num_questions": num_questions,
                "category_distribution": (
                    category_distribution
                ),
                "rag_result": rag_json,
            }
        )
        ###  VALIDAT  ###
        validate_question_set(
            result=result,
            expected_count=num_questions,
            difficulty=difficulty,
            expected_distribution=category_distribution,
        )
        return result