"""
Hebrew letter recognition for Ben (preschool).

Difficulty map:
  1–2   א ב ג — 3 choices, show emoji → pick letter
  3–4   + ד ה — 4 choices
  5–6   + ו ז ח
  7–8   + ט י כ
  9–10  + ל מ נ
  11–12 + ס ע פ
  13–14 + צ ק ר
  15–16 + ש ת (all 22)
  17–18 all 22, mix Type A (emoji→letter) and Type B (letter→emoji)
  19–20 all 22, prefer visually confusable distractors

Type A: question = emoji, choices = Hebrew letters, tts_word = Hebrew word
Type B: question = Hebrew letter, choices = emoji, tts_word = letter name
"""
import random

# (word, emoji) pairs per letter — used as question/distractor material
_WORD_BANK: dict[str, list[tuple[str, str]]] = {
    "א": [("ארנב", "🐰"), ("אריה", "🦁"), ("אוטובוס", "🚌")],
    "ב": [("בית", "🏠"), ("בלון", "🎈"), ("בננה", "🍌")],
    "ג": [("גמל", "🐪"), ("גזר", "🥕"), ("גלידה", "🍦")],
    "ד": [("דג", "🐟"), ("דוב", "🐻"), ("דלת", "🚪")],
    "ה": [("היפופוטם", "🦛"), ("הר", "🏔️")],
    "ו": [("ורד", "🌹"), ("וילון", "🪟")],
    "ז": [("זאב", "🐺"), ("זבוב", "🪰"), ("זית", "🫒")],
    "ח": [("חתול", "🐱"), ("חמור", "🫏"), ("חמניה", "🌻")],
    "ט": [("טלה", "🐑"), ("טלפון", "📱")],
    "י": [("יד", "✋"), ("ירח", "🌙"), ("ינשוף", "🦉")],
    "כ": [("כלב", "🐕"), ("כוכב", "⭐"), ("כוס", "🥤")],
    "ל": [("לב", "❤️"), ("לוויתן", "🐋"), ("לחם", "🍞")],
    "מ": [("מכונית", "🚗"), ("מטוס", "✈️"), ("מנורה", "💡")],
    "נ": [("נמר", "🐆"), ("נחש", "🐍"), ("נר", "🕯️")],
    "ס": [("סוס", "🐴"), ("ספר", "📚"), ("סנאי", "🐿️")],
    "ע": [("עץ", "🌳"), ("עכבר", "🐭"), ("עיט", "🦅")],
    "פ": [("פרח", "🌸"), ("פרפר", "🦋"), ("פיל", "🐘")],
    "צ": [("צב", "🐢"), ("צפרדע", "🐸"), ("צבי", "🦌")],
    "ק": [("קוף", "🐒"), ("קיפוד", "🦔")],
    "ר": [("רכבת", "🚂"), ("רובוט", "🤖")],
    "ש": [("שמש", "☀️"), ("שוקולד", "🍫"), ("שן", "🦷")],
    "ת": [("תפוח", "🍎"), ("תות", "🍓"), ("תרנגול", "🐓")],
}

_LETTER_NAMES: dict[str, str] = {
    "א": "אלף", "ב": "בית", "ג": "גימל", "ד": "דלת", "ה": "הא",
    "ו": "וו", "ז": "זין", "ח": "חית", "ט": "טית", "י": "יוד",
    "כ": "כף", "ל": "למד", "מ": "מם", "נ": "נון", "ס": "סמך",
    "ע": "עין", "פ": "פא", "צ": "צדי", "ק": "קוף", "ר": "ריש",
    "ש": "שין", "ת": "תו",
}

# Letters introduced in order of difficulty
_SEQUENCE = ["א", "ב", "ג", "ד", "ה", "ו", "ז", "ח", "ט", "י",
             "כ", "ל", "מ", "נ", "ס", "ע", "פ", "צ", "ק", "ר", "ש", "ת"]

# Letters that look visually similar — used for hard distractors at levels 19–20
_CONFUSABLE: dict[str, list[str]] = {
    "ב": ["כ", "ד"], "כ": ["ב", "נ"], "ד": ["ר", "ב"], "ר": ["ד", "ו"],
    "ו": ["ז", "י"], "ז": ["ו", "י"], "ח": ["ה", "ת"], "ה": ["ח", "ת"],
    "ת": ["ח", "ה"], "מ": ["ס", "ע"], "ס": ["מ", "ע"],
}


def _pool(d: int) -> list[str]:
    thresholds = [2,  4,  6,  8,  10, 12, 14, 16]
    counts =     [3,  5,  8,  11, 14, 17, 20, 22]
    for threshold, count in zip(thresholds, counts):
        if d <= threshold:
            return _SEQUENCE[:count]
    return _SEQUENCE[:]


def _distractors(target: str, pool: list[str], n: int, d: int) -> list[str]:
    others = [l for l in pool if l != target]
    if d >= 19:
        preferred = [l for l in _CONFUSABLE.get(target, []) if l in others]
        selected = preferred[:n]
        if len(selected) < n:
            remaining = [l for l in others if l not in selected]
            selected += random.sample(remaining, min(n - len(selected), len(remaining)))
    else:
        selected = random.sample(others, min(n, len(others)))
    return selected


def generate(difficulty: float) -> dict:
    d = int(difficulty)
    pool = _pool(d)
    choice_count = 3 if d <= 2 else 4

    letter = random.choice(pool)
    word, emoji = random.choice(_WORD_BANK[letter])

    type_b = d >= 17 and random.random() < 0.5

    if not type_b:
        dist_letters = _distractors(letter, pool, choice_count - 1, d)
        choices = [letter] + dist_letters
        random.shuffle(choices)
        return {"question": emoji, "answer": letter, "choices": choices, "tts_word": word}
    else:
        dist_letters = _distractors(letter, pool, choice_count - 1, d)
        dist_emojis = [random.choice(_WORD_BANK[l])[1] for l in dist_letters]
        choices = [emoji] + dist_emojis
        random.shuffle(choices)
        return {"question": letter, "answer": emoji, "choices": choices, "tts_word": _LETTER_NAMES[letter]}
