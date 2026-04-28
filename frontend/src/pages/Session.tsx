import { useEffect, useRef, useState } from "react";
import { api, type Kid, type NextProblem, type SubmitResult } from "../api";
import { S } from "../strings";

function Frac({ num, den }: { num: string; den: string }) {
  return (
    <span style={{ display: "inline-flex", flexDirection: "column", verticalAlign: "middle", textAlign: "center", lineHeight: 1.1, margin: "0 4px" }}>
      <span style={{ padding: "0 6px" }}>{num}</span>
      <span style={{ padding: "0 6px", borderTop: "0.08em solid currentColor" }}>{den}</span>
    </span>
  );
}

function MathText({ text }: { text: string }) {
  const parts: React.ReactNode[] = [];
  const re = /(\d+|\?)\/(\d+|\?)/g;
  let last = 0;
  let m: RegExpExecArray | null;
  let i = 0;
  while ((m = re.exec(text))) {
    if (m.index > last) parts.push(text.slice(last, m.index));
    parts.push(<Frac key={i++} num={m[1]} den={m[2]} />);
    last = m.index + m[0].length;
  }
  if (last < text.length) parts.push(text.slice(last));
  return <>{parts}</>;
}

interface Props {
  kid: Kid;
  topic: string;
  sessionId: number;
  onDone: (durationSeconds: number) => void;
  onBack: () => void;
}

type Phase = "loading" | "answering" | "feedback" | "done";

