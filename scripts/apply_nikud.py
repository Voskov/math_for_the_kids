"""
Apply Nikud to trivia/countries JSON files and re-seed the DB.
Run once from repo root: uv run python scripts/apply_nikud.py
"""
import json
import sys
from pathlib import Path

ROOT = Path(__file__).parent.parent
TODO = ROOT / "data" / "nikud_todo.txt"
DONE = ROOT / "data" / "nikud_done.txt"


def parse_terms(path):
    return [
        line.strip()
        for line in path.read_text(encoding="utf-8").splitlines()
        if line.strip() and not line.startswith("##")
    ]


def build_mapping():
    originals = parse_terms(TODO)
    vowelized = parse_terms(DONE)
    assert len(originals) == len(vowelized), \
        f"Line count mismatch: {len(originals)} todo vs {len(vowelized)} done"

    m = dict(zip(originals, vowelized))

    # Fix two incomplete entries from the Nikud website
    m["עדה לאבלייס"] = "עֵדָה לָאבְלֵיס"
    m["מקסימיליאן רובספייר"] = "מַקְסִימִילְיָאן רוֹבֶּסְפְּיֵר"

    # Standardize Freud: סיגמונד → vowelized זיגמונד
    m["סיגמונד פרויד"] = m["זיגמונד פרויד"]

    # Fix distractor typo בונוס → בואנוס (with Nikud)
    m["בונוס איירס"] = m["בואנוס איירס"]

    return m


def apply_to_file(path, mapping):
    text = path.read_text(encoding="utf-8")
    for orig, vow in mapping.items():
        text = text.replace(orig, vow)
    path.write_text(text, encoding="utf-8")
    print(f"  updated {path.relative_to(ROOT)}")


def reseed(mapping):
    sys.path.insert(0, str(ROOT))
    import hashlib
    from backend.database import engine, _seed_trivia_bank
    from backend.models import BankQuestion
    from sqlalchemy.orm import Session

    with Session(engine) as db:
        deleted = db.query(BankQuestion).filter(
            BankQuestion.topic.in_(["trivia", "countries"])
        ).delete()
        db.commit()
        print(f"  deleted {deleted} old rows")

    _seed_trivia_bank()
    print("  re-seeded trivia")

    capitals = json.loads((ROOT / "data" / "gemini_2_capitals.json").read_text(encoding="utf-8"))
    with Session(engine) as db:
        for r in capitals:
            h = hashlib.sha256(r["question"].encode()).hexdigest()[:16]
            db.add(BankQuestion(
                topic="countries",
                subtype=r.get("subtype", "capital_to_country"),
                difficulty=r.get("difficulty", 10),
                question=r["question"],
                correct_answer=r["correct_answer"],
                distractors=json.dumps(r["distractors"], ensure_ascii=False),
                source_hash=h,
            ))
        db.commit()
    print(f"  re-seeded {len(capitals)} countries questions")


def main():
    print("Building mapping...")
    mapping = build_mapping()
    print(f"  {len(mapping)} replacements")

    print("Updating JSON files...")
    apply_to_file(ROOT / "backend" / "generators" / "trivia_bank" / "direct.json", mapping)
    apply_to_file(ROOT / "backend" / "generators" / "trivia_bank" / "clue.json", mapping)
    apply_to_file(ROOT / "data" / "gemini_2_capitals.json", mapping)

    print("Re-seeding DB...")
    reseed(mapping)

    print("Done.")


if __name__ == "__main__":
    main()
