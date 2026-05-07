# Backlog

Last updated: 2026-05-07

## Bugs (HIGH PRIORITY)

- [ ] **Kids dropping levels unexpectedly** — kids report level decreases, cause unknown. Investigate `backend/adaptive.py` (−2 on wrong, demote at −16) + check level-history in admin dashboard. Repro: pull recent `KidTopicLevel` history, correlate with `SessionProblem` outcomes. Hypothesis: demote threshold too aggressive, or wrong-answer penalty stacking inside one session.

### Fixed
- **Repeated problems within session** (2026-04-30) — `GET /problems/next` now re-rolls up to 10× against existing `SessionProblem.question_text` for the session

## Math

### Shipped
- **arithmetic** (חשבון) — add, subtract, multiply, divide, fractions, algebra (difficulty 1–20)
- **sequences** (סדרות מספרים) — fill-in-the-missing-number, difficulty 1–20
- **word_problems** (בעיות מילוליות) — Hebrew story problems, ~20 templates, difficulty 1–20 (2026-04-25)
- **fractions** (שברים) — recognition, comparison, arithmetic, difficulty 1–20
- **powers** (חזקות) — squares, cubes, powers of 10, mixed expr, reverse `?²=n`, higher exponents; gated to 1st/2nd grade (2026-04-29)

### Backlog
- [ ] **Comparisons & Ordering** (השוואה וסדר) — sort numbers smallest→largest; needs multi-input or drag-and-drop UI
- [ ] **Clock Reading** (שעון) — analog clock face; needs SVG clock rendering
- [ ] **Geometry** — area, perimeter, angles
- [ ] **More word problem templates (Tier 2)** — Hebrew templates with variable slots

## Language

### Shipped
- **hebrew_letters** (אותיות) — Hebrew letter recognition, preschool-only (Ben), emoji + TTS, two problem types A/B (2026-04-27)

### Backlog
- [ ] **English Letters** (אותיות אנגלית) — direct parallel to `hebrew_letters`; Ben only (preschool); 26 letters A–Z; same 4 problem types: emoji→letter, letter→emoji, letter name→letter, word→first letter; emoji word bank per letter; confusable pairs (b/d, p/q, m/n, u/n). Do first — near-zero infra cost.
- [ ] **Sight Words** (מילים נפוצות באנגלית) — Dolch pre-primer + primer list (~40–80 words); see/read word via TTS, pick correct word from 4 choices; Ben + 1st grade. Do after English Letters.
- [ ] **Rhyming** (חרוזים באנגלית) — hear/read a word, pick which of 4 rhymes; 1st/2nd grade; static bank.
- [ ] **Spelling** (כתיב) — hear word via TTS, type it; open-text input; 2nd grade only.
- [ ] **Sentence Completion** (השלמת משפטים) — fill missing word(s); static question bank (~100+, graded). Do first — simpler.
- [ ] **Word Analogies** (יחסי מלים) — A:B :: C:? reasoning; static question bank. Do after Sentence Completion.

## Trivia / General Knowledge

### Shipped
- **trivia** (ידע כללי) — famous people; 4-option MC; bank in `backend/generators/trivia_bank/{direct,clue}.json` seeded into `BankQuestion` table on startup; difficulty 5 (direct) / 12 (clue) / 18+ swaps in cross-bank distractors; cross-session no-repeat per kid; gated to 1st/2nd grade (2026-04-30). ~47 Q to start; expand via Ollama later.

### Backlog
- [ ] **Countries & Capitals** (מדינות ובירות) — new trivia subtopic. Source bank: `countries/countries_capitals_trivia.json` (25 Hebrew Q's, types `capital_to_country` / `country_to_capital`, 4-option MC). Reuse `BankQuestion` table + existing trivia MC flow; decide whether to fold into existing `trivia` topic or split as separate topic in TopicSelect. Gate to 1st/2nd grade.

## Infrastructure / Cross-cutting

### Shipped
- **Session timer** — client-side, shown on Summary (2026-04-26)
- **Admin dashboard** — per-kid level history (recent)
- **Per-kid topic visibility** — `forGrades` filter in TopicSelect
- **TTS** — browser `speechSynthesis`, `he-IL` (currently hebrew_letters only)
- **Multiple-choice UI in Session** — `choices[]` rendered as buttons; used by hebrew_letters / fractions / clock / trivia
- **BankQuestion DB table** — generic pre-generated question bank (`bank_questions`); first consumer = trivia; reusable for sentence_completion / word_analogies (2026-04-30)

### Backlog
- [ ] **Live timer in session header** — currently only on Summary
- [ ] **Real images for hebrew_letters** — replace emoji in `_WORD_BANK` (`backend/generators/hebrew_letters.py`); render `<img>` in `Session.tsx`. Candidate source: totcards.com
- [ ] **Kid profile editor UI** — names + avatars (currently hardcoded seed)
- [ ] **Claude API hints** — "צריך עזרה?" button → Socratic hint in Hebrew
- [ ] **Audio for all topics** — extend TTS beyond hebrew_letters; read problems aloud
- [ ] **Weekly session summary** — parent report
- [ ] **Challenge mode** — timed session, harder problems
- [ ] **PWA / offline support**
