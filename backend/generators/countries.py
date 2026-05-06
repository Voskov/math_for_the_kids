"""Countries & Capitals generator backed by BankQuestion table.

Difficulty:
  country_to_capital → 5  (easier)
  capital_to_country → 8  (harder)

No-repeat rule: excludes correct_answers kid already saw in any past countries session.
Falls back to full pool if exhausted.
"""
import json
import random
from sqlalchemy import select
from sqlalchemy.orm import Session as DBSession
from backend.models import BankQuestion, Session as SessionModel, SessionProblem


def _difficulty_window(d: float) -> tuple[int, int]:
    di = int(d)
    return max(1, di - 3), min(20, di + 3)


def generate(difficulty: float, db: DBSession, kid_id: int) -> dict:
    lo, hi = _difficulty_window(difficulty)

    seen = set(
        db.execute(
            select(SessionProblem.correct_answer)
            .join(SessionModel, SessionModel.id == SessionProblem.session_id)
            .where(SessionModel.kid_id == kid_id, SessionModel.topic == "countries")
        ).scalars().all()
    )

    in_window = db.execute(
        select(BankQuestion).where(
            BankQuestion.topic == "countries",
            BankQuestion.difficulty.between(lo, hi),
        )
    ).scalars().all()

    fresh = [q for q in in_window if q.correct_answer not in seen]
    pool = fresh or in_window
    if not pool:
        pool = db.execute(
            select(BankQuestion).where(BankQuestion.topic == "countries")
        ).scalars().all()
    if not pool:
        raise RuntimeError("Countries bank empty — seed not run?")

    q = random.choice(pool)
    distractors = json.loads(q.distractors)
    choices = [q.correct_answer] + distractors
    random.shuffle(choices)
    return {
        "question": q.question,
        "answer": q.correct_answer,
        "choices": choices,
    }
