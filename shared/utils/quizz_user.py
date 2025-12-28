from core.db import repository
import json

def _normalize_quiz(quiz: dict) -> dict:
    if not quiz:
        return quiz

    quiz["daily_challenges"] = json.loads(quiz["daily_challenges"])
    quiz["stoic_paths"] = (
        json.loads(quiz["stoic_paths"])
        if quiz.get("stoic_paths")
        else []
    )

    return quiz



def get_quizz_user_by_id(user_id: str):
    if not user_id:
        raise ValueError("user_id es requerido")

    query = """
        SELECT *
        FROM user_quiz_responses
        WHERE user_id = %s
        LIMIT 1
    """

    quiz = repository.fetch_one(query, (user_id,))
    return _normalize_quiz(quiz)
