"""
Scrape exercises from online.haprofessor.com and write to data/haprofessor_questions.json.

Usage:
    uv run python scripts/scrape_haprofessor.py [--sessions N] [--output PATH]

Credentials are read from HAPROFESSOR_USER / HAPROFESSOR_PASS env vars or .env file.

Rate limiting: random 3-7s between questions, 10-20s between sessions, 20-40s between topics.
"""

import argparse
import hashlib
import json
import os
import random
import re
import sys
import time
from pathlib import Path
from urllib.parse import urljoin

import requests
from bs4 import BeautifulSoup
from dotenv import load_dotenv

BASE_URL = "https://online.haprofessor.com"
GRADE_ID = 107  # כיתה ב'
GROUPS = [78, 31004]  # ממוקד מבחן + העשרה (both immediate-feedback)

HEADERS = {
    "User-Agent": (
        "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
        "AppleWebKit/537.36 (KHTML, like Gecko) "
        "Chrome/124.0.0.0 Safari/537.36"
    ),
    "Accept-Language": "he-IL,he;q=0.9,en-US;q=0.8,en;q=0.7",
    "Referer": BASE_URL,
}


def sleep(lo: float, hi: float) -> None:
    t = random.uniform(lo, hi)
    print(f"  [sleep {t:.1f}s]")
    time.sleep(t)


def get_csrf(soup: BeautifulSoup) -> str:
    el = soup.select_one('[name=csrfmiddlewaretoken]')
    return el["value"] if el else ""


def login(sess: requests.Session, username: str, password: str) -> bool:
    resp = sess.get(f"{BASE_URL}/accounts/login/", headers=HEADERS)
    soup = BeautifulSoup(resp.text, "html.parser")
    csrf = get_csrf(soup)
    resp = sess.post(
        f"{BASE_URL}/accounts/login/",
        data={"username": username, "password": password, "csrfmiddlewaretoken": csrf},
        headers={**HEADERS, "Referer": f"{BASE_URL}/accounts/login/"},
        allow_redirects=True,
    )
    return "/accounts/login/" not in resp.url


def get_topic_links(sess: requests.Session, group_id: int) -> list[dict]:
    """Return list of {label, url} for each topic in the group."""
    base_url = f"{BASE_URL}/exams/by_group/{group_id}/{GRADE_ID}"
    resp = sess.get(base_url, headers=HEADERS)
    soup = BeautifulSoup(resp.text, "html.parser")

    topics = []
    seen_hrefs = set()
    for a in soup.select("a[href]"):
        href = a["href"]
        if not href or href in seen_hrefs or href == "/":
            continue
        # Only accept topic links: relative ?subject_id=X query params
        if not href.startswith("?subject_id="):
            continue
        full = urljoin(base_url, href)
        label = a.get_text(" ", strip=True)
        if not label:
            continue
        topics.append({"label": label, "url": full})
        seen_hrefs.add(href)

    return topics


def start_topic_session(sess: requests.Session, topic: dict) -> str | None:
    """Navigate to topic and return the resulting exam URL (or None on failure)."""
    for attempt in range(2):
        if topic.get("method") == "POST":
            resp = sess.post(topic["url"], data=topic.get("data", {}), headers=HEADERS, allow_redirects=True)
        else:
            resp = sess.get(topic["url"], headers=HEADERS, allow_redirects=True)

        url = resp.url
        # Skip summary pages (completed/expired sessions)
        if url.endswith("/summary") or "/summary" in url.split("?")[0]:
            print(f"    -> summary redirect, attempt {attempt + 1}")
            if attempt == 0:
                sleep(5, 10)
                continue
            return None

        if "/exams/" in url and "/by_group/" not in url:
            soup = BeautifulSoup(resp.text, "html.parser")
            if soup.select_one("form#question-form"):
                return url
            # No form yet — session may redirect to summary on next GET
            return None

    return None


def parse_question_page(soup: BeautifulSoup, group_id: int) -> dict | None:
    """Extract question data from an exam page. Returns None for unsupported types."""
    form = soup.select_one("form#question-form")
    if not form:
        return None

    # Skip image-based questions (no text to store)
    if form.select_one("img#question_image"):
        return None

    # Skip fill-in-blank (sequence with text input, uses true/false radio trick)
    if form.select_one("#original-sequence, #the-sequence"):
        return None

    # Question text: join all <p> tags inside the form
    paras = [p.get_text(" ", strip=True) for p in form.select("p") if p.get_text(strip=True)]
    question_text = " ".join(paras)

    if not question_text:
        return None

    # Correct answer and distractors via data-is-correct attribute on labels
    correct_answer = ""
    distractors = []
    for label in form.select("label[data-is-correct]"):
        text = label.get_text(strip=True)
        if label.get("data-is-correct") == "True":
            correct_answer = text
        else:
            distractors.append(text)

    # Fallback: data-correct on the radio input itself (older page variant)
    if not correct_answer:
        for inp in form.select("input[data-correct='True']"):
            label = inp.find_parent("label")
            if label:
                correct_answer = label.get_text(strip=True)
        for inp in form.select("input[type=radio]:not([data-correct])"):
            label = inp.find_parent("label")
            if label:
                distractors.append(label.get_text(strip=True))

    # Skip if no usable MC answer structure (e.g. true/false fill-in submit radios)
    if not correct_answer or set(distractors) <= {"true", "false"}:
        return None

    # Hidden form fields for submission
    csrf = get_csrf(soup)
    q_id_el = form.select_one("[name=question_id]")
    question_id = q_id_el["value"] if q_id_el else ""

    # First radio value (any option) for advancing the session
    first_radio = form.select_one("input[type=radio][name=answer_id]")
    first_answer_id = first_radio["value"] if first_radio else ""

    # Question number + topic label from footer bar
    question_num = None
    topic_label = ""
    footer = soup.find(string=re.compile(r"שאלה\s*#?\d+"))
    if footer:
        m = re.search(r"#?(\d+)", str(footer))
        if m:
            question_num = int(m.group(1))
        m2 = re.search(r"נושא[:\s]+(.+)", str(footer))
        if m2:
            topic_label = m2.group(1).strip()

    return {
        "group_id": group_id,
        "topic_label": topic_label,
        "question_num": question_num,
        "question": question_text,
        "correct_answer": correct_answer,
        "distractors": distractors,
        "_csrf": csrf,
        "_question_id": question_id,
        "_first_answer_id": first_answer_id,
    }


