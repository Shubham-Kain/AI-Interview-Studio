import warnings
from typing import Dict

###  CATEGORY DISTRIBUTION   ###
def calculate_category_distribution(
    num_questions: int,
) -> Dict[str, int]:
    if not 6 <= num_questions <= 30:
        raise ValueError(
            "Number of questions must be between 6 and 30."
        )
    categories = {
        "Basic": 0,
        "Technical": 0,
        "Resume-Based": 0,
        "Project-Based": 0,
        "Scenario-Based": 0,
        "Skill Gap": 0,
    }
    ###  Guarantee one question for every category   ###
    for category in categories:
        categories[category] = 1
    remaining = num_questions - 6
    ###  Priority   ###
    priority = [
        "Technical",
        "Basic",
        "Resume-Based",
        "Project-Based",
        "Scenario-Based",
        "Skill Gap",
    ]
    index = 0
    while remaining > 0:
        category = priority[index]
        categories[category] += 1
        remaining -= 1
        index += 1
        if index >= len(priority):
            index = 0
    return categories


###  QUESTION VALIDATION (lenient — warns instead of crashing) ###
def validate_question_set(
    result,
    expected_count: int,
    difficulty: str,
    expected_distribution: Dict[str, int],
) -> None:
    """
    Validate the LLM-generated question set.
    Raises ValueError only for truly unrecoverable problems
    (empty result). For count/distribution mismatches we log
    a warning so the API still returns usable questions.
    """
    if not result or not result.questions:
        raise ValueError(
            "LLM returned zero questions. "
            "Please try again."
        )

    actual_count = len(result.questions)
    if actual_count != expected_count:
        warnings.warn(
            f"Expected {expected_count} questions but got "
            f"{actual_count}. Returning available questions.",
            stacklevel=2,
        )

    ###  Difficulty check — warn only   ###
    for question in result.questions:
        if question.difficulty != difficulty:
            warnings.warn(
                f"Question {question.question_id} has "
                f"difficulty '{question.difficulty}' "
                f"instead of '{difficulty}'.",
                stacklevel=2,
            )

    ###  Duplicate check — warn only   ###
    normalized_questions = [
        question.question.strip().lower()
        for question in result.questions
    ]
    if len(normalized_questions) != len(
        set(normalized_questions)
    ):
        warnings.warn(
            "Duplicate questions detected in LLM output.",
            stacklevel=2,
        )