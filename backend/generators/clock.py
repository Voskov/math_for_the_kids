"""
Clock reading topic.

Difficulty bands (1-20):
  1-3   read hours-only (clock at H:00, MC of hour numbers)
  4-6   read minutes-only (hour fixed, minute varies, MC of minute numbers)
  7-9   read full time (half/quarter hours, MC of "H:MM")
  10-12 read full time (5-min steps, MC of "H:MM")
  13-15 pick clock (digital text -> MC of analog clocks)
  16-18 add hours/minutes (clock + delta -> MC of "H:MM")
  19-20 elapsed time (two clocks -> MC of duration "H:MM")

Question encoding (consumed by frontend):
  clock-read|H:MM         -> render single clock, choices are time strings
  clock-readH|H:MM        -> hours-only single clock, choices are bare hour numbers
  clock-readM|H:MM        -> minutes-only single clock, choices are bare minute numbers
  clock-pick|H:MM         -> render digital text, choices are time strings (each rendered as clock)
  clock-add|H:MM|+H:MM    -> render clock + delta text, choices are time strings
  clock-elapsed|H:MM|H:MM -> render two clocks, choices are duration strings
"""
import random


def _fmt(h: int, m: int) -> str:
    return f"{h}:{m:02d}"


def _add_minutes(h: int, m: int, delta_h: int, delta_m: int) -> tuple[int, int]:
    total = h * 60 + m + delta_h * 60 + delta_m
    total %= 12 * 60
    return total // 60, total % 60


def _elapsed(h1: int, m1: int, h2: int, m2: int) -> tuple[int, int]:
    diff = (h2 * 60 + m2) - (h1 * 60 + m1)
    if diff < 0:
        diff += 12 * 60
    return diff // 60, diff % 60


def _hour_distractors(target: int, n: int) -> list[int]:
    pool = [h for h in range(1, 13) if h != target]
    near = [h for h in [target - 1, target + 1, target - 2, target + 2]
            if 1 <= h <= 12 and h != target]
    selected = near[:n]
    if len(selected) < n:
        remaining = [h for h in pool if h not in selected]
        selected += random.sample(remaining, min(n - len(selected), len(remaining)))
    return selected


def _minute_distractors(target: int, step: int, n: int) -> list[int]:
    pool = list(range(0, 60, step))
    others = [m for m in pool if m != target]
    if len(others) <= n:
        return others
    return random.sample(others, n)


def _time_distractors(h: int, m: int, step: int, n: int) -> list[tuple[int, int]]:
    seen = {(h, m)}
    out: list[tuple[int, int]] = []
    attempts = 0
    while len(out) < n and attempts < 50:
        attempts += 1
        dh = random.choice([-2, -1, 0, 1, 2])
        dm = random.choice([-step * 2, -step, 0, step, step * 2])
        nh, nm = _add_minutes(h, m, dh, dm)
        if (nh, nm) in seen:
            continue
        if nh == 0:
            nh = 12
        seen.add((nh, nm))
        out.append((nh, nm))
    while len(out) < n:
        nh = random.randint(1, 12)
        nm = random.choice(range(0, 60, step))
        if (nh, nm) not in seen:
            seen.add((nh, nm))
            out.append((nh, nm))
    return out


def _duration_distractors(target_min: int, n: int) -> list[int]:
    candidates = [15, 30, 45, 60, 75, 90, 105, 120, 150, 180]
    others = [c for c in candidates if c != target_min]
    near = sorted(others, key=lambda c: abs(c - target_min))[:n + 2]
    return random.sample(near, min(n, len(near)))


def _fmt_dur(total_min: int) -> str:
    return f"{total_min // 60}:{total_min % 60:02d}"


