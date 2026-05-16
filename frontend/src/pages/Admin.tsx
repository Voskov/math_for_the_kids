import { useEffect, useMemo, useState } from "react";
import {
  CartesianGrid,
  ComposedChart,
  Line,
  ResponsiveContainer,
  Scatter,
  Tooltip,
  XAxis,
  YAxis,
} from "recharts";
import {
  api,
  type ActivityRow,
  type HistoryPoint,
  type OverviewKid,
  type SessionRow,
} from "../api";
import { S } from "../strings";

interface Props {
  onBack: () => void;
}

type Tab = "overview" | "kid" | "activity";

const TOPIC_LABEL: Record<string, string> = {
  arithmetic: S.topicArithmetic,
  sequences: S.topicSequences,
  word_problems: S.topicWordProblems,
  fractions: S.topicFractions,
  hebrew_letters: S.topicHebrewLetters,
};

function topicLabel(t: string) {
  return TOPIC_LABEL[t] ?? t;
}

function formatDate(iso: string) {
  const d = new Date(iso);
  return d.toLocaleString("he-IL", {
    day: "2-digit",
    month: "2-digit",
    hour: "2-digit",
    minute: "2-digit",
  });
}

export default function Admin({ onBack }: Props) {
  const [tab, setTab] = useState<Tab>("overview");

  return (
    <div style={styles.container}>
      <div style={styles.header}>
        <button style={styles.backBtn} onClick={onBack}>
          → {S.back}
        </button>
        <h2 style={styles.title}>{S.adminTitle}</h2>
        <span />
      </div>

      <div style={styles.tabs}>
        <TabButton active={tab === "overview"} onClick={() => setTab("overview")}>
          {S.adminTabOverview}
        </TabButton>
        <TabButton active={tab === "kid"} onClick={() => setTab("kid")}>
          {S.adminTabKid}
        </TabButton>
        <TabButton active={tab === "activity"} onClick={() => setTab("activity")}>
          {S.adminTabActivity}
        </TabButton>
      </div>

      <div style={styles.body}>
        {tab === "overview" && <OverviewTab />}
        {tab === "kid" && <KidTab />}
        {tab === "activity" && <ActivityTab />}
      </div>
    </div>
  );
}

function TabButton({
  active,
  onClick,
  children,
}: {
  active: boolean;
  onClick: () => void;
  children: React.ReactNode;
}) {
  return (
    <button
      onClick={onClick}
      style={{
        ...styles.tabBtn,
        ...(active ? styles.tabBtnActive : null),
      }}
    >
      {children}
    </button>
  );
}

function LevelCell({ kidId, topic, value, onSaved }: { kidId: number; topic: string; value: number | null; onSaved: () => void }) {
  const [editing, setEditing] = useState(false);
  const [input, setInput] = useState("");
  const [saving, setSaving] = useState(false);

  function startEdit() {
    setInput(value != null ? String(Math.floor(value)) : "");
    setEditing(true);
  }

  async function save() {
    const n = Number(input);
    if (!Number.isInteger(n) || n < 1 || n > 20) return;
    setSaving(true);
    await api.setKidTopicLevel(kidId, topic, n);
    setSaving(false);
    setEditing(false);
    onSaved();
  }

  function onKeyDown(e: React.KeyboardEvent) {
    if (e.key === "Enter") save();
    if (e.key === "Escape") setEditing(false);
  }

  if (editing) {
    return (
      <td style={styles.td}>
        <input
          autoFocus
          type="number"
          min={1}
          max={20}
          value={input}
          onChange={(e) => setInput(e.target.value)}
          onKeyDown={onKeyDown}
          onBlur={() => setEditing(false)}
          style={styles.levelInput}
          disabled={saving}
        />
      </td>
    );
  }

  return (
    <td style={{ ...styles.td, cursor: "pointer" }} onClick={startEdit} title="לחץ לשינוי">
      {value != null ? Math.floor(value) : "—"}
    </td>
  );
}

function OverviewTab() {
  const [data, setData] = useState<OverviewKid[] | null>(null);

  function load() { api.getAdminOverview().then(setData); }
  useEffect(load, []);

  const topics = useMemo(() => {
    if (!data) return [];
    const set = new Set<string>();
    data.forEach((k) => k.levels.forEach((l) => set.add(l.topic)));
    return Array.from(set);
  }, [data]);

  if (!data) return <p style={styles.muted}>…</p>;
  if (data.length === 0) return <p style={styles.muted}>{S.adminNoData}</p>;

  return (
    <div style={styles.tableWrap}>
      <table style={styles.table}>
        <thead>
          <tr>
            <th style={styles.th}>{S.adminColKid}</th>
            {topics.map((t) => (
              <th key={t} style={styles.th}>
                {topicLabel(t)}
              </th>
            ))}
            <th style={styles.th}>{S.adminColSessions}</th>
            <th style={styles.th}>{S.adminColAnswered}</th>
            <th style={styles.th}>{S.adminColAccuracy}</th>
          </tr>
        </thead>
        <tbody>
          {data.map((k) => {
            const byTopic = new Map(k.levels.map((l) => [l.topic, l.difficulty_level]));
            return (
              <tr key={k.kid_id}>
                <td style={styles.td}>
                  <span style={styles.avatar}>{k.avatar_emoji}</span> {k.name}
                </td>
                {topics.map((t) => (
                  <LevelCell
                    key={t}
                    kidId={k.kid_id}
                    topic={t}
                    value={byTopic.has(t) ? byTopic.get(t)! : null}
                    onSaved={load}
                  />
                ))}
                <td style={styles.td}>{k.total_sessions}</td>
                <td style={styles.td}>{k.total_problems_answered}</td>
                <td style={styles.td}>{k.overall_accuracy_pct}%</td>
              </tr>
            );
          })}
        </tbody>
      </table>
    </div>
  );
}

