import random
from datetime import datetime
from fractions import Fraction
from loguru import logger
from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel
from sqlalchemy.orm import Session as DBSession
from backend.database import get_db
from backend.models import KidTopicLevel, Session, SessionProblem
from backend.adaptive import MAX_DIFFICULTY, MIN_DIFFICULTY, update_level
from backend import generators

router = APIRouter(prefix="/problems", tags=["problems"])


class NextProblemOut(BaseModel):
    problem_id: int
    question: str
    session_problem_number: int
    total_problems: int
    difficulty: float
    done: bool = False
    choices: list[str] | None = None
    tts_word: str | None = None
    wiki_url: str | None = None


class SubmitAnswerIn(BaseModel):
    problem_id: int
    kid_answer: str
    time_taken_s: float


class SubmitAnswerOut(BaseModel):
    is_correct: bool
    correct_answer: str
    new_difficulty: float
    session_done: bool
    session_id: int


def _get_generator(topic: str):
    if topic == "arithmetic":
        from backend.generators import arithmetic
        return arithmetic.generate
    if topic == "sequences":
        from backend.generators import sequences
        return sequences.generate
    if topic == "word_problems":
        from backend.generators import word_problems
        return word_problems.generate
    if topic == "fractions":
        from backend.generators import fractions
        return fractions.generate
    if topic == "hebrew_letters":
        from backend.generators import hebrew_letters
        return hebrew_letters.generate
    if topic == "english_letters":
        from backend.generators import english_letters
        return english_letters.generate
    if topic == "clock":
        from backend.generators import clock
        return clock.generate
    if topic == "powers":
        from backend.generators import powers
        return powers.generate
    if topic == "trivia":
        from backend.generators import trivia
        return trivia.generate
    if topic == "countries":
        from backend.generators import countries
        return countries.generate
    raise ValueError(f"Unknown topic: {topic}")


def _answers_match(kid: str, correct: str) -> bool:
    if kid == correct:
        return True
    try:
        return Fraction(kid) == Fraction(correct)
    except (ValueError, ZeroDivisionError):
        return False


_TOPIC_START_DIFFICULTY: dict[str, float] = {
    "hebrew_letters": 1.0,
    "english_letters": 1.0,
    "clock": 1.0,
    "trivia": 5.0,
    "countries": 5.0,
}


def _pick_effective_difficulty(base: float) -> float:
    """Mix levels: 70% at base, 20% at base-1, 10% at base+1 (clamped)."""
    roll = random.random()
    if roll < 0.70:
        return base
    if roll < 0.90:
        return max(MIN_DIFFICULTY, base - 1.0)
    return min(MAX_DIFFICULTY, base + 1.0)


def _get_or_create_level(db: DBSession, kid_id: int, topic: str) -> KidTopicLevel:
    level = (
        db.query(KidTopicLevel)
        .filter(KidTopicLevel.kid_id == kid_id, KidTopicLevel.topic == topic)
        .first()
    )
    if not level:
        default = _TOPIC_START_DIFFICULTY.get(topic, 5.0)
        level = KidTopicLevel(kid_id=kid_id, topic=topic, difficulty_level=default, score_accumulator=0.0)
        db.add(level)
        db.flush()
    return level


@router.get("/next/{session_id}", response_model=NextProblemOut)
def next_problem(session_id: int, db: DBSession = Depends(get_db)):
    session = db.get(Session, session_id)
    if not session:
        raise HTTPException(status_code=404, detail="Session not found")

    answered_count = (
        db.query(SessionProblem)
        .filter(SessionProblem.session_id == session_id, SessionProblem.is_correct.isnot(None))
        .count()
    )

    if answered_count >= session.problem_count:
        # Session complete — close it if not already
        if not session.ended_at:
            session.ended_at = datetime.utcnow()
            db.commit()
        return NextProblemOut(
            problem_id=-1,
            question="",
            session_problem_number=answered_count,
            total_problems=session.problem_count,
            difficulty=0,
            done=True,
        )

    level = _get_or_create_level(db, session.kid_id, session.topic)
    gen = _get_generator(session.topic)

    last_question = (
        db.query(SessionProblem.question_text)
        .filter(SessionProblem.session_id == session_id)
        .order_by(SessionProblem.id.desc())
        .limit(1)
        .scalar()
    )

    for _ in range(5):
        effective_diff = _pick_effective_difficulty(level.difficulty_level)
        if session.topic in ("trivia", "countries"):
            problem_data = gen(effective_diff, db=db, kid_id=session.kid_id)
        else:
            problem_data = gen(effective_diff)
        if problem_data["question"] != last_question:
            break

    sp = SessionProblem(
        session_id=session_id,
        question_text=problem_data["question"],
        correct_answer=problem_data["answer"],
        tts_word=problem_data.get("tts_word"),
        difficulty_at_time=effective_diff,
        asked_at=datetime.utcnow(),
    )
    db.add(sp)
    db.commit()
    db.refresh(sp)

    return NextProblemOut(
        problem_id=sp.id,
        question=sp.question_text,
        session_problem_number=answered_count + 1,
        total_problems=session.problem_count,
        difficulty=effective_diff,
        choices=problem_data.get("choices"),
        tts_word=sp.tts_word,
        wiki_url=problem_data.get("wiki_url"),
    )


@router.post("/submit", response_model=SubmitAnswerOut)
def submit_answer(body: SubmitAnswerIn, db: DBSession = Depends(get_db)):
    sp = db.get(SessionProblem, body.problem_id)
    if not sp:
        raise HTTPException(status_code=404, detail="Problem not found")
    if sp.is_correct is not None:
        raise HTTPException(status_code=400, detail="Already answered")

    kid_answer = body.kid_answer.strip()
    is_correct = _answers_match(kid_answer, sp.correct_answer)
    sp.kid_answer = kid_answer
    sp.is_correct = is_correct
    sp.time_taken_s = body.time_taken_s
    sp.answered_at = datetime.utcnow()

    session = db.get(Session, sp.session_id)
    level = _get_or_create_level(db, session.kid_id, session.topic)
    new_diff, new_acc = update_level(
        level.difficulty_level,
        level.score_accumulator,
        is_correct,
        body.time_taken_s,
        problem_level=sp.difficulty_at_time,
    )

    logger.info(
        f"submit_answer: kid_id={session.kid_id}, topic={session.topic}, "
        f"level {level.difficulty_level} → {new_diff}, "
        f"acc {level.score_accumulator:.1f} → {new_acc:.1f}, "
        f"correct={is_correct}, time={body.time_taken_s}s"
    )

    level.difficulty_level = new_diff
    level.score_accumulator = new_acc

    answered_count = (
        db.query(SessionProblem)
        .filter(SessionProblem.session_id == sp.session_id, SessionProblem.is_correct.isnot(None))
        .count()
    )
    session_done = answered_count >= session.problem_count
    if session_done and not session.ended_at:
        session.ended_at = datetime.utcnow()

    db.commit()

    return SubmitAnswerOut(
        is_correct=is_correct,
        correct_answer=sp.correct_answer,
        new_difficulty=new_diff,
        session_done=session_done,
        session_id=sp.session_id,
    )
