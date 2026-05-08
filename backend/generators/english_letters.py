"""
English letter recognition for Ben (preschool).

Difficulty map:
  1–2   A B C — 3 choices, Type A only
  3–6   + D–I — 4 choices, mix A / C
  7–10  + J–O — mix A / C
  11–16 + P–X — mix A / C / D
  17–20 all 26 — mix A / B / C / D

Type A: emoji → pick letter       (question=emoji, tts_word=English word)
Type B: letter → pick emoji       (question=letter, tts_word=letter name)
Type C: letter name → pick letter (question=letter name, tts_word=letter name)
Type D: English word → pick first letter (question=word, tts_word=word)
"""
import random

_WORD_BANK: dict[str, list[tuple[str, str]]] = {
    "A": [("Apple", "🍎"), ("Ant", "🐜"), ("Airplane", "✈️"), ("Alligator", "🐊")],
    "B": [("Ball", "⚽"), ("Bear", "🐻"), ("Butterfly", "🦋"), ("Banana", "🍌")],
    "C": [("Cat", "🐱"), ("Cake", "🎂"), ("Car", "🚗"), ("Cow", "🐄")],
    "D": [("Dog", "🐕"), ("Duck", "🦆"), ("Dinosaur", "🦕"), ("Donut", "🍩")],
    "E": [("Elephant", "🐘"), ("Egg", "🥚"), ("Earth", "🌍"), ("Eagle", "🦅")],
    "F": [("Fish", "🐟"), ("Frog", "🐸"), ("Flower", "🌸"), ("Fox", "🦊")],
    "G": [("Giraffe", "🦒"), ("Grapes", "🍇"), ("Guitar", "🎸"), ("Ghost", "👻")],
    "H": [("Horse", "🐴"), ("Heart", "❤️"), ("Hat", "🎩"), ("House", "🏠")],
    "I": [("Ice cream", "🍦"), ("Island", "🏝️"), ("Igloo", "🧊")],
    "J": [("Jellyfish", "🪼"), ("Jar", "🫙"), ("Juice", "🧃")],
    "K": [("Kite", "🪁"), ("Kangaroo", "🦘"), ("Key", "🔑"), ("Koala", "🐨")],
    "L": [("Lion", "🦁"), ("Lemon", "🍋"), ("Leaf", "🍃"), ("Ladybug", "🐞")],
    "M": [("Moon", "🌙"), ("Mouse", "🐭"), ("Monkey", "🐒"), ("Mushroom", "🍄")],
    "N": [("Nest", "🪺"), ("Nose", "👃"), ("Nut", "🥜"), ("Needle", "🪡")],
    "O": [("Orange", "🍊"), ("Octopus", "🐙"), ("Owl", "🦉"), ("Onion", "🧅")],
    "P": [("Pizza", "🍕"), ("Penguin", "🐧"), ("Pig", "🐷"), ("Pear", "🍐")],
    "Q": [("Queen", "👸"), ("Question", "❓")],
    "R": [("Rainbow", "🌈"), ("Rabbit", "🐰"), ("Rocket", "🚀"), ("Rose", "🌹")],
    "S": [("Sun", "☀️"), ("Star", "⭐"), ("Snake", "🐍"), ("Strawberry", "🍓")],
    "T": [("Tiger", "🐯"), ("Train", "🚂"), ("Tree", "🌳"), ("Turtle", "🐢")],
    "U": [("Umbrella", "☂️"), ("Unicorn", "🦄")],
    "V": [("Violin", "🎻"), ("Volcano", "🌋"), ("Van", "🚐")],
    "W": [("Whale", "🐋"), ("Wolf", "🐺"), ("Watermelon", "🍉"), ("Worm", "🪱")],
    "X": [("X-ray", "🩻")],
    "Y": [("Yarn", "🧶"), ("Yak", "🐃"), ("Yo-yo", "🪀")],
    "Z": [("Zebra", "🦓"), ("Zero", "0️⃣")],
}

_LETTER_NAMES: dict[str, str] = {
    "A": "Ay", "B": "Bee", "C": "See", "D": "Dee", "E": "Ee",
    "F": "Ef", "G": "Jee", "H": "Aych", "I": "Eye", "J": "Jay",
    "K": "Kay", "L": "El", "M": "Em", "N": "En", "O": "Oh",
    "P": "Pee", "Q": "Kyoo", "R": "Ar", "S": "Es", "T": "Tee",
    "U": "Yoo", "V": "Vee", "W": "Double-U", "X": "Eks", "Y": "Why",
    "Z": "Zee",
}

_SEQUENCE = list("ABCDEFGHIJKLMNOPQRSTUVWXYZ")

_CONFUSABLE: dict[str, list[str]] = {
    "B": ["D", "P"], "D": ["B", "Q"], "P": ["Q", "B"], "Q": ["P", "D"],
    "M": ["N", "W"], "N": ["M", "U"], "U": ["N", "V"], "V": ["U", "W"],
    "W": ["M", "V"],
}


def _pool(d: int) -> list[str]:
    thresholds = [2,  4,  6,  8, 10, 12, 14, 16]
    counts =     [3,  6,  9, 12, 15, 18, 21, 24]
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

    if d <= 2:
        qtype = "A"
    elif d <= 6:
        qtype = random.choice(["A", "A", "C"])
    elif d <= 10:
        qtype = random.choice(["A", "C"])
    elif d <= 16:
        qtype = random.choice(["A", "C", "D"])
    else:
        qtype = random.choice(["A", "B", "C", "D"])

    if qtype == "A":
        choices = [letter] + dist_letters
        random.shuffle(choices)
        return {"question": emoji, "answer": letter, "choices": choices, "tts_word": word}

    if qtype == "B":
        dist_emojis = [random.choice(_WORD_BANK[l])[1] for l in dist_letters]
        choices = [emoji] + dist_emojis
        random.shuffle(choices)
        return {"question": letter, "answer": emoji, "choices": choices, "tts_word": _LETTER_NAMES[letter]}

    if qtype == "C":
        name = _LETTER_NAMES[letter]
        choices = [letter] + dist_letters
        random.shuffle(choices)
        return {"question": name, "answer": letter, "choices": choices, "tts_word": name}

    # Type D: English word → pick first letter
    choices = [letter] + dist_letters
    random.shuffle(choices)
    return {"question": word, "answer": letter, "choices": choices, "tts_word": word}
