from datetime import datetime
from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel
from sqlalchemy import case, func
from sqlalchemy.orm import Session as DBSession
from backend.database import get_db
from backend.models import Kid, KidTopicLevel, Session, SessionProblem

router = APIRouter(prefix="/admin", tags=["admin"])


class TopicLevelOut(BaseModel):
    topic: str
    difficulty_level: float


class OverviewKidOut(BaseModel):
    kid_id: int
    name: str
    avatar_emoji: str
    starting_grade: str
    levels: list[TopicLevelOut]
    total_sessions: int
    total_problems_answered: int
    overall_accuracy_pct: float


class SessionRowOut(BaseModel):
    session_id: int
    topic: str
    started_at: datetime
    ended_at: datetime | None
    duration_s: float | None
    total: int
    correct: int
    accuracy_pct: float


class ActivityRowOut(SessionRowOut):
    kid_id: int
    kid_name: str
    avatar_emoji: str


class ProblemHistoryPointOut(BaseModel):
    asked_at: datetime
    difficulty_at_time: float
    is_correct: bool
    time_taken_s: float | None
    session_id: int


def _accuracy(correct: int, total: int) -> float:
    return round(correct / total * 100, 1) if total else 0.0


@router.get("/overview", response_model=list[OverviewKidOut])
def overview(db: DBSession = Depends(get_db)):
    kids = db.query(Kid).all()
    out: list[OverviewKidOut] = []
    for kid in kids:
        total_sessions = (
            db.query(func.count(Session.id))
            .filter(Session.kid_id == kid.id, Session.ended_at.isnot(None))
            .scalar()
            or 0
        )
        answered, correct = (
            db.query(
                func.count(SessionProblem.id),
                func.sum(case((SessionProblem.is_correct.is_(True), 1), else_=0)),
            )
            .join(Session, Session.id == SessionProblem.session_id)
            .filter(Session.kid_id == kid.id, SessionProblem.is_correct.isnot(None))
            .one()
        )
        answered = answered or 0
        correct = int(correct or 0)
        out.append(
            OverviewKidOut(
                kid_id=kid.id,
                name=kid.name,
                avatar_emoji=kid.avatar_emoji,
                starting_grade=kid.starting_grade,
                levels=[
                    TopicLevelOut(topic=l.topic, difficulty_level=l.difficulty_level)
                    for l in kid.levels
                ],
                total_sessions=total_sessions,
                total_problems_answered=answered,
                overall_accuracy_pct=_accuracy(correct, answered),
            )
        )
    return out


def _session_rows(db: DBSession, kid_id: int | None, limit: int):
    correct_sum = func.sum(case((SessionProblem.is_correct.is_(True), 1), else_=0))
    answered_count = func.sum(case((SessionProblem.is_correct.isnot(None), 1), else_=0))
    q = (
        db.query(
            Session.id,
            Session.kid_id,
            Session.topic,
            Session.started_at,
            Session.ended_at,
            answered_count.label("total"),
            correct_sum.label("correct"),
        )
        .outerjoin(SessionProblem, SessionProblem.session_id == Session.id)
        .group_by(Session.id)
        .order_by(Session.started_at.desc())
        .limit(limit)
    )
    if kid_id is not None:
        q = q.filter(Session.kid_id == kid_id)
    return q.all()


@router.get("/kids/{kid_id}/sessions", response_model=list[SessionRowOut])
def kid_sessions(kid_id: int, limit: int = 50, db: DBSession = Depends(get_db)):
    if not db.get(Kid, kid_id):
        raise HTTPException(status_code=404, detail="Kid not found")
    rows = _session_rows(db, kid_id, limit)
    return [
        SessionRowOut(
            session_id=r.id,
            topic=r.topic,
            started_at=r.started_at,
            ended_at=r.ended_at,
            duration_s=(r.ended_at - r.started_at).total_seconds() if r.ended_at else None,
            total=int(r.total or 0),
            correct=int(r.correct or 0),
            accuracy_pct=_accuracy(int(r.correct or 0), int(r.total or 0)),
        )
        for r in rows
    ]


@router.get("/kids/{kid_id}/topics/{topic}/history", response_model=list[ProblemHistoryPointOut])
def kid_topic_history(
    kid_id: int, topic: str, limit: int = 200, db: DBSession = Depends(get_db)
):
    if not db.get(Kid, kid_id):
        raise HTTPException(status_code=404, detail="Kid not found")
    rows = (
        db.query(SessionProblem)
        .join(Session, Session.id == SessionProblem.session_id)
        .filter(
            Session.kid_id == kid_id,
            Session.topic == topic,
            SessionProblem.is_correct.isnot(None),
        )
        .order_by(SessionProblem.asked_at.asc())
        .limit(limit)
        .all()
    )
    return [
        ProblemHistoryPointOut(
            asked_at=p.asked_at,
            difficulty_at_time=p.difficulty_at_time,
            is_correct=bool(p.is_correct),
            time_taken_s=p.time_taken_s,
            session_id=p.session_id,
        )
        for p in rows
    ]


class SetLevelIn(BaseModel):
    level: float


@router.put("/kids/{kid_id}/topics/{topic}/level", status_code=204)
def set_kid_topic_level(
    kid_id: int, topic: str, body: SetLevelIn, db: DBSession = Depends(get_db)
):
    if not db.get(Kid, kid_id):
        raise HTTPException(status_code=404, detail="Kid not found")
    if not (1 <= body.level <= 20):
        raise HTTPException(status_code=422, detail="level must be 1–20")
    row = (
        db.query(KidTopicLevel)
        .filter(KidTopicLevel.kid_id == kid_id, KidTopicLevel.topic == topic)
        .first()
    )
    if row is None:
        db.add(KidTopicLevel(kid_id=kid_id, topic=topic, difficulty_level=body.level, score_accumulator=0.0))
    else:
        row.difficulty_level = body.level
        row.score_accumulator = 0.0
    db.commit()


@router.get("/activity", response_model=list[ActivityRowOut])
def activity(limit: int = 30, db: DBSession = Depends(get_db)):
    rows = _session_rows(db, None, limit)
    kid_ids = {r.kid_id for r in rows}
    kids = {k.id: k for k in db.query(Kid).filter(Kid.id.in_(kid_ids)).all()} if kid_ids else {}
    out: list[ActivityRowOut] = []
    for r in rows:
        kid = kids.get(r.kid_id)
        out.append(
            ActivityRowOut(
                session_id=r.id,
                kid_id=r.kid_id,
                kid_name=kid.name if kid else "",
                avatar_emoji=kid.avatar_emoji if kid else "",
                topic=r.topic,
                started_at=r.started_at,
                ended_at=r.ended_at,
                duration_s=(r.ended_at - r.started_at).total_seconds() if r.ended_at else None,
                total=int(r.total or 0),
                correct=int(r.correct or 0),
                accuracy_pct=_accuracy(int(r.correct or 0), int(r.total or 0)),
            )
        )
    return out
