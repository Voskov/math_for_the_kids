"""
Number sequence problem generator.
Produces fill-in-the-missing-number problems (one gap per sequence of 5 terms).

Difficulty map:
  1–2   add by 1 or 2, small starting numbers
  3–4   skip-count by 3, 4, or 5
  5–6   skip-count by 6–10, larger starting numbers
  7–8   subtract sequences (count down by 2–8)
  9–10  multiply sequences (×2 or ×3)
  11–12 divide sequences (÷2 or ÷3)
  13–14 increasing-step sequences (triangular-style: +2, +3, +4, +5)
  15–16 alternating two-step patterns (+a, +b, +a, +b)
  17–18 perfect-square sequences (n², (n+1)², …)
  19–20 Fibonacci-style or ×m+b recurrence
"""

import random


def generate(difficulty: float) -> dict:
    d = int(difficulty)
    if d <= 2:
        return _add_seq(step_range=(1, 2), start_range=(1, 10))
    if d <= 4:
        return _add_seq(step_range=(3, 5), start_range=(1, 15))
    if d <= 6:
        return _add_seq(step_range=(6, 10), start_range=(1, 20))
    if d <= 8:
        return _subtract_seq(difficulty)
    if d <= 10:
        return _multiply_seq(difficulty)
    if d <= 12:
        return _divide_seq(difficulty)
    if d <= 14:
        return _increasing_step_seq()
    if d <= 16:
        return _alternating_seq()
    if d <= 18:
        return _squares_seq()
    return _complex_seq()


# ── helpers ──────────────────────────────────────────────────────────────────

def _make_q(terms: list, gap_idx: int) -> dict:
    answer = terms[gap_idx]
    parts = ["_" if i == gap_idx else str(t) for i, t in enumerate(terms)]
    return {"question": ", ".join(parts), "answer": str(answer)}


def _gap(lo: int = 2, hi: int = 4) -> int:
    return random.randint(lo, hi)


# ── generators ───────────────────────────────────────────────────────────────

def _add_seq(step_range: tuple, start_range: tuple) -> dict:
    step = random.randint(*step_range)
    start = random.randint(*start_range)
    terms = [start + step * i for i in range(5)]
    return _make_q(terms, _gap())


def _subtract_seq(difficulty: float) -> dict:
    step = random.randint(2, 5) if difficulty < 7.5 else random.randint(3, 8)
    start = random.randint(step * 4 + 1, step * 4 + 30)
    terms = [start - step * i for i in range(5)]
    return _make_q(terms, _gap())


def _multiply_seq(difficulty: float) -> dict:
    ratio = 2 if difficulty < 9.5 else random.choice([2, 3])
    start = random.randint(1, 5)
    terms = [start * (ratio ** i) for i in range(5)]
    return _make_q(terms, _gap())


def _divide_seq(difficulty: float) -> dict:
    ratio = 2 if difficulty < 11.5 else random.choice([2, 3])
    # pick a start that divides cleanly 4 times
    power = ratio ** 4
    start = power * random.randint(1, 4)
    terms = [start // (ratio ** i) for i in range(5)]
    # gap earlier so kids still have small visible numbers as anchors
    return _make_q(terms, _gap(lo=1, hi=3))


def _increasing_step_seq() -> dict:
    start = random.randint(1, 10)
    init_step = random.randint(1, 3)
    terms = [start]
    step = init_step
    for _ in range(4):
        terms.append(terms[-1] + step)
        step += 1
    return _make_q(terms, _gap())


def _alternating_seq() -> dict:
    a = random.randint(1, 5)
    b = random.randint(6, 15)
    start = random.randint(1, 10)
    terms = [start]
    for i in range(4):
        terms.append(terms[-1] + (a if i % 2 == 0 else b))
    return _make_q(terms, _gap())


def _squares_seq() -> dict:
    n = random.randint(1, 7)
    terms = [(n + i) ** 2 for i in range(5)]
    return _make_q(terms, _gap())


def _complex_seq() -> dict:
    if random.random() < 0.5:
        # Fibonacci-style: each term = sum of previous two
        a, b = random.randint(1, 5), random.randint(1, 5)
        terms = [a, b]
        for _ in range(3):
            terms.append(terms[-1] + terms[-2])
    else:
        # ×m + b recurrence
        m = random.choice([2, 3])
        b = random.randint(1, 4)
        start = random.randint(1, 5)
        terms = [start]
        for _ in range(4):
            terms.append(terms[-1] * m + b)
    return _make_q(terms, _gap())
