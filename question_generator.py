import json
import re
from gap_schema import GapAnalysisResult
from interview_schema import InterviewQuestionSet
from interview_prompt import INTERVIEW_QUESTION_PROMPT
from validators import (
    calculate_category_distribution,
    validate_question_set,
)


class InterviewQuestionGenerator:
    def __init__(self, llm):
        self.llm = llm

    @staticmethod
    def _extract_json(raw_text: str) -> dict:
        """Extract and parse JSON from model response text cleanly."""
        text = raw_text.strip()
        # Remove markdown code fences if present
        match = re.search(r"```(?:json)?\s*([\s\S]*?)\s*```", text)
        if match:
            text = match.group(1).strip()
        # Extract from first { to last }
        start = text.find("{")
        end = text.rfind("}")
        if start != -1 and end != -1:
            text = text[start : end + 1]
        return json.loads(text)

    def generate(
        self,
        rag_result: GapAnalysisResult,
        job_title: str,
        difficulty: str,
        num_questions: int,
    ) -> InterviewQuestionSet:
        # Validate inputs
        allowed_difficulties = {"Easy", "Medium", "Hard"}
        if difficulty not in allowed_difficulties:
            raise ValueError("Difficulty must be Easy, Medium, or Hard.")
        if not 6 <= num_questions <= 30:
            raise ValueError("Number of questions must be between 6 and 30.")

        category_distribution = calculate_category_distribution(num_questions)
        final_job_title = (
            rag_result.job.job_title.strip()
            if rag_result.job.job_title
            else job_title.strip()
        ) or "Technical Role"

        rag_json = rag_result.model_dump_json(indent=2)

        prompt = f"""{INTERVIEW_QUESTION_PROMPT.format(
            job_title=final_job_title,
            difficulty=difficulty,
            num_questions=num_questions,
            category_distribution=category_distribution,
            rag_result=rag_json,
        )}

============================================================
REQUIRED JSON OUTPUT FORMAT
============================================================
Return ONLY a valid JSON object matching this exact schema, with NO markdown code fences and NO explanatory text:
{{
  "job_title": "{final_job_title}",
  "total_questions": {num_questions},
  "category_distribution": {json.dumps(category_distribution)},
  "questions": [
    {{
      "question_id": 1,
      "category": "Basic",
      "difficulty": "{difficulty}",
      "question": "Question text here...",
      "expected_answer": "Expected answer here...",
      "key_points": ["point 1", "point 2"]
    }}
  ]
}}
"""
        response = self.llm.invoke(prompt)
        raw_text = (
            response.content if hasattr(response, "content") else str(response)
        )
        if isinstance(raw_text, list):
            raw_text = " ".join(
                str(c.get("text", c) if isinstance(c, dict) else c)
                for c in raw_text
            )

        data = self._extract_json(raw_text)
        result = InterviewQuestionSet.model_validate(data)

        validate_question_set(
            result=result,
            expected_count=num_questions,
            difficulty=difficulty,
            expected_distribution=category_distribution,
        )
        return result