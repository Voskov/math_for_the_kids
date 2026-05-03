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
    url = f"{BASE_URL}/exams/by_group/{group_id}/{GRADE_ID}"
    resp = sess.get(url, headers=HEADERS)
    soup = BeautifulSoup(resp.text, "html.parser")

    topics = []
    seen_hrefs = set()
    for a in soup.select("a[href]"):
        href = a["href"]
        if not href or href in seen_hrefs:
            continue
        # Skip back-to-home, non-exam, and group-level links
        full = urljoin(BASE_URL, href)
        if "/exams/" not in full or "/by_group/" in full or "/active/" in full:
            continue
        label = a.get_text(" ", strip=True)
        if not label:
            continue
        topics.append({"label": label, "url": full})
        seen_hrefs.add(href)

    # Also look for form-submit buttons that might navigate to topics
    for form in soup.select("form[action]"):
        action = urljoin(BASE_URL, form["action"])
        if "/exams/" not in action or action in seen_hrefs:
            continue
        label = form.get_text(" ", strip=True)[:40]
        topics.append({"label": label, "url": action, "method": "POST",
                        "data": {i["name"]: i.get("value", "") for i in form.select("input")}})
        seen_hrefs.add(action)

    return topics


def start_topic_session(sess: requests.Session, topic: dict) -> str | None:
    """Navigate to topic and return the resulting exam URL (or None on failure)."""
    if topic.get("method") == "POST":
        resp = sess.post(topic["url"], data=topic.get("data", {}), headers=HEADERS, allow_redirects=True)
    else:
        resp = sess.get(topic["url"], headers=HEADERS, allow_redirects=True)

    if "/exams/" in resp.url and "/by_group/" not in resp.url:
        return resp.url
    # Maybe we need to look for a redirect or a meta-refresh
    soup = BeautifulSoup(resp.text, "html.parser")
    # Check if exam form is on this page
    if soup.select_one("form#question-form"):
        return resp.url
    return None


def parse_question_page(soup: BeautifulSoup, group_id: int) -> dict | None:
    """Extract question data from an exam page."""
    form = soup.select_one("form#question-form")
    if not form:
        return None

    # Question text: first non-trivial <p> inside the form
    question_text = ""
    for p in form.select("p"):
        text = p.get_text(" ", strip=True)
        if text and len(text) > 3:
            question_text = text
            break

    if not question_text:
        # Fallback: generic div/span with substantial text before the radio list
        for el in form.children:
            if hasattr(el, "get_text"):
                text = el.get_text(" ", strip=True)
                if len(text) > 10 and "הַבָּא" not in text:
                    question_text = text
                    break

    # Answer options from radio labels
    options = []
    for label in form.select("label"):
        radio = label.find("input", {"type": "radio"})
        if radio:
            options.append({
                "answer_id": radio.get("value", ""),
                "text": label.get_text(strip=True),
            })

    if not options:
        return None

    # Correct answer: pre-rendered as .label.success in wrong-answer dialog
    correct_answer = ""
    correct_el = soup.select_one("#wrong-answer .question-in-summary .label.success")
    if correct_el:
        correct_answer = correct_el.get_text(strip=True)

    # Hidden form fields for submission
    csrf = get_csrf(soup)
    q_id_el = form.select_one("[name=question_id]")
    question_id = q_id_el["value"] if q_id_el else ""

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
        "options": options,
        "_csrf": csrf,
        "_question_id": question_id,
    }


def advance_question(sess: requests.Session, url: str, q: dict) -> bool:
    """Submit an answer (first option) to advance server-side to next question."""
    if not q.get("_question_id") or not q.get("options"):
        return False
    data = {
        "csrfmiddlewaretoken": q["_csrf"],
        "question_id": q["_question_id"],
        "answer_id": q["options"][0]["answer_id"],
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
        q = parse_question_page(soup, group_id)
        if not q:
            print(f"    No question form on Q{q_num}, session ended")
            break

        if q["question"]:
            records.append({
                "source": "haprofessor",
                "group_id": q["group_id"],
                "topic_label": q["topic_label"],
                "question_num": q["question_num"],
                "question": q["question"],
                "correct_answer": q["correct_answer"],
                "distractors": [o["text"] for o in q["options"] if o["text"] != q["correct_answer"]],
                "source_hash": hashlib.sha256(q["question"].encode()).hexdigest()[:16],
            })
            status = "✓ " + q["question"][:60]
            print(f"    Q{q_num}: {status}")

        # Advance to next question
        advance_question(sess, current_url, q)

    return records


def main() -> None:
    load_dotenv()

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
