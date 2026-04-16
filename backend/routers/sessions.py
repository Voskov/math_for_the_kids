from datetime import datetime
from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel
from sqlalchemy.orm import Session as DBSession
from backend.database import get_db
from backend.models import Kid, Session, SessionProblem

router = APIRouter(prefix="/sessions", tags=["sessions"])

PROBLEMS_PER_SESSION = 10


class StartSessionIn(BaseModel):
    kid_id: int
    topic: str = "arithmetic"


class SessionOut(BaseModel):
    id: int
    kid_id: int
    topic: str
    problem_count: int

    model_config = {"from_attributes": True}


class SummaryProblemOut(BaseModel):
    question_text: str
    correct_answer: str
    kid_answer: str | None
    is_correct: bool | None
    time_taken_s: float | None
    difficulty_at_time: float


class SessionSummaryOut(BaseModel):
    session_id: int
    kid_name: str
    topic: str
    total: int
    correct: int
    accuracy_pct: float
    problems: list[SummaryProblemOut]


@router.post("/start", response_model=SessionOut)
def start_session(body: StartSessionIn, db: DBSession = Depends(get_db)):
    kid = db.get(Kid, body.kid_id)
    if not kid:
        raise HTTPException(status_code=404, detail="Kid not found")
    session = Session(
        kid_id=body.kid_id,
        topic=body.topic,
        problem_count=PROBLEMS_PER_SESSION,
    )
    db.add(session)
    db.commit()
    db.refresh(session)
    return session


@router.get("/{session_id}/summary", response_model=SessionSummaryOut)
def get_summary(session_id: int, db: DBSession = Depends(get_db)):
    session = db.get(Session, session_id)
    if not session:
        raise HTTPException(status_code=404, detail="Session not found")
    problems = (
        db.query(SessionProblem)
        .filter(SessionProblem.session_id == session_id)
        .order_by(SessionProblem.id)
        .all()
    )
    answered = [p for p in problems if p.is_correct is not None]
    correct = sum(1 for p in answered if p.is_correct)
    total = len(answered)
    return SessionSummaryOut(
        session_id=session_id,
        kid_name=session.kid.name,
        topic=session.topic,
        total=total,
        correct=correct,
        accuracy_pct=round(correct / total * 100, 1) if total else 0.0,
        problems=[
            SummaryProblemOut(
                question_text=p.question_text,
                correct_answer=p.correct_answer,
                kid_answer=p.kid_answer,
                is_correct=p.is_correct,
                time_taken_s=p.time_taken_s,
                difficulty_at_time=p.difficulty_at_time,
            )
            for p in problems
        ],
    )