function KidTab() {
  const [overview, setOverview] = useState<OverviewKid[]>([]);
  const [kidId, setKidId] = useState<number | null>(null);
  const [topic, setTopic] = useState<string>("");
  const [history, setHistory] = useState<HistoryPoint[]>([]);
  const [sessions, setSessions] = useState<SessionRow[]>([]);

  useEffect(() => {
    api.getAdminOverview().then((d) => {
      setOverview(d);
      if (d.length > 0) {
        setKidId(d[0].kid_id);
        if (d[0].levels.length > 0) setTopic(d[0].levels[0].topic);
      }
    });
  }, []);

  useEffect(() => {
    if (kidId == null) return;
    api.getKidSessions(kidId).then(setSessions);
  }, [kidId]);

  useEffect(() => {
    if (kidId == null || !topic) return;
    api.getKidTopicHistory(kidId, topic).then(setHistory);
  }, [kidId, topic]);

  const chartData = useMemo(
    () =>
      history.map((h, i) => ({
        i,
        level: h.difficulty_at_time,
        correct: h.is_correct ? h.difficulty_at_time : null,
        wrong: h.is_correct ? null : h.difficulty_at_time,
        date: formatDate(h.asked_at),
      })),
    [history]
  );

  const kid = overview.find((k) => k.kid_id === kidId);
  const topicsForKid = kid?.levels.map((l) => l.topic) ?? [];

  return (
    <>
      <div style={styles.controls}>
        <label style={styles.controlLabel}>
          {S.adminPickKid}
          <select
            style={styles.select}
            value={kidId ?? ""}
            onChange={(e) => setKidId(Number(e.target.value))}
          >
            {overview.map((k) => (
              <option key={k.kid_id} value={k.kid_id}>
                {k.avatar_emoji} {k.name}
              </option>
            ))}
          </select>
        </label>
        <label style={styles.controlLabel}>
          {S.adminPickTopic}
          <select
            style={styles.select}
            value={topic}
            onChange={(e) => setTopic(e.target.value)}
          >
            {topicsForKid.map((t) => (
              <option key={t} value={t}>
                {topicLabel(t)}
              </option>
            ))}
          </select>
        </label>
      </div>

      <h3 style={styles.sectionTitle}>{S.adminLevelOverTime}</h3>
      <div style={styles.chartWrap}>
        {chartData.length === 0 ? (
          <p style={styles.muted}>{S.adminNoData}</p>
        ) : (
          <ResponsiveContainer width="100%" height={260}>
            <ComposedChart data={chartData} margin={{ top: 8, right: 16, bottom: 8, left: 0 }}>
              <CartesianGrid stroke="var(--border)" strokeDasharray="3 3" />
              <XAxis dataKey="i" tick={{ fontSize: 11 }} />
              <YAxis domain={[1, 20]} tick={{ fontSize: 11 }} />
              <Tooltip
                contentStyle={{ background: "var(--surface)", border: "1px solid var(--border)" }}
                labelFormatter={(_, payload) =>
                  payload && payload[0] ? (payload[0].payload as { date: string }).date : ""
                }
              />
              <Line
                type="monotone"
                dataKey="level"
                stroke="var(--primary)"
                strokeWidth={2}
                dot={false}
                isAnimationActive={false}
                name={S.adminColLevel}
              />
              <Scatter dataKey="correct" fill="var(--success)" name={S.adminCorrect} />
              <Scatter dataKey="wrong" fill="var(--error)" name={S.adminWrong} />
            </ComposedChart>
          </ResponsiveContainer>
        )}
      </div>

      <h3 style={styles.sectionTitle}>{S.adminTabActivity}</h3>
      <SessionsTable rows={sessions} highlightTopic={topic} />
    </>
  );
}

