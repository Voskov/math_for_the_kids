"""
Hebrew letter recognition for Ben (preschool).

Difficulty map:
  1–10  growing letter pool — 3–4 choices, Type A only
  11–16 + more letters — mix A / D
  17–20 all 22 letters — mix A / B / D

Type A: emoji → pick letter             (question=emoji, tts_word=Hebrew word)
Type B: letter → pick emoji            (question=letter, tts_word=letter name)
Type D: Hebrew word → pick first letter (question=word, tts_word=word)
"""
import random

_WORD_BANK: dict[str, list[tuple[str, str]]] = {
    "א": [("ארנב", "🐰"), ("אריה", "🦁"), ("אוטובוס", "🚌"), ("אבטיח", "🍉"), ("אננס", "🍍")],
    "ב": [("בית", "🏠"), ("בלון", "🎈"), ("בננה", "🍌"), ("ברבור", "🦢"), ("בקבוק", "🍼")],
    "ג": [("גמל", "🐪"), ("גזר", "🥕"), ("גלידה", "🍦"), ("גורילה", "🦍")],
    "ד": [("דג", "🐟"), ("דוב", "🐻"), ("דלת", "🚪"), ("דינוזאור", "🦕")],
    "ה": [("היפופוטם", "🦛"), ("הר", "🏔️"), ("הודו", "🦃"), ("המבורגר", "🍔"), ("הלוכית", "🐌")],
    "ו": [("ורד", "🌹"), ("ווי", "🪝"), ("ופל", "🧇")],
    "ז": [("זאב", "🐺"), ("זבוב", "🪰"), ("זית", "🫒"), ("זיקית", "🦎")],
    "ח": [("חתול", "🐱"), ("חמור", "🫏"), ("חמניה", "🌻"), ("חיפושית", "🪲"), ("חלון", "🪟")],
    "ט": [("טלה", "🐑"), ("טלפון", "📱"), ("טווס", "🦚"), ("טירה", "🏰"), ("טבעת", "💍")],
    "י": [("יד", "✋"), ("ירח", "🌙"), ("ינשוף", "🦉"), ("יונה", "🕊️")],
    "כ": [("כלב", "🐕"), ("כוכב", "⭐"), ("כוס", "🥤"), ("כדור", "⚽")],
    "ל": [("לב", "❤️"), ("לוויתן", "🐋"), ("לחם", "🍞"), ("לימון", "🍋")],
    "מ": [("מכונית", "🚗"), ("מטוס", "✈️"), ("מנורה", "💡"), ("מסוק", "🚁")],
    "נ": [("נמר", "🐆"), ("נחש", "🐍"), ("נר", "🕯️"), ("נסיכה", "👸")],
    "ס": [("סוס", "🐴"), ("ספר", "📚"), ("סנאי", "🐿️"), ("סירה", "⛵")],
    "ע": [("עץ", "🌳"), ("עכבר", "🐭"), ("ענב", "🍇")],
    "פ": [("פרח", "🌸"), ("פרפר", "🦋"), ("פיל", "🐘"), ("פינגווין", "🐧")],
    "צ": [("צב", "🐢"), ("צפרדע", "🐸"), ("צבי", "🦌"), ("צלחת", "🍽️")],
    "ק": [("קוף", "🐒"), ("קיפוד", "🦔"), ("קשת", "🌈"), ("קלמר", "🦑"), ("קנגורו", "🦘")],
    "ר": [("רכבת", "🚂"), ("רובוט", "🤖"), ("רקטה", "🚀"), ("רגל", "🦶"), ("רוח", "💨")],
    "ש": [("שמש", "☀️"), ("שוקולד", "🍫"), ("שן", "🦷"), ("שפן", "🐇")],
    "ת": [("תפוח", "🍎"), ("תות", "🍓"), ("תרנגול", "🐓"), ("תמנון", "🐙")],
}

_LETTER_NAMES: dict[str, str] = {
    "א": "אלף", "ב": "בית", "ג": "גימל", "ד": "דלת", "ה": "הא",
    "ו": "וו", "ז": "זין", "ח": "חית", "ט": "טית", "י": "יוד",
    "כ": "כף", "ל": "למד", "מ": "מם", "נ": "נון", "ס": "סמך",
    "ע": "עין", "פ": "פא", "צ": "צדי", "ק": "קוף", "ר": "ריש",
    "ש": "שין", "ת": "תו",
}

_SEQUENCE = ["א", "ב", "ג", "ד", "ה", "ו", "ז", "ח", "ט", "י",
             "כ", "ל", "מ", "נ", "ס", "ע", "פ", "צ", "ק", "ר", "ש", "ת"]

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
    dist_letters = _distractors(letter, pool, choice_count - 1, d)

    if d <= 10:
        qtype = "A"
    elif d <= 16:
        qtype = random.choice(["A", "D"])
    else:
        qtype = random.choice(["A", "B", "D"])

    if qtype == "A":
        choices = [letter] + dist_letters
        random.shuffle(choices)
        return {"question": emoji, "answer": letter, "choices": choices, "tts_word": word}

    if qtype == "B":
        dist_emojis = [random.choice(_WORD_BANK[l])[1] for l in dist_letters]
        choices = [emoji] + dist_emojis
        random.shuffle(choices)
        return {"question": letter, "answer": emoji, "choices": choices, "tts_word": _LETTER_NAMES[letter]}

    # Type D: Hebrew word → pick first letter
    choices = [letter] + dist_letters
    random.shuffle(choices)
    return {"question": word, "answer": letter, "choices": choices, "tts_word": word}