export default function Session({ kid, topic: _topic, sessionId, onDone, onBack }: Props) {
  const [phase, setPhase] = useState<Phase>("loading");
  const [problem, setProblem] = useState<NextProblem | null>(null);
  const [answer, setAnswer] = useState("");
  const [result, setResult] = useState<SubmitResult | null>(null);
  const [difficulty, setDifficulty] = useState(0);
  const startTimeRef = useRef<number>(Date.now());
  const sessionStartRef = useRef<number>(Date.now());
  const inputRef = useRef<HTMLInputElement>(null);

  async function loadNext() {
    setPhase("loading");
    setAnswer("");
    setResult(null);
    const p = await api.nextProblem(sessionId);
    if (p.done) {
      setPhase("done");
      return;
    }
    setProblem(p);
    setDifficulty(p.difficulty);
    setPhase("answering");
    startTimeRef.current = Date.now();
    setTimeout(() => inputRef.current?.focus(), 50);
  }

  useEffect(() => {
    loadNext();
  }, []);

  async function handleSubmit() {
    if (!problem || !answer.trim()) return;
    const timeTaken = (Date.now() - startTimeRef.current) / 1000;
    const r = await api.submitAnswer(problem.problem_id, answer.trim(), timeTaken);
    setResult(r);
    setDifficulty(r.new_difficulty);
    setPhase("feedback");
    if (r.session_done) {
      const duration = Math.round((Date.now() - sessionStartRef.current) / 1000);
      setTimeout(() => onDone(duration), 1400);
    }
  }

  async function handleChoice(choice: string) {
    if (!problem) return;
    setAnswer(choice);
    const timeTaken = (Date.now() - startTimeRef.current) / 1000;
    const r = await api.submitAnswer(problem.problem_id, choice, timeTaken);
    setResult(r);
    setDifficulty(r.new_difficulty);
    setPhase("feedback");
    if (r.session_done) {
      const duration = Math.round((Date.now() - sessionStartRef.current) / 1000);
      setTimeout(() => onDone(duration), 1400);
    }
  }

  function handleKeyDown(e: React.KeyboardEvent) {
    if (e.key === "Enter") handleSubmit();
  }

  function speak(word: string) {
    const utt = new SpeechSynthesisUtterance(word);
    utt.lang = "he-IL";
    window.speechSynthesis.cancel();
    window.speechSynthesis.speak(utt);
  }

  const prevDiffRef = useRef(difficulty);
  const levelChange =
    result && difficulty !== prevDiffRef.current
      ? difficulty > prevDiffRef.current
        ? S.levelUp
        : S.levelDown
      : S.levelSame;

  useEffect(() => {
    if (phase === "answering") prevDiffRef.current = difficulty;
  }, [phase, difficulty]);

  useEffect(() => {
    function onKey(e: KeyboardEvent) {
      if (e.key !== "Enter") return;
      if (phase === "feedback" && result && !result.session_done) loadNext();
    }
    window.addEventListener("keydown", onKey);
    return () => window.removeEventListener("keydown", onKey);
  }, [phase, result]);

  return (
    <div style={styles.container}>
      {/* Header */}
      <div style={styles.header}>
        <button style={styles.backBtn} onClick={onBack}>{S.back} ←</button>
        <span style={styles.kidBadge}>{kid.avatar_emoji} {kid.name}</span>
        <span style={styles.levelBadge}>{S.level}: {Math.floor(difficulty)}</span>
      </div>

      {/* Progress */}
      {problem && (
        <div style={styles.progressRow}>
          <div style={styles.progressBar}>
            <div
              style={{
                ...styles.progressFill,
                width: `${((problem.session_problem_number - 1) / problem.total_problems) * 100}%`,
              }}
            />
          </div>
          <span style={styles.progressLabel}>
            {S.problemOf(problem.session_problem_number, problem.total_problems)}
          </span>
        </div>
      )}

      {/* Card */}
      <div style={styles.card}>
        {phase === "loading" && <p style={styles.loading}>...</p>}

        {(phase === "answering" || phase === "feedback") && problem && (
          <>
            {problem.tts_word ? (
              <button style={styles.ttsQuestion} onClick={() => speak(problem.tts_word!)}>
                <span style={styles.ttsDisplay}>{problem.question}</span>
                <span style={styles.ttsSpeakHint}>🔊</span>
              </button>
            ) : (
              <p style={styles.question}><MathText text={problem.question} /></p>
            )}

            {problem.choices ? (
              <div style={styles.choices}>
                {problem.choices.map((c) => {
                  let bg = "var(--bg)";
                  let color: string | undefined = undefined;
                  if (phase === "feedback" && result) {
                    if (c === answer && result.is_correct) { bg = "var(--success)"; color = "#fff"; }
                    else if (c === answer && !result.is_correct) { bg = "var(--error)"; color = "#fff"; }
                    else if (c === result.correct_answer && !result.is_correct) { bg = "var(--success)"; color = "#fff"; }
                  }
                  return (
                    <button
                      key={c}
                      style={{ ...styles.choiceBtn, ...(problem.tts_word ? styles.choiceBtnLarge : {}), background: bg, color }}
                      onClick={() => phase === "answering" && handleChoice(c)}
                      disabled={phase === "feedback"}
                    >
                      <MathText text={c} />
                    </button>
                  );
                })}
              </div>
            ) : (
              <>
                <div style={styles.inputRow}>
                  <input
                    ref={inputRef}
                    style={{
                      ...styles.input,
                      borderColor:
                        phase === "feedback"
                          ? result?.is_correct
                            ? "var(--success)"
                            : "var(--error)"
                          : "var(--border)",
                    }}
                    type="text"
                    inputMode="decimal"
                    value={answer}
                    onChange={(e) => setAnswer(e.target.value)}
                    onKeyDown={handleKeyDown}
                    disabled={phase === "feedback"}
                    placeholder={S.answer}
                  />
                  {phase === "answering" && (
                    <button style={styles.submitBtn} onClick={handleSubmit} disabled={!answer.trim()}>
                      {S.submit}
                    </button>
                  )}
                </div>

                {phase === "answering" && (
                  <div style={styles.numpad}>
                    {["7","8","9","4","5","6","1","2","3"].map((k) => (
                      <button key={k} style={styles.numkey} onClick={() => { setAnswer((a) => a + k); inputRef.current?.focus(); }}>
                        {k}
                      </button>
                    ))}
                    <button style={styles.numkey} onClick={() => { setAnswer((a) => a.slice(0, -1)); inputRef.current?.focus(); }}>⌫</button>
                    <button style={styles.numkey} onClick={() => { setAnswer((a) => a + "0"); inputRef.current?.focus(); }}>0</button>
                    <button style={styles.numkey} onClick={() => { setAnswer((a) => a + "/"); inputRef.current?.focus(); }}>／</button>
                  </div>
                )}
              </>
            )}

            {phase === "feedback" && result && (
              <div style={styles.feedback}>
                <p
                  style={{
                    ...styles.feedbackText,
                    color: result.is_correct ? "var(--success)" : "var(--error)",
                  }}
                >
                  {result.is_correct ? S.correct : <MathText text={S.wrong(result.correct_answer)} />}
                </p>
                {levelChange && <p style={styles.levelChange}>{levelChange}</p>}
                {!result.session_done && (
                  <button style={styles.nextBtn} onClick={loadNext}>
                    {S.next} ←
                  </button>
                )}
              </div>
            )}
          </>
        )}

        {phase === "done" && (
          <p style={styles.loading}>{S.sessionComplete}</p>
        )}
      </div>
    </div>
  );
}

