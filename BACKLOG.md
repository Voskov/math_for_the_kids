# Backlog

Last updated: 2026-04-29

## Math

### Shipped
- **arithmetic** (חשבון) — add, subtract, multiply, divide, fractions, algebra (difficulty 1–20)
- **sequences** (סדרות מספרים) — fill-in-the-missing-number, difficulty 1–20
- **word_problems** (בעיות מילוליות) — Hebrew story problems, ~20 templates, difficulty 1–20 (2026-04-25)
- **fractions** (שברים) — recognition, comparison, arithmetic, difficulty 1–20

### Backlog
- [ ] **Comparisons & Ordering** (השוואה וסדר) — sort numbers smallest→largest; needs multi-input or drag-and-drop UI
- [ ] **Clock Reading** (שעון) — analog clock face; needs SVG clock rendering
- [ ] **Geometry** — area, perimeter, angles
- [ ] **More word problem templates (Tier 2)** — Hebrew templates with variable slots

## Language

Prerequisite for both items below: multiple-choice UI mode in Session (currently free-text only). See Infrastructure.

### Shipped
- **hebrew_letters** (אותיות) — Hebrew letter recognition, preschool-only (Ben), emoji + TTS, two problem types A/B (2026-04-27)

### Backlog
- [ ] **Sentence Completion** (השלמת משפטים) — fill missing word(s); static question bank (~100+, graded). Do first — simpler.
- [ ] **Word Analogies** (יחסי מלים) — A:B :: C:? reasoning; static question bank. Do after Sentence Completion.

## Trivia / General Knowledge

### Backlog
- [ ] **Trivia** (ידע כללי) — e.g. "מי היה אלברט איינשטיין?"; age-tier difficulty (preschool / 1st / 2nd grade) instead of ELO 1–20; 4-option multiple-choice
  - Generation: free UI prompting (Claude.ai / ChatGPT) + manual import first; Ollama (local, free) for bulk later

## Infrastructure / Cross-cutting

### Shipped
- **Session timer** — client-side, shown on Summary (2026-04-26)
- **Admin dashboard** — per-kid level history (recent)
- **Per-kid topic visibility** — `forGrades` filter in TopicSelect
- **TTS** — browser `speechSynthesis`, `he-IL` (currently hebrew_letters only)

### Backlog
- [ ] **Multiple-choice UI in Session** — unblocks Language category + Trivia
- [ ] **BankQuestion DB table** — pre-generated questions, shared by word_problems + trivia, 4-option MC
- [ ] **Live timer in session header** — currently only on Summary
- [ ] **Real images for hebrew_letters** — replace emoji in `_WORD_BANK` (`backend/generators/hebrew_letters.py`); render `<img>` in `Session.tsx`. Candidate source: totcards.com
- [ ] **Kid profile editor UI** — names + avatars (currently hardcoded seed)
- [ ] **Claude API hints** — "צריך עזרה?" button → Socratic hint in Hebrew
- [ ] **Audio for all topics** — extend TTS beyond hebrew_letters; read problems aloud
- [ ] **Weekly session summary** — parent report
- [ ] **Challenge mode** — timed session, harder problems
- [ ] **PWA / offline support**
