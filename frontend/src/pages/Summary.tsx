import { useEffect, useState } from "react";
import { api, type SessionSummary } from "../api";
import { S } from "../strings";

interface Props {
  sessionId: number;
  durationSeconds: number;
  onPlayAgain: () => void;
  onHome: () => void;
}

export default function Summary({ sessionId, durationSeconds, onPlayAgain, onHome }: Props) {
  const [summary, setSummary] = useState<SessionSummary | null>(null);

  useEffect(() => {
    api.getSummary(sessionId).then(setSummary);
  }, [sessionId]);

  if (!summary) return <p style={{ color: "var(--text-muted)" }}>...</p>;

  return (
    <div style={styles.container}>
      <h2 style={styles.title}>{S.summaryTitle}</h2>
      <p style={styles.kidName}>{summary.kid_name}</p>

      <div style={styles.statsRow}>
        <div style={styles.stat}>
          <span style={styles.statNum}>{summary.correct}</span>
          <span style={styles.statLabel}>נכון</span>
        </div>
        <div style={styles.stat}>
          <span style={styles.statNum}>{summary.total - summary.correct}</span>
          <span style={styles.statLabel}>שגוי</span>
        </div>
        <div style={styles.stat}>
          <span style={styles.statNum}>{summary.accuracy_pct}%</span>
          <span style={styles.statLabel}>דיוק</span>
        </div>
        <div style={styles.stat}>
          <span style={styles.statNum}>{S.formatDuration(durationSeconds)}</span>
          <span style={styles.statLabel}>{S.duration}</span>
        </div>
      </div>

      <div style={styles.problemList}>
        {summary.problems.map((p, i) => (
          <div
            key={i}
            style={{
              ...styles.problemRow,
              borderRight: `4px solid ${p.is_correct ? "var(--success)" : "var(--error)"}`,
            }}
          >
            <span style={styles.problemQ}>{p.question_text}</span>
            <span style={{ color: p.is_correct ? "var(--success)" : "var(--error)", fontWeight: 600 }}>
              {p.kid_answer ?? "—"}
            </span>
            {!p.is_correct && (
              <span style={styles.correctAns}>({p.correct_answer})</span>
            )}
            {p.time_taken_s != null && (
              <span style={styles.timeTaken}>{p.time_taken_s.toFixed(1)}s</span>
            )}
          </div>
        ))}
      </div>

      <div style={styles.actions}>
        <button style={styles.primaryBtn} onClick={onPlayAgain}>
          {S.playAgain}
        </button>
        <button style={styles.secondaryBtn} onClick={onHome}>
          {S.goHome}
        </button>
      </div>
    </div>
  );
}

const styles: Record<string, React.CSSProperties> = {
  container: { maxWidth: 520, width: "100%" },
  title: { fontSize: 28, fontWeight: 700, textAlign: "center", marginBottom: 4 },
  kidName: { fontSize: 18, textAlign: "center", color: "var(--text-muted)", marginBottom: 24 },
  statsRow: {
    display: "flex",
    gap: 16,
    justifyContent: "center",
    marginBottom: 28,
  },
  stat: {
    display: "flex",
    flexDirection: "column",
    alignItems: "center",
    background: "var(--surface)",
    border: "2px solid var(--border)",
    borderRadius: "var(--radius)",
    padding: "16px 24px",
    minWidth: 90,
  },
  statNum: { fontSize: 28, fontWeight: 700 },
  statLabel: { fontSize: 13, color: "var(--text-muted)" },
  problemList: {
    display: "flex",
    flexDirection: "column",
    gap: 8,
    marginBottom: 28,
    maxHeight: 300,
    overflowY: "auto",
  },
  problemRow: {
    display: "flex",
    gap: 12,
    alignItems: "center",
    background: "var(--surface)",
    padding: "10px 16px",
    borderRadius: 8,
    fontSize: 15,
  },
  problemQ: { flex: 1, direction: "ltr", fontFamily: "monospace", fontSize: 16 },
  correctAns: { fontSize: 13, color: "var(--text-muted)" },
  timeTaken: { fontSize: 12, color: "var(--text-muted)", marginLeft: "auto" },
  actions: { display: "flex", gap: 12, justifyContent: "center" },
  primaryBtn: {
    padding: "12px 28px",
    background: "var(--primary)",
    color: "#fff",
    borderRadius: 8,
    fontWeight: 700,
    fontSize: 16,
  },
  secondaryBtn: {
    padding: "12px 28px",
    background: "var(--surface)",
    color: "var(--text)",
    border: "2px solid var(--border)",
    borderRadius: 8,
    fontWeight: 600,
    fontSize: 16,
  },
};
