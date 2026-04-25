"""
Hebrew word problem generator.
Arithmetic wrapped in short Hebrew story sentences — no AI, pure templates.

Difficulty map:
  1–2   single-digit add/subtract
  3–4   two-digit add/subtract
  5–6   multiplication/division (tables up to 10)
  7–8   three-digit add/subtract; two-digit × single-digit
  9–10  two-step problems (add+sub, mul+add)
  11–12 two-step with larger numbers
  13–14 two-step with multiplication and subtraction
  15–16 three-quantity problems
  17–18 two-digit × two-digit with extra step
  19–20 multi-step complex
"""

import random


def generate(difficulty: float) -> dict:
    d = int(difficulty)
    if d <= 2:
        return _add_sub_single()
    if d <= 4:
        return _add_sub_two_digit()
    if d <= 6:
        return _mul_div_tables()
    if d <= 8:
        return _add_sub_large_or_mul()
    if d <= 10:
        return _two_step_easy()
    if d <= 12:
        return _two_step_medium()
    if d <= 14:
        return _two_step_mul_add()
    if d <= 16:
        return _three_quantity()
    if d <= 18:
        return _two_step_large_mul()
    return _multi_step()


# ── helpers ──────────────────────────────────────────────────────────────────

def _q(text: str, answer: int) -> dict:
    return {"question": text, "answer": str(answer)}


def _pick(templates: list) -> tuple:
    return random.choice(templates)


# ── single-digit add / subtract ──────────────────────────────────────────────

_ADD_SUB_SINGLE = [
    (
        "לתום יש {a} מדבקות ולאדם יש {b} מדבקות. כמה מדבקות יש להם ביחד?",
        lambda a, b: a + b,
    ),
    (
        "בסל יש {a} תפוחים. הוסיפו עוד {b} תפוחים. כמה תפוחים יש בסל עכשיו?",
        lambda a, b: a + b,
    ),
    (
        "היו {a} ממתקים בקופסה. אכלתי {b} ממתקים. כמה ממתקים נשארו?",
        lambda a, b: a - b,
    ),
    (
        "עלו {a} ציפורים על ענף. עפו {b} ציפורים. כמה ציפורים נשארו?",
        lambda a, b: a - b,
    ),
]


def _add_sub_single() -> dict:
    tmpl, fn = _pick(_ADD_SUB_SINGLE)
    if "נשארו" in tmpl or "נשארו" in tmpl:
        a = random.randint(3, 9)
        b = random.randint(1, a - 1)
    else:
        a, b = random.randint(1, 9), random.randint(1, 9)
    return _q(tmpl.format(a=a, b=b), fn(a, b))


# ── two-digit add / subtract ─────────────────────────────────────────────────

_ADD_SUB_TWO = [
    (
        "בספרייה יש {a} ספרים בעברית ו-{b} ספרים באנגלית. כמה ספרים יש בספרייה בסך הכל?",
        lambda a, b: a + b,
        "add",
    ),
    (
        "ביום ראשון ירד {a} מ\"מ גשם. ביום שני ירד עוד {b} מ\"מ. כמה מ\"מ גשם ירד בסך הכל?",
        lambda a, b: a + b,
        "add",
    ),
    (
        "היו {a} תלמידים בבית הספר. {b} תלמידים היו חולים. כמה תלמידים באו לבית הספר?",
        lambda a, b: a - b,
        "sub",
    ),
    (
        "לתום היו {a} שקלים. הוא קנה ספר ב-{b} שקלים. כמה שקלים נשארו לו?",
        lambda a, b: a - b,
        "sub",
    ),
]


def _add_sub_two_digit() -> dict:
    tmpl, fn, kind = _pick(_ADD_SUB_TWO)
    if kind == "sub":
        a = random.randint(20, 90)
        b = random.randint(10, a - 5)
    else:
        a, b = random.randint(10, 70), random.randint(10, 70)
    return _q(tmpl.format(a=a, b=b), fn(a, b))


# ── multiplication / division ────────────────────────────────────────────────

