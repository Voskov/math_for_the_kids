from datetime import datetime
from sqlalchemy import Boolean, DateTime, Float, ForeignKey, Integer, String
from sqlalchemy.orm import Mapped, mapped_column, relationship
from backend.database import Base


class Kid(Base):
    __tablename__ = "kids"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    name: Mapped[str] = mapped_column(String, nullable=False)
    avatar_emoji: Mapped[str] = mapped_column(String, default="🧒")
    starting_grade: Mapped[str] = mapped_column(String)  # "preschool", "1st", "2nd"

    levels: Mapped[list["KidTopicLevel"]] = relationship("KidTopicLevel", back_populates="kid")
    sessions: Mapped[list["Session"]] = relationship("Session", back_populates="kid")


class KidTopicLevel(Base):
    __tablename__ = "kid_topic_levels"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    kid_id: Mapped[int] = mapped_column(Integer, ForeignKey("kids.id"), nullable=False)
    topic: Mapped[str] = mapped_column(String, nullable=False)
    difficulty_level: Mapped[float] = mapped_column(Float, default=5.0)
    score_accumulator: Mapped[float] = mapped_column(Float, default=0.0)

    kid: Mapped["Kid"] = relationship("Kid", back_populates="levels")


class Session(Base):
    __tablename__ = "sessions"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    kid_id: Mapped[int] = mapped_column(Integer, ForeignKey("kids.id"), nullable=False)
    topic: Mapped[str] = mapped_column(String, nullable=False)
    started_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)
    ended_at: Mapped[datetime | None] = mapped_column(DateTime, nullable=True)
    problem_count: Mapped[int] = mapped_column(Integer, default=10)

    kid: Mapped["Kid"] = relationship("Kid", back_populates="sessions")
    problems: Mapped[list["SessionProblem"]] = relationship("SessionProblem", back_populates="session")


class SessionProblem(Base):
    __tablename__ = "session_problems"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    session_id: Mapped[int] = mapped_column(Integer, ForeignKey("sessions.id"), nullable=False)
    question_text: Mapped[str] = mapped_column(String, nullable=False)
    correct_answer: Mapped[str] = mapped_column(String, nullable=False)
    kid_answer: Mapped[str | None] = mapped_column(String, nullable=True)
    is_correct: Mapped[bool | None] = mapped_column(Boolean, nullable=True)
    time_taken_s: Mapped[float | None] = mapped_column(Float, nullable=True)
    difficulty_at_time: Mapped[float] = mapped_column(Float, nullable=False)
    tts_word: Mapped[str | None] = mapped_column(String, nullable=True)
    asked_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)
    answered_at: Mapped[datetime | None] = mapped_column(DateTime, nullable=True)

    session: Mapped["Session"] = relationship("Session", back_populates="problems")
