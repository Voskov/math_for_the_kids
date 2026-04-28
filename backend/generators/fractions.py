"""
Fractions problem generator.

Difficulty map:
  1–2   fraction of a whole: unit fractions (half, third, quarter of a number)
  3–4   fraction of a whole: non-unit fractions (2/3 of 9, 3/4 of 8)
  5–6   comparing two fractions: which is bigger?
  7–8   equivalent fractions: fill in the missing numerator (1/2 = ?/4)
  9–10  add fractions, same denominator
  11–12 subtract fractions, same denominator
  13–14 add or subtract fractions, different denominators
  15–16 multiply two fractions
  17–18 divide two fractions
  19–20 sum of three fractions
"""

import random
from fractions import Fraction


def generate(difficulty: float) -> dict:
    d = int(difficulty)
    if d <= 2:
        return _fraction_of_whole_unit(difficulty)
    if d <= 4:
        return _fraction_of_whole_non_unit(difficulty)
    if d <= 6:
        return _compare_fractions(difficulty)
    if d <= 8:
        return _equivalent_fractions(difficulty)
    if d <= 10:
        return _add_same_denom(difficulty)
    if d <= 12:
        return _subtract_same_denom(difficulty)
    if d <= 14:
        return _add_sub_diff_denom(difficulty)
    if d <= 16:
        return _multiply_fractions(difficulty)
    if d <= 18:
        return _divide_fractions(difficulty)
    return _three_fractions(difficulty)


# ── helpers ──────────────────────────────────────────────────────────────────

def _q(text: str, answer) -> dict:
    q = text if text.endswith("?") else f"{text} = ?"
    return {"question": q, "answer": str(answer)}


def _fmt(f: Fraction) -> str:
    return str(f.numerator) if f.denominator == 1 else f"{f.numerator}/{f.denominator}"


# ── generators ───────────────────────────────────────────────────────────────

def _fraction_of_whole_unit(difficulty: float) -> dict:
    denom = random.choice([2, 4] if difficulty < 1.5 else [2, 3, 4])
    k = random.randint(1, 6 if difficulty < 1.5 else 10)
    names = {2: "חצי", 3: "שליש", 4: "רבע"}
    return _q(f"{names[denom]} מ-{denom * k}", k)


def _fraction_of_whole_non_unit(difficulty: float) -> dict:
    pairs = [(2, 3), (3, 4)] if difficulty < 3.5 else [(2, 3), (3, 4), (2, 5), (3, 5), (3, 8)]
    num, denom = random.choice(pairs)
    k = random.randint(1, 8 if difficulty < 3.5 else 12)
    return _q(f"{num}/{denom} מ-{denom * k}", num * k)


def _compare_fractions(difficulty: float) -> dict:
    pool = [2, 3, 4, 5] if difficulty < 5.5 else [2, 3, 4, 5, 6, 8, 10]
    d1, d2 = random.sample(pool, 2)
    n1, n2 = random.randint(1, d1 - 1), random.randint(1, d2 - 1)
    f1, f2 = Fraction(n1, d1), Fraction(n2, d2)
    if f1 == f2:
        return _compare_fractions(difficulty)
    bigger = f"{n1}/{d1}" if f1 > f2 else f"{n2}/{d2}"
    return {
        "question": "מה גדול יותר?",
        "answer": bigger,
        "choices": [f"{n1}/{d1}", "=", f"{n2}/{d2}"],
    }


def _equivalent_fractions(difficulty: float) -> dict:
    d1 = random.choice([2, 3, 4, 5])
    n1 = random.randint(1, d1 - 1)
    mult = random.randint(2, 4 if difficulty < 7.5 else 5)
    return {"question": f"{n1}/{d1} = ?/{d1 * mult}", "answer": str(n1 * mult)}


def _add_same_denom(difficulty: float) -> dict:
    denom = random.randint(2, 8 if difficulty < 9.5 else 12)
    a, b = random.randint(1, denom - 1), random.randint(1, denom - 1)
    return _q(f"{a}/{denom} + {b}/{denom}", _fmt(Fraction(a, denom) + Fraction(b, denom)))


def _subtract_same_denom(difficulty: float) -> dict:
    denom = random.randint(2, 8 if difficulty < 11.5 else 12)
    a, b = random.randint(1, denom - 1), random.randint(1, denom - 1)
    big, small = max(a, b), min(a, b)
    if big == small:
        small = max(1, small - 1)
    return _q(f"{big}/{denom} − {small}/{denom}", _fmt(Fraction(big, denom) - Fraction(small, denom)))


def _add_sub_diff_denom(difficulty: float) -> dict:
    d1, d2 = random.sample([2, 3, 4, 5, 6], 2)
    n1, n2 = random.randint(1, d1 - 1), random.randint(1, d2 - 1)
    f1, f2 = Fraction(n1, d1), Fraction(n2, d2)
    op = random.choice(["+", "−"])
    if op == "−" and f1 < f2:
        n1, n2, d1, d2, f1, f2 = n2, n1, d2, d1, f2, f1
    result = f1 + f2 if op == "+" else f1 - f2
    return _q(f"{n1}/{d1} {op} {n2}/{d2}", _fmt(result))


def _multiply_fractions(difficulty: float) -> dict:
    top = 5 if difficulty < 15.5 else 8
    d1, d2 = random.randint(2, top), random.randint(2, top)
    n1, n2 = random.randint(1, d1 - 1), random.randint(1, d2 - 1)
    return _q(f"{n1}/{d1} × {n2}/{d2}", _fmt(Fraction(n1, d1) * Fraction(n2, d2)))


def _divide_fractions(difficulty: float) -> dict:
    d1, d2 = random.randint(2, 5), random.randint(2, 5)
    n1, n2 = random.randint(1, d1 - 1), random.randint(1, d2 - 1)
    return _q(f"{n1}/{d1} ÷ {n2}/{d2}", _fmt(Fraction(n1, d1) / Fraction(n2, d2)))


def _three_fractions(difficulty: float) -> dict:
    if difficulty < 19.5:
        denom = random.randint(3, 8)
        nums = [random.randint(1, denom - 1) for _ in range(3)]
        result = sum(Fraction(n, denom) for n in nums)
        lhs = " + ".join(f"{n}/{denom}" for n in nums)
    else:
        denoms = random.sample([2, 3, 4, 5, 6], 3)
        nums = [random.randint(1, d - 1) for d in denoms]
        result = sum(Fraction(n, d) for n, d in zip(nums, denoms))
        lhs = " + ".join(f"{n}/{d}" for n, d in zip(nums, denoms))
    return _q(lhs, _fmt(result))
