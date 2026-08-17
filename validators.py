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
###  QUESTION VALIDATION   ###
def validate_question_set(
    result,
    expected_count: int,
    difficulty: str,
    expected_distribution: Dict[str, int],
) -> None:
    ###  Number validation   ###
    if len(result.questions) != expected_count:
        raise ValueError(
            f"Expected {expected_count} questions, "
            f"got {len(result.questions)}."
        )
    ###  Difficulty validation   ###
    for question in result.questions:
        if question.difficulty != difficulty:
            raise ValueError(
                f"Question {question.question_id} "
                f"has invalid difficulty."
            )
    ###  Question ID validation   ###
    for index, question in enumerate(
        result.questions,
        start=1,
    ):
        if question.question_id != index:
            raise ValueError(
                f"Expected question ID {index}, "
                f"got {question.question_id}."
            )
    ###  Category count validation   ###
    actual_distribution = {}
    for question in result.questions:
        actual_distribution[
            question.category
        ] = (
            actual_distribution.get(
                question.category,
                0,
            )
            + 1
        )
    if actual_distribution != expected_distribution:
        raise ValueError(
            "Generated category distribution does not "
            "match the required distribution."
        )
    ###  Duplicate validation   ###
    normalized_questions = [
        question.question.strip().lower()
        for question in result.questions
    ]
    if len(normalized_questions) != len(
        set(normalized_questions)
    ):
        raise ValueError(
            "Duplicate questions detected."
        )