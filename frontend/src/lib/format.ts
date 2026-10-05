/** Display formatting and neutral, factual labels for clinician views. */

const dateTime = new Intl.DateTimeFormat("en-GB", {
  dateStyle: "medium",
  timeStyle: "short",
});
const dateOnly = new Intl.DateTimeFormat("en-GB", { dateStyle: "medium" });

const dayMonth = new Intl.DateTimeFormat("en-GB", {
  day: "numeric",
  month: "short",
});
const timeOnly = new Intl.DateTimeFormat("en-GB", { timeStyle: "short" });

/** Short, distinct axis labels: times when all points share a day, otherwise dates. */
export function axisLabels(isos: string[]): string[] {
  const days = new Set(isos.map((i) => dateOnly.format(new Date(i))));
  const fmt = days.size === 1 ? timeOnly : dayMonth;
  return isos.map((i) => fmt.format(new Date(i)));
}

export const formatDateTime = (iso: string) => dateTime.format(new Date(iso));
export const formatDate = (iso: string) => dateOnly.format(new Date(iso));

export function formatDuration(seconds: number | null): string {
  if (seconds === null) return "—";
  const m = Math.floor(seconds / 60);
  const s = seconds % 60;
  return m ? `${m} min ${s} s` : `${s} s`;
}

export function formatMs(ms: number | null): string {
  if (ms === null) return "—";
  return ms < 1000 ? `${ms} ms` : `${(ms / 1000).toFixed(1)} s`;
}

export function percent(part: number, whole: number): string {
  return whole ? `${Math.round((part / whole) * 100)}%` : "—";
}

export function daysSince(iso: string | null): number | null {
  return iso
    ? Math.floor((Date.now() - new Date(iso).getTime()) / 86_400_000)
    : null;
}

const humanize = (s: string) =>
  s.charAt(0).toUpperCase() + s.slice(1).replaceAll("_", " ");

export const EXERCISE_TYPE: Record<string, string> = {
  picture_naming: "Picture naming",
  word_repetition: "Word repetition",
  word_recognition: "Word recognition",
  sentence_completion: "Sentence completion",
  sentence_construction: "Sentence construction",
  picture_description: "Picture description",
  category_naming: "Category naming",
};
export const exerciseType = (t: string) => EXERCISE_TYPE[t] ?? humanize(t);

export const RESPONSE_MODE: Record<string, string> = {
  text: "Typing",
  speech: "Speaking",
};
export const responseMode = (m: string) => RESPONSE_MODE[m] ?? humanize(m);

export const OUTCOME: Record<string, string> = {
  correct: "Correct",
  near_miss: "Close",
  incorrect: "Incorrect",
  skipped: "Skipped",
};
export const outcome = (o: string | null) =>
  o ? (OUTCOME[o] ?? humanize(o)) : "Not answered";

export const SESSION_STATUS: Record<string, string> = {
  completed: "Completed",
  ended: "Stopped early",
  active: "In progress",
};

export const SOURCE: Record<string, string> = {
  ai: "AI-personalized",
  rule: "Rule-based",
  fallback: "Safe fallback",
};

export const SELECTION_REASON: Record<string, string> = {
  reinforce_recent_error: "Revisit after recent errors",
  consolidate_success: "Consolidate a weaker category",
  introduce_new: "Introduce a new picture",
  category_variety: "Vary the category",
};

export const STAGE: Record<string, string> = {
  provider: "Provider (no response)",
  schema: "Format check",
  clinical: "Clinical limits check",
  safety: "Safety check",
  issuer: "Exercise issuer check",
};

const REASON: Record<string, string> = {
  invalid_json: "Output was not valid JSON",
  not_an_object: "Output had the wrong structure",
  stimulus_not_in_candidates: "Picture not in the allowed list",
  difficulty_out_of_range: "Difficulty outside the clinician's range",
  difficulty_mismatch: "Difficulty did not match the picture",
  category_not_allowed: "Category not allowed",
  invalid_phonemic_cue: "First-sound hint did not match the word",
  provider_error: "Provider error",
  timeout: "Provider timed out",
};

/** Human-readable reason code, e.g. "answer_leak:prompt" → "Answer revealed (prompt)". */
export function reasonLabel(code: string): string {
  const [kind, field] = code.split(":");
  const fieldLabel = field ? ` (${field.replaceAll("_", " ")})` : "";
  const kinds: Record<string, string> = {
    answer_leak: "Answer revealed",
    medical_claim: "Medical or recovery claim",
    pressure_language: "Pressuring language",
    link_or_contact: "Link or contact details",
    digits: "Contains numbers",
    too_long: "Too long",
    missing: "Missing field",
    extra_forbidden: "Unexpected field",
    enum: "Invalid value",
    less_than_equal: "Value too high",
    greater_than_equal: "Value too low",
  };
  return REASON[code] ?? `${kinds[kind] ?? humanize(kind)}${fieldLabel}`;
}

export const SPEECH_ATTEMPT_REASON: Record<string, string> = {
  empty: "nothing heard",
  no_speech: "no speech detected",
  low_confidence: "low recognition confidence",
  known_hallucination: "unreliable transcript discarded",
  transcription_error: "processing error",
  timed_out: "timed out",
  exercise_closed: "exercise already closed",
};