const styles: Record<string, React.CSSProperties> = {
  container: { maxWidth: 520, width: "100%" },
  header: {
    display: "flex",
    justifyContent: "space-between",
    alignItems: "center",
    marginBottom: 20,
  },
  backBtn: {
    background: "none",
    border: "none",
    color: "var(--text-muted)",
    fontSize: 14,
    cursor: "pointer",
    padding: "4px 0",
  },
  kidBadge: { fontSize: 18, fontWeight: 600 },
  levelBadge: {
    fontSize: 14,
    fontWeight: 600,
    background: "var(--primary)",
    color: "#fff",
    padding: "4px 12px",
    borderRadius: 999,
  },
  progressRow: { marginBottom: 20 },
  progressBar: {
    height: 6,
    background: "var(--border)",
    borderRadius: 999,
    overflow: "hidden",
    marginBottom: 6,
  },
  progressFill: {
    height: "100%",
    background: "var(--primary)",
    borderRadius: 999,
    transition: "width 0.3s",
  },
  progressLabel: { fontSize: 13, color: "var(--text-muted)" },
  card: {
    background: "var(--surface)",
    border: "2px solid var(--border)",
    borderRadius: "var(--radius)",
    boxShadow: "var(--shadow)",
    padding: "36px 32px",
    minHeight: 220,
    display: "flex",
    flexDirection: "column",
    gap: 24,
  },
  loading: { color: "var(--text-muted)", textAlign: "center", fontSize: 18 },
  question: { fontSize: 28, fontWeight: 600, textAlign: "center", lineHeight: 1.4, direction: "ltr" },
  ttsQuestion: {
    display: "flex",
    flexDirection: "column",
    alignItems: "center",
    gap: 8,
    background: "none",
    border: "none",
    cursor: "pointer",
    padding: "8px 0",
  },
  ttsDisplay: { fontSize: 80, lineHeight: 1.1 },
  ttsSpeakHint: { fontSize: 20, opacity: 0.5 },
  choiceBtnLarge: { fontSize: 36, padding: "20px 8px" },
  inputRow: { display: "flex", gap: 12, alignItems: "center", direction: "ltr" },
  input: {
    flex: 1,
    minWidth: 0,
    padding: "12px 16px",
    fontSize: 20,
    border: "2px solid",
    borderRadius: 8,
    background: "var(--bg)",
    textAlign: "center",
    direction: "ltr",
    outline: "none",
    transition: "border-color 0.15s",
  },
  submitBtn: {
    padding: "12px 20px",
    background: "var(--primary)",
    color: "#fff",
    borderRadius: 8,
    fontWeight: 700,
    fontSize: 16,
  },
  numpad: {
    display: "grid",
    gridTemplateColumns: "repeat(3, 1fr)",
    gap: 10,
    direction: "ltr",
  },
  choices: {
    display: "flex",
    gap: 12,
    justifyContent: "center",
    direction: "ltr",
  },
  choiceBtn: {
    flex: 1,
    padding: "18px 8px",
    fontSize: 22,
    fontWeight: 700,
    background: "var(--bg)",
    border: "2px solid var(--border)",
    borderRadius: 10,
    cursor: "pointer",
    transition: "background 0.15s",
  },
  numkey: {
    padding: "14px 0",
    fontSize: 22,
    fontWeight: 600,
    background: "var(--bg)",
    border: "2px solid var(--border)",
    borderRadius: 10,
    cursor: "pointer",
    transition: "background 0.1s",
  },
  feedback: { display: "flex", flexDirection: "column", gap: 12, alignItems: "center" },
  feedbackText: { fontSize: 20, fontWeight: 600 },
  levelChange: { fontSize: 14, color: "var(--text-muted)" },
  nextBtn: {
    padding: "10px 24px",
    background: "var(--primary)",
    color: "#fff",
    borderRadius: 8,
    fontWeight: 700,
    fontSize: 16,
  },
};
