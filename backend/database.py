import hashlib
import json
from pathlib import Path
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
    _migrate_bank_questions()
    _migrate_kids()
    _seed_kids()
    _seed_special_kids()
    _seed_trivia_bank()
    _seed_countries_bank()


def _migrate_kids():
    from sqlalchemy import text
    with engine.connect() as conn:
        try:
            conn.execute(text("ALTER TABLE kids ADD COLUMN is_special INTEGER NOT NULL DEFAULT 0"))
            conn.commit()
        except Exception:
            pass  # column already exists


def _migrate_bank_questions():
    from sqlalchemy import text
    with engine.connect() as conn:
        try:
            conn.execute(text("ALTER TABLE bank_questions ADD COLUMN wiki_url TEXT"))
            conn.commit()
        except Exception:
            pass  # column already exists


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


def _seed_special_kids():
    from backend.models import Kid
    special = [
        {"name": "בדיקה", "avatar_emoji": "🧪", "starting_grade": "2nd"},
        {"name": "אורח",  "avatar_emoji": "👤", "starting_grade": "2nd"},
    ]
    with Session(engine) as db:
        for spec in special:
            if not db.query(Kid).filter_by(name=spec["name"]).first():
                db.add(Kid(name=spec["name"], avatar_emoji=spec["avatar_emoji"],
                           starting_grade=spec["starting_grade"], is_special=True))
        db.commit()


_TRIVIA_BANK_DIR = Path(__file__).parent / "generators" / "trivia_bank"
_COUNTRIES_BANK_PATH = Path(__file__).parent.parent / "countries" / "countries_capitals_trivia.json"


def _trivia_rows():
    direct_path = _TRIVIA_BANK_DIR / "direct.json"
    clue_path = _TRIVIA_BANK_DIR / "clue.json"
    if direct_path.exists():
        for item in json.loads(direct_path.read_text(encoding="utf-8")):
            yield {
                "subtype": "direct",
                "difficulty": 5,
                "question": item["question"],
                "correct_answer": item["correct_answer"],
                "distractors": item["distractors"],
            }
    if clue_path.exists():
        for item in json.loads(clue_path.read_text(encoding="utf-8")):
            yield {
                "subtype": "clue",
                "difficulty": 12,
                "question": item["description"],
                "correct_answer": item["correct_answer"],
                "distractors": item["distractors"],
            }


def _seed_trivia_bank():
    from backend.models import BankQuestion
    with Session(engine) as db:
        for r in _trivia_rows():
            h = hashlib.sha256(r["question"].encode("utf-8")).hexdigest()[:16]
            existing = db.query(BankQuestion).filter_by(source_hash=h).first()
            distractors_json = json.dumps(r["distractors"], ensure_ascii=False)
            if existing:
                existing.question = r["question"]
                existing.correct_answer = r["correct_answer"]
                existing.distractors = distractors_json
                existing.difficulty = r["difficulty"]
                existing.subtype = r["subtype"]
            else:
                db.add(BankQuestion(
                    topic="trivia",
                    subtype=r["subtype"],
                    difficulty=r["difficulty"],
                    question=r["question"],
                    correct_answer=r["correct_answer"],
                    distractors=distractors_json,
                    source_hash=h,
                ))
        db.commit()


def _seed_countries_bank():
    from backend.models import BankQuestion
    if not _COUNTRIES_BANK_PATH.exists():
        return
    items = json.loads(_COUNTRIES_BANK_PATH.read_text(encoding="utf-8"))
    difficulty_map = {"country_to_capital": 5, "capital_to_country": 8}
    with Session(engine) as db:
        for item in items:
            h = hashlib.sha256(item["question"].encode("utf-8")).hexdigest()[:16]
            existing = db.query(BankQuestion).filter_by(source_hash=h).first()
            distractors_json = json.dumps(item["distractors"], ensure_ascii=False)
            diff = difficulty_map.get(item["type"], 8)
            if existing:
                existing.question = item["question"]
                existing.correct_answer = item["correct_answer"]
                existing.distractors = distractors_json
                existing.difficulty = diff
                existing.subtype = item["type"]
            else:
                db.add(BankQuestion(
                    topic="countries",
                    subtype=item["type"],
                    difficulty=diff,
                    question=item["question"],
                    correct_answer=item["correct_answer"],
                    distractors=distractors_json,
                    source_hash=h,
                ))
        db.commit()
