import { useState } from "react";
import { api, type Kid } from "../api";
import { S } from "../strings";

type Category = "math" | "language" | "trivia";

interface Topic {
  id: string;
  label: string;
  desc: string;
  emoji: string;
  category: Category;
  forGrades?: string[];
}

const TOPICS: Topic[] = [
  { id: "arithmetic", label: S.topicArithmetic, desc: S.topicArithmeticDesc, emoji: "🔢", category: "math" },
  { id: "sequences", label: S.topicSequences, desc: S.topicSequencesDesc, emoji: "📈", category: "math" },
  { id: "word_problems", label: S.topicWordProblems, desc: S.topicWordProblemsDesc, emoji: "📖", category: "math" },
  { id: "fractions", label: S.topicFractions, desc: S.topicFractionsDesc, emoji: "½", category: "math" },
  { id: "clock", label: S.topicClock, desc: S.topicClockDesc, emoji: "🕐", category: "trivia" },
  { id: "powers", label: S.topicPowers, desc: S.topicPowersDesc, emoji: "xⁿ", category: "math", forGrades: ["1st", "2nd"] },
  { id: "hebrew_letters", label: S.topicHebrewLetters, desc: S.topicHebrewLettersDesc, emoji: "🔤", category: "language", forGrades: ["preschool"] },
  { id: "trivia", label: S.topicTrivia, desc: S.topicTriviaDesc, emoji: "🌍", category: "trivia", forGrades: ["1st", "2nd"] },
  { id: "countries", label: S.topicCountries, desc: S.topicCountriesDesc, emoji: "🗺️", category: "trivia", forGrades: ["1st", "2nd"] },
];

const CATEGORY_ORDER: Category[] = ["math", "language", "trivia"];
const CATEGORY_LABEL: Record<Category, string> = {
  math: S.categoryMath,
  language: S.categoryLanguage,
  trivia: S.categoryTrivia,
};
const CATEGORY_EMOJI: Record<Category, string> = {
  math: "🧮",
  language: "🔤",
  trivia: "🌍",
};
const CATEGORY_DESC: Record<Category, (n: number) => string> = {
  math: (n) => `${n} נושאים`,
  language: (n) => `${n} נושאים`,
  trivia: (n) => `${n} נושאים`,
};

interface Props {
  kid: Kid;
  onStart: (topic: string, sessionId: number) => void;
  onBack: () => void;
}

export default function TopicSelect({ kid, onStart, onBack }: Props) {
  const [loading, setLoading] = useState(false);
  const [selectedCategory, setSelectedCategory] = useState<Category | null>(null);

  async function handleStart(topicId: string) {
    setLoading(true);
    try {
      const session = await api.startSession(kid.id, topicId);
      onStart(topicId, session.id);
    } finally {
      setLoading(false);
    }
  }

  const visible = TOPICS.filter((t) => !t.forGrades || t.forGrades.includes(kid.starting_grade));
  const grouped: Record<Category, Topic[]> = { math: [], language: [], trivia: [] };
  visible.forEach((t) => grouped[t.category].push(t));

  const onCategoryBack = () => setSelectedCategory(null);

  return (
    <div style={styles.container}>
      <div style={styles.header}>
        <button
          style={styles.backBtn}
          onClick={selectedCategory === null ? onBack : onCategoryBack}
        >
          → {S.back}
        </button>
        <span style={styles.kidBadge}>
          {kid.avatar_emoji} {kid.name}
        </span>
      </div>

      {selectedCategory === null ? (
        <>
          <h2 style={styles.title}>{S.chooseTopicTitle}</h2>
          <div style={styles.grid}>
            {CATEGORY_ORDER.map((cat) => {
              const count = grouped[cat].length;
              const empty = count === 0;
              return (
                <button
                  key={cat}
                  style={{ ...styles.card, ...(empty ? styles.cardDisabled : null) }}
                  onClick={() => !empty && setSelectedCategory(cat)}
                  disabled={empty}
                >
                  <span style={styles.emoji}>{CATEGORY_EMOJI[cat]}</span>
                  <span style={styles.label}>{CATEGORY_LABEL[cat]}</span>
                  <span style={styles.desc}>
                    {empty ? S.comingSoon : CATEGORY_DESC[cat](count)}
                  </span>
                </button>
              );
            })}
          </div>
        </>
      ) : (
        <>
          <h2 style={styles.title}>{CATEGORY_LABEL[selectedCategory]}</h2>
          <div style={styles.grid}>
            {grouped[selectedCategory].map((t) => (
              <button
                key={t.id}
                style={styles.card}
                onClick={() => handleStart(t.id)}
                disabled={loading}
              >
                <span style={styles.emoji}>{t.emoji}</span>
                <span style={styles.label}>{t.label}</span>
                <span style={styles.desc}>{t.desc}</span>
              </button>
            ))}
          </div>
        </>
      )}
    </div>
  );
}

const styles: Record<string, React.CSSProperties> = {
  container: { maxWidth: 500, width: "100%" },
  header: { display: "flex", justifyContent: "space-between", alignItems: "center", marginBottom: 32 },
  backBtn: {
    background: "none",
    color: "var(--primary)",
    fontWeight: 600,
    fontSize: 15,
    padding: "6px 0",
  },
  kidBadge: { fontSize: 18, fontWeight: 600 },
  title: { fontSize: 24, fontWeight: 700, marginBottom: 24, textAlign: "center" },
  grid: { display: "flex", flexDirection: "column", gap: 16 },
  card: {
    display: "flex",
    flexDirection: "column",
    alignItems: "flex-start",
    gap: 6,
    padding: "20px 24px",
    background: "var(--surface)",
    border: "2px solid var(--border)",
    borderRadius: "var(--radius)",
    boxShadow: "var(--shadow)",
    textAlign: "right",
    width: "100%",
  },
  cardDisabled: {
    opacity: 0.5,
    cursor: "not-allowed",
    border: "2px dashed var(--border)",
    boxShadow: "none",
  },
  emoji: { fontSize: 32 },
  label: { fontSize: 20, fontWeight: 600 },
  desc: { fontSize: 14, color: "var(--text-muted)" },
};
