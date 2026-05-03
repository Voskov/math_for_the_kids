"""
Import scraped haprofessor questions from JSON into the bank_questions table.

Usage:
    uv run python scripts/import_haprofessor.py [--input PATH] [--difficulty N] [--dry-run]
"""

import argparse
import hashlib
import json
import sys
from pathlib import Path

# Hebrew topic label → app topic name
TOPIC_MAP: dict[str, str] = {
    "סדרות": "sequence",
    "סדרות פתוחות": "sequence",
    "סדרות: צורות ומספרים": "sequence",
    "תרגילים ומשוואות": "arithmetic",
    "בעיות בחשבון": "arithmetic",
    "בעיות בחשבון (מבחן שלב ב')": "arithmetic",
    "יחסי מילים": "word_problems",
    "השלמת משפטים": "word_problems",
    "תבניות של צורות": "shapes",
    "צורות ברצף": "shapes",
    "צורות בזווות": "shapes",
    "יוצא דופן צורות": "shapes",
    "יוצא דופן": "shapes",
    "ידע והבנה": "haprofessor",
    "פרושי מלים": "haprofessor",
    "צורות (שטיחים)": "shapes",
}


def map_topic(label: str) -> str:
    clean = label.strip()
    if clean in TOPIC_MAP:
        return TOPIC_MAP[clean]
    # Fuzzy: check if any key is a substring
    for k, v in TOPIC_MAP.items():
        if k in clean or clean in k:
            return v
    return "haprofessor"


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--input", default="data/haprofessor_questions.json")
    parser.add_argument("--difficulty", type=int, default=10,
                        help="Default difficulty for imported questions (1-20, default 10)")
    parser.add_argument("--dry-run", action="store_true",
                        help="Print what would be imported without writing to DB")
    args = parser.parse_args()

    in_path = Path(args.input)
    if not in_path.exists():
        print(f"ERROR: {in_path} not found. Run scrape_haprofessor.py first.")
        sys.exit(1)

    records = json.loads(in_path.read_text(encoding="utf-8"))
    print(f"Loaded {len(records)} records from {in_path}")

    if args.dry_run:
        topics: dict[str, int] = {}
        for r in records:
            t = map_topic(r.get("topic_label", ""))
            topics[t] = topics.get(t, 0) + 1
        print("Dry-run — topic distribution:")
        for t, n in sorted(topics.items()):
            print(f"  {t}: {n}")
        return

    # Import into DB
    import hashlib as _hashlib
    sys.path.insert(0, str(Path(__file__).parent.parent))
    from backend.database import engine
    from backend.models import BankQuestion
    from sqlalchemy.orm import Session as OrmSession

    added = updated = skipped = 0
    with OrmSession(engine) as db:
        for r in records:
            q_text = r.get("question", "").strip()
            correct = r.get("correct_answer", "").strip()
            distractors = [d for d in r.get("distractors", []) if d.strip()]

            if not q_text or not correct:
                skipped += 1
                continue

            source_hash = r.get("source_hash") or _hashlib.sha256(q_text.encode()).hexdigest()[:16]
            topic = map_topic(r.get("topic_label", ""))
            topic_label = r.get("topic_label", "")
            import json as _json
            distractors_json = _json.dumps(distractors, ensure_ascii=False)

            existing = db.query(BankQuestion).filter_by(source_hash=source_hash).first()
            if existing:
                existing.question = q_text
                existing.correct_answer = correct
                existing.distractors = distractors_json
                existing.difficulty = args.difficulty
                existing.subtype = topic_label
                updated += 1
            else:
                db.add(BankQuestion(
                    topic=topic,
                    subtype=topic_label,
                    difficulty=args.difficulty,
                    question=q_text,
                    correct_answer=correct,
                    distractors=distractors_json,
                    source_hash=source_hash,
                ))
                added += 1

        db.commit()

    print(f"Done: {added} added, {updated} updated, {skipped} skipped")


if __name__ == "__main__":
    main()