def advance_question(sess: requests.Session, url: str, q: dict) -> bool:
    """Submit an answer to advance server-side to next question."""
    if not q.get("_question_id") or not q.get("_first_answer_id"):
        return False
    data = {
        "csrfmiddlewaretoken": q["_csrf"],
        "question_id": q["_question_id"],
        "answer_id": q["_first_answer_id"],
        "subject_time_over": "False",
        "ajax": "true",
    }
    try:
        resp = sess.post(url, data=data, headers={**HEADERS, "X-Requested-With": "XMLHttpRequest"})
        resp.json()  # validate it's JSON
        return True
    except Exception:
        return False


def scrape_session(sess: requests.Session, exam_url: str, group_id: int) -> list[dict]:
    """Scrape all questions from one 10-question exam session."""
    records = []
    current_url = exam_url

    for q_num in range(1, 11):
        sleep(3, 7)  # polite delay between questions

        resp = sess.get(current_url, headers=HEADERS)
        if resp.status_code != 200:
            print(f"    HTTP {resp.status_code} on Q{q_num}, stopping session")
            break

        soup = BeautifulSoup(resp.text, "html.parser")

        # Check if session ended (no form at all)
        if not soup.select_one("form#question-form"):
            print(f"    No form on Q{q_num}, session ended")
            break

        q = parse_question_page(soup, group_id)

        # Advance through unsupported question types (image-only, fill-in-blank)
        if q is None:
            print(f"    Q{q_num}: skipped (unsupported type)")
            # Still need to advance — extract form fields directly
            form = soup.select_one("form#question-form")
            csrf = get_csrf(soup)
            q_id = (form.select_one("[name=question_id]") or {}).get("value", "")
            radio = form.select_one("input[type=radio][name=answer_id]")
            if q_id and radio:
                advance_question(sess, current_url, {
                    "_csrf": csrf, "_question_id": q_id,
                    "_first_answer_id": radio["value"],
                })
            continue

        if q["question"]:
            h = hashlib.sha256(q["question"].encode()).hexdigest()[:16]
            records.append({
                "source": "haprofessor",
                "group_id": q["group_id"],
                "topic_label": q["topic_label"],
                "question_num": q["question_num"],
                "question": q["question"],
                "correct_answer": q["correct_answer"],
                "distractors": q["distractors"],
                "source_hash": h,
            })
            print(f"    Q{q_num}: {q['question'][:70]}")

        # Advance to next question
        advance_question(sess, current_url, q)

    return records


def main() -> None:
    load_dotenv(Path(__file__).parent.parent / ".env")

    parser = argparse.ArgumentParser(description="Scrape haprofessor exercises")
    parser.add_argument("--sessions", type=int, default=5, help="Sessions per topic (default 5)")
    parser.add_argument("--output", default="data/haprofessor_questions.json")
    args = parser.parse_args()

    username = os.environ.get("HAPROFESSOR_USER")
    password = os.environ.get("HAPROFESSOR_PASS")
    if not username or not password:
        print("ERROR: Set HAPROFESSOR_USER and HAPROFESSOR_PASS in .env or environment")
        sys.exit(1)

    out_path = Path(args.output)
    existing: list[dict] = []
    if out_path.exists():
        existing = json.loads(out_path.read_text(encoding="utf-8"))
        print(f"Loaded {len(existing)} existing records from {out_path}")

    seen_hashes = {r["source_hash"] for r in existing}
    all_records = list(existing)

    sess = requests.Session()
    sess.headers.update(HEADERS)

    print("Logging in...")
    if not login(sess, username, password):
        print("ERROR: Login failed — check credentials")
        sys.exit(1)
    print("Logged in OK")

    for group_id in GROUPS:
        sleep(3, 6)
        print(f"\n=== Group {group_id} ===")
        topics = get_topic_links(sess, group_id)
        if not topics:
            print(f"  No topics found for group {group_id}")
            continue
        print(f"  Found {len(topics)} topics: {[t['label'] for t in topics]}")

        for topic in topics:
            print(f"\n  Topic: {topic['label']}")
            sleep(10, 20)  # pause between topics

            for s in range(1, args.sessions + 1):
                print(f"    Session {s}/{args.sessions}")
                sleep(10, 20)  # pause between sessions

                exam_url = start_topic_session(sess, topic)
                if not exam_url:
                    print("    Could not start session, skipping")
                    break

                records = scrape_session(sess, exam_url, group_id)
                new = [r for r in records if r["source_hash"] not in seen_hashes]
                for r in new:
                    seen_hashes.add(r["source_hash"])
                    all_records.append(r)

                print(f"    +{len(new)} new ({len(records) - len(new)} dupes)")

    out_path.write_text(json.dumps(all_records, ensure_ascii=False, indent=2), encoding="utf-8")
    print(f"\nWrote {len(all_records)} total records to {out_path}")


if __name__ == "__main__":
    main()