_MUL_DIV = [
    (
        "בכל קופסה יש {a} צבעים. יש {b} קופסות. כמה צבעים יש בסך הכל?",
        lambda a, b: a * b,
        "mul",
    ),
    (
        "לכל ילד יש {a} מדבקות. יש {b} ילדים. כמה מדבקות יש בסך הכל?",
        lambda a, b: a * b,
        "mul",
    ),
    (
        "בכל שורה יש {a} כסאות. יש {b} שורות. כמה כסאות יש בכיתה?",
        lambda a, b: a * b,
        "mul",
    ),
    (
        "{a} ממתקים מחולקים שווה בשווה בין {b} ילדים. כמה ממתקים מקבל כל ילד?",
        lambda a, b: a // b,
        "div",
    ),
    (
        "יש {a} ביסקויטים. רוצים לארוז {b} ביסקויטים בכל שקית. כמה שקיות אפשר למלא?",
        lambda a, b: a // b,
        "div",
    ),
]


def _mul_div_tables() -> dict:
    tmpl, fn, kind = _pick(_MUL_DIV)
    if kind == "div":
        b = random.randint(2, 9)
        a = b * random.randint(2, 10)
    else:
        a, b = random.randint(2, 9), random.randint(2, 9)
    return _q(tmpl.format(a=a, b=b), fn(a, b))


# ── three-digit add/sub or two-digit × single ────────────────────────────────

_LARGE = [
    (
        "בעיר גרים {a} אנשים. עברו לגור בה עוד {b} אנשים. כמה אנשים גרים בעיר עכשיו?",
        lambda a, b: a + b,
        "add",
    ),
    (
        "בחנות היו {a} פריטים. נמכרו {b} פריטים. כמה פריטים נשארו בחנות?",
        lambda a, b: a - b,
        "sub",
    ),
    (
        "בכל אוטובוס יש {a} נוסעים. נסעו {b} אוטובוסים. כמה נוסעים נסעו בסך הכל?",
        lambda a, b: a * b,
        "mul",
    ),
]


def _add_sub_large_or_mul() -> dict:
    tmpl, fn, kind = _pick(_LARGE)
    if kind == "mul":
        a, b = random.randint(11, 50), random.randint(2, 9)
    elif kind == "sub":
        a = random.randint(200, 900)
        b = random.randint(50, a - 50)
    else:
        a, b = random.randint(100, 800), random.randint(50, 300)
    return _q(tmpl.format(a=a, b=b), fn(a, b))


# ── two-step: add then subtract (easy) ──────────────────────────────────────

_TWO_STEP_EASY = [
    (
        "היו {a} ילדים בגן. הגיעו עוד {b} ילדים. אחר כך הלכו {c} ילדים הביתה. כמה ילדים נשארו בגן?",
        lambda a, b, c: a + b - c,
    ),
    (
        "לתום היו {a} מדבקות. קיבל עוד {b} מדבקות. נתן {c} מדבקות לאחיו. כמה מדבקות יש לו עכשיו?",
        lambda a, b, c: a + b - c,
    ),
    (
        "בעץ ישבו {a} ציפורים. עפו עוד {b} ציפורים ובאו לשבת. אחר כך עפו {c} ציפורים. כמה ציפורים נשארו?",
        lambda a, b, c: a + b - c,
    ),
]


def _two_step_easy() -> dict:
    tmpl, fn = _pick(_TWO_STEP_EASY)
    a = random.randint(5, 20)
    b = random.randint(3, 15)
    c = random.randint(1, a + b - 2)
    return _q(tmpl.format(a=a, b=b, c=c), fn(a, b, c))


# ── two-step: add then subtract (medium, larger numbers) ────────────────────

def _two_step_medium() -> dict:
    tmpl, fn = _pick(_TWO_STEP_EASY)
    a = random.randint(20, 80)
    b = random.randint(10, 40)
    c = random.randint(5, a + b - 5)
    return _q(tmpl.format(a=a, b=b, c=c), fn(a, b, c))


# ── two-step: multiply then add or subtract ──────────────────────────────────

