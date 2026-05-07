"""
ELO-like adaptive difficulty engine.

Difficulty scale: 1.0 – 20.0 (floats, so changes are gradual)

Each session mixes problem levels: 70% at kid's level (N), 20% at N-1, 10% at N+1.
The score per answer is weighted by offset = problem_level - kid_level:
  correct: base * (1 + 0.5 * offset)   easier=less reward, harder=more reward
  wrong:   base * (1 - 0.5 * offset)   easier wrong=harsher, harder wrong=lighter

Base scoring:
  correct + fast  (< 15s)  → +2
  correct + slow  (15-45s) → +1
  wrong                    → -1

Promote at +40 accumulated; demote at -32; reset accumulator on level change.
Negative accumulator clears at session start (clean slate per session).
"""

from loguru import logger

PROMOTE_THRESHOLD = 40.0
DEMOTE_THRESHOLD = -32.0
MIN_DIFFICULTY = 1.0
MAX_DIFFICULTY = 20.0

SCORE_CORRECT_FAST = 2.0
SCORE_CORRECT_SLOW = 1.0
SCORE_WRONG = -1.0
FAST_THRESHOLD_S = 15.0
SLOW_THRESHOLD_S = 45.0

OFFSET_WEIGHT = 0.5


def compute_score(
    is_correct: bool,
    time_taken_s: float | None,
    level_offset: int = 0,
) -> float:
    if not is_correct:
        return SCORE_WRONG * (1.0 - OFFSET_WEIGHT * level_offset)
    t = time_taken_s or SLOW_THRESHOLD_S
    base = SCORE_CORRECT_FAST if t < FAST_THRESHOLD_S else SCORE_CORRECT_SLOW
    return base * (1.0 + OFFSET_WEIGHT * level_offset)


def update_level(
    difficulty_level: float,
    score_accumulator: float,
    is_correct: bool,
    time_taken_s: float | None,
    problem_level: float | None = None,
) -> tuple[float, float]:
    """
    Returns (new_difficulty_level, new_score_accumulator).
    `problem_level` is the difficulty the problem was actually generated at;
    if omitted, treated as equal to the kid's level (no offset weighting).
    """
    offset = 0
    if problem_level is not None:
        offset = int(round(problem_level - difficulty_level))
    delta = compute_score(is_correct, time_taken_s, offset)
    new_acc = score_accumulator + delta

    logger.debug(
        f"score_calc: level={difficulty_level}, acc={score_accumulator}, "
        f"correct={is_correct}, time={time_taken_s}s, offset={offset}, delta={delta}, new_acc={new_acc}"
    )

    if new_acc >= PROMOTE_THRESHOLD:
        new_level = min(difficulty_level + 1.0, MAX_DIFFICULTY)
        logger.info(f"PROMOTE: level {difficulty_level} → {new_level} (acc={new_acc} >= {PROMOTE_THRESHOLD})")
        return new_level, 0.0

    if new_acc <= DEMOTE_THRESHOLD:
        new_level = max(difficulty_level - 1.0, MIN_DIFFICULTY)
        logger.warning(f"DEMOTE: level {difficulty_level} → {new_level} (acc={new_acc} <= {DEMOTE_THRESHOLD})")
        return new_level, 0.0

    return difficulty_level, new_acc
