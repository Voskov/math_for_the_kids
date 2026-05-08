"""
Import AI-generated questions from JSON into the bank_questions table.

Usage:
    uv run python scripts/import_ai_questions.py --input data/gemini_trivia.json
    uv run python scripts/import_ai_questions.py --input data/gemini_trivia.json --dry-run

Expected JSON format:
    [
      {
        "topic": "trivia",
        "subtype": "direct",
        "difficulty": 5,
        "question": "...",
        "correct_answer": "...",
        "distractors": ["...", "...", "..."]
      }
    ]
"""

import argparse
import hashlib
import json
import sys
from pathlib import Path


def validate(r: dict, idx: int) -> str | None:
    for f in ("topic", "question", "correct_answer", "distractors"):
        if not r.get(f):
            return f"record {idx}: missing '{f}'"
    if not isinstance(r["distractors"], list) or len(r["distractors"]) != 3:
        return f"record {idx}: 'distractors' must be a list of exactly 3 items"
    diff = r.get("difficulty", 0)
    if not isinstance(diff, int) or not (1 <= diff <= 20):
        return f"record {idx}: 'difficulty' must be int 1-20, got {diff!r}"
    return None


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--input", required=True, help="Path to AI-generated JSON file")
    parser.add_argument("--dry-run", action="store_true",
                        help="Validate and show stats without writing to DB")
    args = parser.parse_args()

    in_path = Path(args.input)
    if not in_path.exists():
        print(f"ERROR: {in_path} not found")
        sys.exit(1)

    records = json.loads(in_path.read_text(encoding="utf-8-sig"))
    if not isinstance(records, list):
        print("ERROR: JSON must be a top-level array")
        sys.exit(1)

    print(f"Loaded {len(records)} records from {in_path}")

    errors = [e for i, r in enumerate(records) if (e := validate(r, i))]
    if errors:
        for e in errors:
            print(f"  INVALID: {e}")
        print(f"{len(errors)} invalid records — fix before importing")
        sys.exit(1)

    if args.dry_run:
        by_topic: dict[str, int] = {}
        for r in records:
            k = f"{r['topic']}:{r.get('subtype', '-')} (diff {r['difficulty']})"
            by_topic[k] = by_topic.get(k, 0) + 1
        print("Dry-run — distribution:")
        for k, n in sorted(by_topic.items()):
            print(f"  {k}: {n}")
        return

    sys.path.insert(0, str(Path(__file__).parent.parent))
    from backend.database import engine
    from backend.models import BankQuestion
    from sqlalchemy.orm import Session as OrmSession

    added = updated = 0
    with OrmSession(engine) as db:
        for r in records:
            q_text = r["question"].strip()
            correct = r["correct_answer"].strip()
            source_hash = hashlib.sha256(q_text.encode()).hexdigest()[:16]
            distractors_json = json.dumps(r["distractors"], ensure_ascii=False)

            existing = db.query(BankQuestion).filter_by(source_hash=source_hash).first()
            if existing:
                existing.question = q_text
                existing.correct_answer = correct
                existing.distractors = distractors_json
                existing.difficulty = r["difficulty"]
                existing.topic = r["topic"]
                existing.subtype = r.get("subtype")
                existing.wiki_url = r.get("wiki_url")
                updated += 1
            else:
                db.add(BankQuestion(
                    topic=r["topic"],
                    subtype=r.get("subtype"),
                    difficulty=r["difficulty"],
                    question=q_text,
                    correct_answer=correct,
                    distractors=distractors_json,
                    source_hash=source_hash,
                    wiki_url=r.get("wiki_url"),
                ))
                added += 1

        db.commit()

    print(f"Done: {added} added, {updated} updated")


if __name__ == "__main__":
    main()