_TWO_STEP_MUL = [
    (
        "קנינו {b} חבילות. בכל חבילה יש {a} עוגיות. מצאנו עוד {c} עוגיות בבית. כמה עוגיות יש בסך הכל?",
        lambda a, b, c: a * b + c,
    ),
    (
        "בכל שקית יש {a} סוכריות. קנינו {b} שקיות. אכלנו {c} סוכריות. כמה סוכריות נשארו?",
        lambda a, b, c: a * b - c,
    ),
    (
        "בכל קרון יש {a} נוסעים. לרכבת יש {b} קרונות. ירדו {c} נוסעים בתחנה. כמה נוסעים נשארו ברכבת?",
        lambda a, b, c: a * b - c,
    ),
]


def _two_step_mul_add() -> dict:
    tmpl, fn = _pick(_TWO_STEP_MUL)
    a = random.randint(3, 9)
    b = random.randint(3, 9)
    product = a * b
    if "נשארו" in tmpl:
        c = random.randint(1, product - 1)
    else:
        c = random.randint(1, 20)
    result = fn(a, b, c)
    if result <= 0:
        return _two_step_mul_add()
    return _q(tmpl.format(a=a, b=b, c=c), result)


# ── three quantities ─────────────────────────────────────────────────────────

_THREE_Q = [
    (
        "לתום יש {a} כדורים, לאדם יש {b} כדורים ולבן יש {c} כדורים. כמה כדורים יש להם ביחד?",
        lambda a, b, c: a + b + c,
    ),
    (
        "בכיתה א יש {a} תלמידים, בכיתה ב יש {b} תלמידים ובכיתה ג יש {c} תלמידים. כמה תלמידים יש בסך הכל?",
        lambda a, b, c: a + b + c,
    ),
    (
        "בחנות היו {a} חולצות. נמכרו {b} חולצות ביום ראשון ועוד {c} חולצות ביום שני. כמה חולצות נשארו?",
        lambda a, b, c: a - b - c,
    ),
]


def _three_quantity() -> dict:
    tmpl, fn = _pick(_THREE_Q)
    if "נשארו" in tmpl:
        a = random.randint(50, 200)
        b = random.randint(5, a // 3)
        c = random.randint(5, a // 3)
        while b + c >= a:
            b, c = random.randint(5, a // 3), random.randint(5, a // 3)
    else:
        a, b, c = random.randint(10, 60), random.randint(10, 60), random.randint(10, 60)
    return _q(tmpl.format(a=a, b=b, c=c), fn(a, b, c))


# ── two-step with larger multiplication ─────────────────────────────────────

def _two_step_large_mul() -> dict:
    tmpl, fn = _pick(_TWO_STEP_MUL)
    a = random.randint(11, 30)
    b = random.randint(3, 9)
    product = a * b
    if "נשארו" in tmpl:
        c = random.randint(10, product - 10)
    else:
        c = random.randint(5, 50)
    result = fn(a, b, c)
    if result <= 0:
        return _two_step_large_mul()
    return _q(tmpl.format(a=a, b=b, c=c), result)


# ── multi-step complex ───────────────────────────────────────────────────────

_MULTI = [
    (
        "בכל קופסה יש {a} עפרונות. יש {b} קופסות. לאחר מכן נוספו {c} עפרונות ונלקחו {d} עפרונות. כמה עפרונות יש עכשיו?",
        lambda a, b, c, d: a * b + c - d,
    ),
    (
        "לתום יש {a} שקלים. לאדם יש פי {b} יותר. ביחד הם קנו משהו ב-{c} שקלים. כמה שקלים נשארו להם?",
        lambda a, b, c: a + a * b - c,
    ),
]


def _multi_step() -> dict:
    tmpl, fn = _pick(_MULTI)
    if "{d}" in tmpl:
        a, b = random.randint(5, 15), random.randint(4, 9)
        product = a * b
        c = random.randint(5, 20)
        d = random.randint(5, product + c - 5)
        result = fn(a, b, c, d)
        if result <= 0:
            return _multi_step()
        return _q(tmpl.format(a=a, b=b, c=c, d=d), result)
    else:
        a = random.randint(10, 30)
        b = random.randint(2, 5)
        total = a + a * b
        c = random.randint(10, total - 10)
        result = fn(a, b, c)
        if result <= 0:
            return _multi_step()
        return _q(tmpl.format(a=a, b=b, c=c), result)
