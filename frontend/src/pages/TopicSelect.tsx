import { useState } from "react";
import { api, type Kid } from "../api";
import { S } from "../strings";

interface Topic {
  id: string;
  label: string;
  desc: string;
  emoji: string;
}

const TOPICS: Topic[] = [
  { id: "arithmetic", label: S.topicArithmetic, desc: S.topicArithmeticDesc, emoji: "🔢" },
];

interface Props {
  kid: Kid;
  onStart: (topic: string, sessionId: number) => void;
  onBack: () => void;
}

export default function TopicSelect({ kid, onStart, onBack }: Props) {
  const [loading, setLoading] = useState(false);

  async function handleStart(topicId: string) {
    setLoading(true);
    try {
      const session = await api.startSession(kid.id, topicId);
      onStart(topicId, session.id);
    } finally {
      setLoading(false);
    }
  }

  return (
    <div style={styles.container}>
      <div style={styles.header}>
        <button style={styles.backBtn} onClick={onBack}>
          → {S.back}
        </button>
        <span style={styles.kidBadge}>
          {kid.avatar_emoji} {kid.name}
        </span>
      </div>

      <h2 style={styles.title}>{S.chooseTopicTitle}</h2>

      <div style={styles.grid}>
        {TOPICS.map((t) => (
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
  emoji: { fontSize: 32 },
  label: { fontSize: 20, fontWeight: 600 },
  desc: { fontSize: 14, color: "var(--text-muted)" },
};
