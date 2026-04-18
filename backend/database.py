from sqlalchemy import create_engine
from sqlalchemy.orm import DeclarativeBase, Session

DATABASE_URL = "sqlite:///./data/math_tutor.db"

engine = create_engine(DATABASE_URL, connect_args={"check_same_thread": False})


class Base(DeclarativeBase):
    pass


def get_db():
    with Session(engine) as session:
        yield session


def init_db():
    from backend import models  # noqa: F401 — ensures models are registered
    Base.metadata.create_all(bind=engine)
    _seed_kids()


def _seed_kids():
    from backend.models import Kid, KidTopicLevel
    with Session(engine) as db:
        if db.query(Kid).count() > 0:
            return
        kids = [
            Kid(name="טום", avatar_emoji="👦🏼", starting_grade="2nd", id=1),
            Kid(name="אדם", avatar_emoji="👦🏻", starting_grade="1st", id=2),
            Kid(name="בן", avatar_emoji="👶🏼", starting_grade="preschool", id=3),
        ]
        default_levels = {"2nd": 7.0, "1st": 5.0, "preschool": 1.0}
        db.add_all(kids)
        db.flush()
        for kid in kids:
            for topic in ["arithmetic"]:
                db.add(KidTopicLevel(
                    kid_id=kid.id,
                    topic=topic,
                    difficulty_level=default_levels[kid.starting_grade],
                    score_accumulator=0.0,
                ))
        db.commit()
