"""
Powers (חזקות) problem generator.

Difficulty map:
  1–3   small squares: 2², 3², 4², 5²
  4–6   larger squares: 6²–10²
  7–9   small cubes: 2³–5³
  10–12 powers of 10: 10², 10³, 10⁴
  13–15 mixed expressions: a² + b, a² − b², a³ − k
  16–18 reverse: ?² = n   (n is a perfect square)
  19–20 higher exponents: 2⁵, 2⁶, 3⁴, 4⁴, 5³, 2⁷
"""

import random

_SUP = str.maketrans("0123456789", "⁰¹²³⁴⁵⁶⁷⁸⁹")


def _sup(n: int) -> str:
    return str(n).translate(_SUP)


def _q(text: str, answer) -> dict:
    q = text if text.endswith("?") else f"{text} = ?"
    return {"question": q, "answer": str(answer)}


def generate(difficulty: float) -> dict:
    d = int(difficulty)
    if d <= 3:
        return _small_square()
    if d <= 6:
        return _bigger_square()
    if d <= 9:
        return _small_cube()
    if d <= 12:
        return _power_of_ten()
    if d <= 15:
        return _mixed_expr()
    if d <= 18:
        return _reverse_square()
    return _higher_exponent()


def _small_square() -> dict:
    n = random.randint(2, 5)
    return _q(f"{n}{_sup(2)}", n * n)


def _bigger_square() -> dict:
    n = random.randint(6, 10)
    return _q(f"{n}{_sup(2)}", n * n)


def _small_cube() -> dict:
    n = random.randint(2, 5)
    return _q(f"{n}{_sup(3)}", n ** 3)


def _power_of_ten() -> dict:
    e = random.randint(2, 4)
    return _q(f"10{_sup(e)}", 10 ** e)


def _mixed_expr() -> dict:
    kind = random.choice(["sq_plus", "sq_minus_sq", "cube_minus"])
    if kind == "sq_plus":
        a = random.randint(2, 8)
        b = random.randint(1, 15)
        return _q(f"{a}{_sup(2)} + {b}", a * a + b)
    if kind == "sq_minus_sq":
        a = random.randint(3, 8)
        b = random.randint(1, a - 1)
        return _q(f"{a}{_sup(2)} − {b}{_sup(2)}", a * a - b * b)
    a = random.randint(2, 4)
    k = random.randint(1, 10)
    return _q(f"{a}{_sup(3)} − {k}", a ** 3 - k)


def _reverse_square() -> dict:
    n = random.randint(2, 12)
    return {"question": f"?{_sup(2)} = {n * n}", "answer": str(n)}


def _higher_exponent() -> dict:
    base, exp = random.choice([(2, 5), (2, 6), (2, 7), (3, 4), (4, 4), (5, 3)])
    return _q(f"{base}{_sup(exp)}", base ** exp)
