"""
ELO-like adaptive difficulty engine.

Difficulty scale: 1.0 – 20.0 (floats, so changes are gradual)
Scoring per answer:
  correct + fast  (< 15s)  → +2
  correct + slow  (15-45s) → +1
  wrong                    → -2

Promote at +6 accumulated; demote at -4; reset accumulator on level change.
"""

PROMOTE_THRESHOLD = 6.0
DEMOTE_THRESHOLD = -4.0
MIN_DIFFICULTY = 1.0
MAX_DIFFICULTY = 20.0

SCORE_CORRECT_FAST = 2.0
SCORE_CORRECT_SLOW = 1.0
SCORE_WRONG = -2.0
FAST_THRESHOLD_S = 15.0
SLOW_THRESHOLD_S = 45.0


def compute_score(is_correct: bool, time_taken_s: float | None) -> float:
    if not is_correct:
        return SCORE_WRONG
    t = time_taken_s or SLOW_THRESHOLD_S
    return SCORE_CORRECT_FAST if t < FAST_THRESHOLD_S else SCORE_CORRECT_SLOW


def update_level(
    difficulty_level: float,
    score_accumulator: float,
    is_correct: bool,
    time_taken_s: float | None,
) -> tuple[float, float]:
    """
    Returns (new_difficulty_level, new_score_accumulator).
    """
    delta = compute_score(is_correct, time_taken_s)
    new_acc = score_accumulator + delta

    if new_acc >= PROMOTE_THRESHOLD:
        new_level = min(difficulty_level + 1.0, MAX_DIFFICULTY)
        return new_level, 0.0

    if new_acc <= DEMOTE_THRESHOLD:
        new_level = max(difficulty_level - 1.0, MIN_DIFFICULTY)
        return new_level, 0.0

    return difficulty_level, new_acc