function ActivityTab() {
  const [rows, setRows] = useState<ActivityRow[] | null>(null);
  useEffect(() => {
    api.getRecentActivity().then(setRows);
  }, []);

  if (!rows) return <p style={styles.muted}>…</p>;
  if (rows.length === 0) return <p style={styles.muted}>{S.adminNoData}</p>;

  return (
    <div style={styles.tableWrap}>
      <table style={styles.table}>
        <thead>
          <tr>
            <th style={styles.th}>{S.adminColKid}</th>
            <th style={styles.th}>{S.adminColTopic}</th>
            <th style={styles.th}>{S.adminColDate}</th>
            <th style={styles.th}>{S.adminColAnswered}</th>
            <th style={styles.th}>{S.adminColAccuracy}</th>
            <th style={styles.th}>{S.adminColDuration}</th>
          </tr>
        </thead>
        <tbody>
          {rows.map((r) => (
            <tr key={r.session_id}>
              <td style={styles.td}>
                <span style={styles.avatar}>{r.avatar_emoji}</span> {r.kid_name}
              </td>
              <td style={styles.td}>{topicLabel(r.topic)}</td>
              <td style={styles.td}>{formatDate(r.started_at)}</td>
              <td style={styles.td}>
                {r.correct}/{r.total}
              </td>
              <td style={styles.td}>{r.accuracy_pct}%</td>
              <td style={styles.td}>
                {r.duration_s != null ? S.formatDuration(Math.round(r.duration_s)) : "—"}
              </td>
            </tr>
          ))}
        </tbody>
      </table>
    </div>
  );
}

function SessionsTable({ rows, highlightTopic }: { rows: SessionRow[]; highlightTopic?: string }) {
  if (rows.length === 0) return <p style={styles.muted}>{S.adminNoData}</p>;
  return (
    <div style={styles.tableWrap}>
      <table style={styles.table}>
        <thead>
          <tr>
            <th style={styles.th}>{S.adminColTopic}</th>
            <th style={styles.th}>{S.adminColDate}</th>
            <th style={styles.th}>{S.adminColAnswered}</th>
            <th style={styles.th}>{S.adminColAccuracy}</th>
            <th style={styles.th}>{S.adminColDuration}</th>
          </tr>
        </thead>
        <tbody>
          {rows.map((r) => (
            <tr
              key={r.session_id}
              style={r.topic === highlightTopic ? { background: "var(--bg)" } : undefined}
            >
              <td style={styles.td}>{topicLabel(r.topic)}</td>
              <td style={styles.td}>{formatDate(r.started_at)}</td>
              <td style={styles.td}>
                {r.correct}/{r.total}
              </td>
              <td style={styles.td}>{r.accuracy_pct}%</td>
              <td style={styles.td}>
                {r.duration_s != null ? S.formatDuration(Math.round(r.duration_s)) : "—"}
              </td>
            </tr>
          ))}
        </tbody>
      </table>
    </div>
  );
}

const styles: Record<string, React.CSSProperties> = {
  container: { maxWidth: 900, width: "100%" },
  header: {
    display: "flex",
    justifyContent: "space-between",
    alignItems: "center",
    marginBottom: 16,
  },
  backBtn: {
    background: "none",
    color: "var(--primary)",
    fontWeight: 600,
    fontSize: 15,
    padding: "6px 0",
  },
  title: { fontSize: 24, fontWeight: 700, margin: 0 },
  tabs: { display: "flex", gap: 8, marginBottom: 20, borderBottom: "1px solid var(--border)" },
  tabBtn: {
    background: "none",
    color: "var(--text-muted)",
    fontWeight: 600,
    fontSize: 15,
    padding: "10px 16px",
    borderBottom: "2px solid transparent",
    cursor: "pointer",
  },
  tabBtnActive: { color: "var(--primary)", borderBottomColor: "var(--primary)" },
  body: { display: "flex", flexDirection: "column", gap: 12 },
  tableWrap: {
    background: "var(--surface)",
    border: "1px solid var(--border)",
    borderRadius: "var(--radius)",
    overflowX: "auto",
  },
  table: { width: "100%", borderCollapse: "collapse", fontSize: 14 },
  th: {
    textAlign: "right",
    padding: "10px 12px",
    fontWeight: 600,
    color: "var(--text-muted)",
    borderBottom: "1px solid var(--border)",
    whiteSpace: "nowrap",
  },
  td: {
    padding: "10px 12px",
    borderBottom: "1px solid var(--border)",
    whiteSpace: "nowrap",
  },
  avatar: { fontSize: 18, marginInlineEnd: 6 },
  controls: { display: "flex", gap: 16, flexWrap: "wrap", marginBottom: 8 },
  controlLabel: {
    display: "flex",
    flexDirection: "column",
    gap: 4,
    fontSize: 13,
    color: "var(--text-muted)",
  },
  select: {
    padding: "8px 10px",
    background: "var(--surface)",
    border: "1px solid var(--border)",
    borderRadius: 8,
    fontSize: 14,
    minWidth: 160,
  },
  sectionTitle: { fontSize: 16, fontWeight: 600, margin: "12px 0 4px" },
  chartWrap: {
    background: "var(--surface)",
    border: "1px solid var(--border)",
    borderRadius: "var(--radius)",
    padding: 12,
  },
  muted: { color: "var(--text-muted)", padding: 12 },
  levelInput: {
    width: 52,
    padding: "2px 4px",
    fontSize: 14,
    border: "1px solid var(--primary)",
    borderRadius: 4,
    background: "var(--surface)",
    textAlign: "center" as const,
  },
};