def generate(difficulty: float) -> dict:
    d = int(difficulty)

    # Band 1-3: hours-only read
    if d <= 3:
        h = random.randint(1, 12)
        distractors = _hour_distractors(h, 3)
        choices = [str(h)] + [str(x) for x in distractors]
        random.shuffle(choices)
        return {
            "question": f"clock-readH|{_fmt(h, 0)}",
            "answer": str(h),
            "choices": choices,
        }

    # Band 4-6: minutes-only read
    if d <= 6:
        h = random.randint(1, 12)
        step = 15 if d <= 5 else 5
        m = random.choice(range(0, 60, step))
        distractors = _minute_distractors(m, step, 3)
        choices = [str(m)] + [str(x) for x in distractors]
        random.shuffle(choices)
        return {
            "question": f"clock-readM|{_fmt(h, m)}",
            "answer": str(m),
            "choices": choices,
        }

    # Band 7-9: full read, half/quarter
    if d <= 9:
        h = random.randint(1, 12)
        m = random.choice([0, 15, 30, 45])
        distractors = _time_distractors(h, m, 15, 3)
        correct = _fmt(h, m)
        choices = [correct] + [_fmt(dh, dm) for dh, dm in distractors]
        random.shuffle(choices)
        return {
            "question": f"clock-read|{correct}",
            "answer": correct,
            "choices": choices,
        }

    # Band 10-12: full read, 5-min steps
    if d <= 12:
        h = random.randint(1, 12)
        m = random.choice(range(0, 60, 5))
        distractors = _time_distractors(h, m, 5, 3)
        correct = _fmt(h, m)
        choices = [correct] + [_fmt(dh, dm) for dh, dm in distractors]
        random.shuffle(choices)
        return {
            "question": f"clock-read|{correct}",
            "answer": correct,
            "choices": choices,
        }

    # Band 13-15: pick clock (digital -> analog MC)
    if d <= 15:
        h = random.randint(1, 12)
        step = 15 if d <= 14 else 5
        m = random.choice(range(0, 60, step))
        distractors = _time_distractors(h, m, step, 3)
        correct = _fmt(h, m)
        choices = [correct] + [_fmt(dh, dm) for dh, dm in distractors]
        random.shuffle(choices)
        return {
            "question": f"clock-pick|{correct}",
            "answer": correct,
            "choices": choices,
        }

    # Band 16-18: add hours/minutes
    if d <= 18:
        h = random.randint(1, 11)
        if d <= 16:
            m = 0
            delta_h = random.randint(1, 4)
            delta_m = 0
        elif d == 17:
            m = random.choice([0, 15, 30, 45])
            delta_h = 0
            delta_m = random.choice([15, 30, 45])
        else:
            m = random.choice(range(0, 60, 5))
            delta_h = random.randint(0, 2)
            delta_m = random.choice([5, 10, 15, 20, 25, 35, 40, 50])
        ah, am = _add_minutes(h, m, delta_h, delta_m)
        if ah == 0:
            ah = 12
        correct = _fmt(ah, am)
        step = 15 if d <= 17 else 5
        distractors = _time_distractors(ah, am, step, 3)
        choices = [correct] + [_fmt(dh, dm) for dh, dm in distractors]
        random.shuffle(choices)
        return {
            "question": f"clock-add|{_fmt(h, m)}|+{delta_h}:{delta_m:02d}",
            "answer": correct,
            "choices": choices,
        }

    # Band 19-20: elapsed time
    h1 = random.randint(1, 10)
    m1 = random.choice(range(0, 60, 5))
    delta_min = random.choice([15, 30, 45, 60, 75, 90, 105, 120])
    h2_total = h1 * 60 + m1 + delta_min
    h2 = (h2_total // 60) % 12
    m2 = h2_total % 60
    if h2 == 0:
        h2 = 12
    eh, em = _elapsed(h1, m1, h2, m2)
    correct_min = eh * 60 + em
    distractors = _duration_distractors(correct_min, 3)
    correct = _fmt_dur(correct_min)
    choices = [correct] + [_fmt_dur(x) for x in distractors]
    random.shuffle(choices)
    return {
        "question": f"clock-elapsed|{_fmt(h1, m1)}|{_fmt(h2, m2)}",
        "answer": correct,
        "choices": choices,
    }
