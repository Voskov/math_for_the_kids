import { useEffect, useState } from "react";
import { api, type Kid } from "../api";
import { S } from "../strings";

interface Props {
  onSelect: (kid: Kid) => void;
  onAdmin?: () => void;
}

export default function KidSelect({ onSelect, onAdmin }: Props) {
  const [kids, setKids] = useState<Kid[]>([]);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    const includeSpecial = sessionStorage.getItem("showSpecialKids") === "1";
    api.getKids(includeSpecial).then(setKids).catch(() => setError("לא ניתן להתחבר לשרת"));
  }, []);

  return (
    <div style={styles.container}>
      {onAdmin && (
        <button
          onClick={onAdmin}
          style={styles.adminBtn}
          aria-label="admin"
          title="admin"
        >
          ⚙
        </button>
      )}
      <h1 style={styles.title}>{S.appTitle}</h1>
      <p style={styles.subtitle}>{S.chooseKid}</p>

      {error && <p style={styles.error}>{error}</p>}

      <div style={styles.grid}>
        {kids.map((kid) => (
          <button key={kid.id} style={styles.card} onClick={() => onSelect(kid)}>
            <span style={styles.avatar}>{kid.avatar_emoji}</span>
            <span style={styles.name}>{kid.name}</span>
            <span style={styles.level}>
              {S.level}: {kid.levels.length ? Math.floor(kid.levels.reduce((sum, l) => sum + l.difficulty_level, 0) / kid.levels.length) : 0}
            </span>
          </button>
        ))}
      </div>
    </div>
  );
}

const styles: Record<string, React.CSSProperties> = {
  container: { textAlign: "center", maxWidth: 500, width: "100%", position: "relative" },
  adminBtn: {
    position: "absolute",
    top: 0,
    insetInlineStart: 0,
    background: "none",
    color: "var(--text-muted)",
    fontSize: 18,
    opacity: 0.35,
    padding: 4,
    cursor: "pointer",
  },
  title: { fontSize: 32, fontWeight: 700, marginBottom: 8 },
  subtitle: { fontSize: 20, color: "var(--text-muted)", marginBottom: 40 },
  error: { color: "var(--error)", marginBottom: 16 },
  grid: { display: "flex", gap: 20, justifyContent: "center", flexWrap: "wrap" },
  card: {
    display: "flex",
    flexDirection: "column",
    alignItems: "center",
    gap: 10,
    padding: "28px 32px",
    background: "var(--surface)",
    border: "2px solid var(--border)",
    borderRadius: "var(--radius)",
    boxShadow: "var(--shadow)",
    cursor: "pointer",
    minWidth: 130,
    transition: "border-color 0.15s, box-shadow 0.15s",
  },
  avatar: { fontSize: 52 },
  name: { fontSize: 20, fontWeight: 600 },
  level: { fontSize: 14, color: "var(--text-muted)" },
};
