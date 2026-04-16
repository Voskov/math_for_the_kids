"""
Tier 1 arithmetic problem generator.
Produces problems algorithmically — no storage, no AI.

Difficulty map:
  1–2   single-digit add/subtract
  3–4   two-digit add/subtract
  5–6   multiplication/division (tables up to 10)
  7–8   three-digit add/subtract; two-digit × single-digit
  9–10  two-step expressions (a op b op c)
  11–12 multi-step with parentheses
  13–14 squares and square roots (perfect)
  15–16 fractions: same denominator
  17–18 fractions: different denominators
  19–20 early algebra: find x (linear, one variable)
"""

import random
from fractions import Fraction


def generate(difficulty: float) -> dict:
    """Return {"question": str, "answer": str, "difficulty": float}"""
    d = int(difficulty)
    if d <= 2:
        return _add_sub_single(difficulty)
    if d <= 4:
        return _add_sub_two_digit(difficulty)
    if d <= 6:
        return _mul_div_tables(difficulty)
    if d <= 8:
        return _add_sub_three_digit_or_mixed(difficulty)
    if d <= 10:
        return _two_step(difficulty)
    if d <= 12:
        return _parentheses_expr(difficulty)
    if d <= 14:
        return _squares_roots(difficulty)
    if d <= 16:
        return _fractions_same_denom(difficulty)
    if d <= 18:
        return _fractions_diff_denom(difficulty)
    return _find_x(difficulty)


# ── helpers ─────────────────────────────────────────────────────────────────

def _q(text: str, answer) -> dict:
    q = text if text.endswith("?") else f"{text} = ?"
    return {"question": q, "answer": str(answer)}


def _add_sub_single(difficulty: float) -> dict:
    a, b = random.randint(1, 9), random.randint(1, 9)
    if random.random() < 0.5:
        return _q(f"{a} + {b}", a + b)
    big, small = max(a, b), min(a, b)
    return _q(f"{big} − {small}", big - small)


def _add_sub_two_digit(difficulty: float) -> dict:
    lo, hi = (10, 50) if difficulty < 3.5 else (10, 99)
    a, b = random.randint(lo, hi), random.randint(lo, hi)
    if random.random() < 0.5:
        return _q(f"{a} + {b}", a + b)
    big, small = max(a, b), min(a, b)
    return _q(f"{big} − {small}", big - small)


def _mul_div_tables(difficulty: float) -> dict:
    a, b = random.randint(2, 10), random.randint(2, 10)
    if random.random() < 0.5:
        return _q(f"{a} × {b}", a * b)
    product = a * b
    return _q(f"{product} ÷ {a}", b)


def _add_sub_three_digit_or_mixed(difficulty: float) -> dict:
    if difficulty < 7.5:
        a, b = random.randint(100, 999), random.randint(10, 200)
        big, small = max(a, b), min(a, b)
        return _q(f"{big} − {small}", big - small) if random.random() < 0.5 else _q(f"{a} + {b}", a + b)
    # two-digit × single-digit
    a, b = random.randint(11, 99), random.randint(2, 9)
    if random.random() < 0.5:
        return _q(f"{a} × {b}", a * b)
    # division with no remainder
    product = a * b
    return _q(f"{product} ÷ {b}", a)


def _two_step(difficulty: float) -> dict:
    ops = ["+", "−", "×"]
    op1, op2 = random.choices(ops, k=2)
    a = random.randint(2, 15)
    b = random.randint(2, 12)
    c = random.randint(2, 12)
    expr = f"{a} {op1} {b} {op2} {c}"
    # evaluate left-to-right (no precedence for display simplicity at this level)
    val_ab = _eval_op(a, b, op1)
    if val_ab is None:
        return _two_step(difficulty)  # retry if division produced non-integer
    result = _eval_op(val_ab, c, op2)
    if result is None:
        return _two_step(difficulty)
    return _q(expr, result)


def _parentheses_expr(difficulty: float) -> dict:
    a = random.randint(2, 20)
    b = random.randint(2, 15)
    c = random.randint(2, 10)
    inner = _eval_op(a, b, "+")
    outer_op = random.choice(["×", "−"])
    result = _eval_op(inner, c, outer_op)
    if result is None or result < 0:
        return _parentheses_expr(difficulty)
    return _q(f"({a} + {b}) {outer_op} {c}", result)


def _squares_roots(difficulty: float) -> dict:
    n = random.randint(2, 15) if difficulty < 13.5 else random.randint(2, 20)
    if random.random() < 0.5:
        return _q(f"{n}²", n * n)
    return _q(f"√{n * n}", n)


def _fractions_same_denom(difficulty: float) -> dict:
    denom = random.randint(2, 10)
    a = random.randint(1, denom - 1)
    b = random.randint(1, denom - 1)
    op = random.choice(["+", "−"])
    fa, fb = Fraction(a, denom), Fraction(b, denom)
    result = fa + fb if op == "+" else (fa - fb if fa >= fb else fb - fa)
    lhs = f"{a}/{denom} {op} {b}/{denom}" if fa >= fb or op == "+" else f"{b}/{denom} {op} {a}/{denom}"
    return _q(lhs, str(result) if result.denominator != 1 else str(result.numerator))


def _fractions_diff_denom(difficulty: float) -> dict:
    d1, d2 = random.randint(2, 6), random.randint(2, 6)
    if d1 == d2:
        d2 += 1
    a, b = random.randint(1, d1 - 1), random.randint(1, d2 - 1)
    fa, fb = Fraction(a, d1), Fraction(b, d2)
    op = random.choice(["+", "−"])
    result = fa + fb if op == "+" else (fa - fb if fa >= fb else fb - fa)
    lhs = f"{a}/{d1} {op} {b}/{d2}" if fa >= fb or op == "+" else f"{b}/{d2} {op} {a}/{d1}"
    return _q(lhs, str(result) if result.denominator != 1 else str(result.numerator))


def _find_x(difficulty: float) -> dict:
    # ax + b = c  (a in 1..5, b in 1..20, x in 1..15)
    a = random.randint(1, 5)
    x = random.randint(1, 15)
    b = random.randint(1, 20)
    c = a * x + b
    return _q(f"{a}x + {b} = {c}  →  x = ?", x)


def _eval_op(a, b, op: str):
    if op == "+":
        return a + b
    if op == "−":
        return a - b if a >= b else None
    if op == "×":
        return a * b
    if op == "÷":
        return a // b if b != 0 and a % b == 0 else None
    return None
