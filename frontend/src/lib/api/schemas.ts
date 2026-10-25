import { z } from "zod";

export const RoleSchema = z.enum(["patient", "clinician", "admin", "carer"]);
export type Role = z.infer<typeof RoleSchema>;

export const MeSchema = z.object({
  id: z.string(),
  role: RoleSchema,
  display_name: z.string(),
});
export type Me = z.infer<typeof MeSchema>;

export const PatientSchema = z.object({
  id: z.string(),
  display_name: z.string(),
});
export type Patient = z.infer<typeof PatientSchema>;

export const UserSummarySchema = z.object({
  id: z.string(),
  email: z.string(),
  role: RoleSchema,
  display_name: z.string(),
  is_active: z.boolean(),
  care_team: z.array(z.string()).default([]),
  // Carers: who they support, e.g. "Alex (daughter)".
  supports: z.array(z.string()).default([]),
});
export type UserSummary = z.infer<typeof UserSummarySchema>;

export const ROLE_HOME: Record<Role, string> = {
  patient: "/patient",
  clinician: "/clinician",
  admin: "/admin",
  carer: "/carer",
};

// ---- Practice ----

export const PracticeStatusSchema = z.object({
  has_plan: z.boolean(),
  has_active_session: z.boolean(),
  // Stopped early in the last 30 minutes: can be reopened ("Keep going").
  resumable: z
    .object({ session_id: z.string(), answered: z.number() })
    .nullable()
    .default(null),
});

export const PracticeActivitySchema = z.object({
  sessions_completed: z.number(),
  pictures_practised: z.number(),
  recent: z.array(z.object({ started_at: z.string(), answered: z.number() })),
});
export type PracticeActivity = z.infer<typeof PracticeActivitySchema>;

export const ExerciseSchema = z.object({
  id: z.string(),
  position: z.number(),
  type: z.string(),
  prompt: z.string(),
  instructions: z.string(),
  image_url: z.string().nullable(),
  response_modes: z.array(z.string()),
  cues: z.array(z.string()),
  words: z.array(z.string()).nullable().optional(),
  image_kind: z.string().optional(),
  // Word repetition and word recognition: the word to say or to find.
  word: z.string().nullable().optional(),
  // Picture-choice types: tapping a picture answers with its word.
  options: z
    .array(z.object({ word: z.string(), image_url: z.string() }))
    .nullable()
    .optional(),
});
export type Exercise = z.infer<typeof ExerciseSchema>;

export const SessionStateSchema = z.object({
  session_id: z.string(),
  status: z.enum(["active", "completed", "ended"]),
  total: z.number(),
  exercise: ExerciseSchema.nullable(),
  summary: z
    .object({
      practiced: z.number(),
      correct: z.number(),
      near_miss: z.number(),
    })
    .nullable(),
});
export type SessionState = z.infer<typeof SessionStateSchema>;

export const OutcomeSchema = z.enum([
  "correct",
  "near_miss",
  "incorrect",
  "skipped",
]);
export type Outcome = z.infer<typeof OutcomeSchema>;

export const ResponseResultSchema = z.object({
  outcome: OutcomeSchema,
  target: z.string(),
  heard: z.string().nullable().optional(),
  concepts_matched: z.array(z.string()).nullable().optional(),
  concepts_missing: z.array(z.string()).nullable().optional(),
  state: SessionStateSchema,
});
export type ResponseResult = z.infer<typeof ResponseResultSchema>;

export const SpeechAcceptedSchema = z.object({ recording_id: z.string() });

export const SpeechStatusSchema = z.object({
  status: z.enum([
    "pending",
    "processing",
    "confirm",
    "done",
    "rejected",
    "no_speech",
    "failed",
  ]),
  // status "confirm": what the recogniser heard, for "Is that what you said?"
  heard: z.string().nullable().optional(),
  result: z.lazy(() => ResponseResultSchema).nullable(),
});

/** GenAI use case 2: a short supportive tip about an already-scored answer (or nothing). */
export const AIFeedbackSchema = z.object({
  feedback: z.string().nullable(),
  hint: z.string().nullable(),
});

/** One-word answers in a finished session, for the end-of-session recap. */
export const RecapSchema = z.array(
  z.object({
    word: z.string(),
    image_url: z.string().nullable(),
    outcome: z.enum(["correct", "near_miss", "incorrect", "skipped"]),
  }),
);
export type RecapWord = z.infer<typeof RecapSchema>[number];

/** A therapy goal set by the clinician, with progress measured from practice. */
export const GoalSchema = z.object({
  id: z.string(),
  kind: z.enum(["name_words", "practice_days"]),
  target: z.number(),
  category: z.string().nullable(),
  due_on: z.string().nullable(),
  status: z.enum(["active", "achieved", "ended"]),
  title: z.string(),
  progress: z.number(),
  created_at: z.string(),
  achieved_at: z.string().nullable(),
});
export type Goal = z.infer<typeof GoalSchema>;
export const GoalListSchema = z.array(GoalSchema);

// ---- Family / carers ----

export const SupportedPatientSchema = z.object({
  id: z.string(),
  display_name: z.string(),
  relationship: z.string(),
});
export const CarerSummarySchema = z.object({
  patient: SupportedPatientSchema,
  activity: z.lazy(() => PracticeActivitySchema),
  goals: GoalListSchema,
});

/** One of a patient's own words: a photo added by their family or clinician. */
export const PersonalWordSchema = z.object({
  id: z.string(),
  word: z.string(),
  also_accepted: z.array(z.string()),
  image_url: z.string(),
  added_by: z.string().nullable(),
});
export type PersonalWord = z.infer<typeof PersonalWordSchema>;

/** A short note from a family member to the patient. */
export const MessageSchema = z.object({
  id: z.string(),
  text: z.string(),
  author: z.string(),
  relationship: z.string(),
  created_at: z.string(),
  seen: z.boolean(),
});
export type Message = z.infer<typeof MessageSchema>;
export const MessageListSchema = z.array(MessageSchema);

/** An everyday script ("At the café"), practised line by line. */
export const ScriptSchema = z.object({
  id: z.string(),
  title: z.string(),
  icon: z.string(),
  lines: z.array(z.string()),
  times_practised: z.number(),
  last_practised: z.string().nullable(),
});
export type Script = z.infer<typeof ScriptSchema>;

/** One tap a day: how the patient feels. */
export const MoodDaySchema = z.object({
  day: z.string(),
  mood: z.enum(["good", "okay", "low"]),
});
export type MoodDay = z.infer<typeof MoodDaySchema>;
