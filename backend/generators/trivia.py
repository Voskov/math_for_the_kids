"""Trivia generator backed by BankQuestion table.

Difficulty rules:
  Bank questions are tagged at seed time:
    direct format → difficulty 5  (easy: name given, asks about field)
    clue format   → difficulty 12 (harder: description → guess person)
  Generator picks from a window around effective difficulty.
  At difficulty >= 18, distractors are swapped for cross-bank correct_answers
  (other famous names) — much harder than the canned distractors.

No-repeat rule:
  Excludes correct_answers the kid already saw in any past trivia session.
  Falls back to the full pool if exhausted.
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
            .where(SessionModel.kid_id == kid_id, SessionModel.topic == "trivia")
        ).scalars().all()
    )

    in_window = db.execute(
        select(BankQuestion).where(
            BankQuestion.topic == "trivia",
            BankQuestion.difficulty.between(lo, hi),
        )
    ).scalars().all()

    fresh = [q for q in in_window if q.correct_answer not in seen]
    pool = fresh or in_window
    if not pool:
        pool = db.execute(
            select(BankQuestion).where(BankQuestion.topic == "trivia")
        ).scalars().all()
    if not pool:
        raise RuntimeError("Trivia bank empty — seed not run?")

    q = random.choice(pool)
    distractors = json.loads(q.distractors)

    if int(difficulty) >= 18:
        cross = db.execute(
            select(BankQuestion.correct_answer).where(
                BankQuestion.topic == "trivia",
                BankQuestion.correct_answer != q.correct_answer,
            )
        ).scalars().all()
        if len(cross) >= 3:
            distractors = random.sample(cross, 3)

    choices = [q.correct_answer] + distractors
    random.shuffle(choices)
    return {
        "question": q.question,
        "answer": q.correct_answer,
        "choices": choices,
        "wiki_url": q.wiki_url,
    }
