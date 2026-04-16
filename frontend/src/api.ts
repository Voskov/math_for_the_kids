const BASE = "http://localhost:8000";

async function req<T>(path: string, options?: RequestInit): Promise<T> {
  const res = await fetch(`${BASE}${path}`, {
    headers: { "Content-Type": "application/json" },
    ...options,
  });
  if (!res.ok) {
    const text = await res.text();
    throw new Error(`API error ${res.status}: ${text}`);
  }
  return res.json();
}

export interface TopicLevel {
  topic: string;
  difficulty_level: number;
  score_accumulator: number;
}

export interface Kid {
  id: number;
  name: string;
  avatar_emoji: string;
  starting_grade: string;
  levels: TopicLevel[];
}

export interface SessionInfo {
  id: number;
  kid_id: number;
  topic: string;
  problem_count: number;
}

export interface NextProblem {
  problem_id: number;
  question: string;
  session_problem_number: number;
  total_problems: number;
  difficulty: number;
  done: boolean;
}

export interface SubmitResult {
  is_correct: boolean;
  correct_answer: string;
  new_difficulty: number;
  session_done: boolean;
  session_id: number;
}

export interface SummaryProblem {
  question_text: string;
  correct_answer: string;
  kid_answer: string | null;
  is_correct: boolean | null;
  time_taken_s: number | null;
  difficulty_at_time: number;
}

export interface SessionSummary {
  session_id: number;
  kid_name: string;
  topic: string;
  total: number;
  correct: number;
  accuracy_pct: number;
  problems: SummaryProblem[];
}

export const api = {
  getKids: () => req<Kid[]>("/kids/"),
  getKid: (id: number) => req<Kid>(`/kids/${id}`),

  startSession: (kid_id: number, topic: string) =>
    req<SessionInfo>("/sessions/start", {
      method: "POST",
      body: JSON.stringify({ kid_id, topic }),
    }),

  nextProblem: (session_id: number) =>
    req<NextProblem>(`/problems/next/${session_id}`),

  submitAnswer: (problem_id: number, kid_answer: string, time_taken_s: number) =>
    req<SubmitResult>("/problems/submit", {
      method: "POST",
      body: JSON.stringify({ problem_id, kid_answer, time_taken_s }),
    }),

  getSummary: (session_id: number) =>
    req<SessionSummary>(`/sessions/${session_id}/summary`),
};
