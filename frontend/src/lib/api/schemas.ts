import { z } from "zod";

export const RoleSchema = z.enum(["patient", "clinician", "admin"]);
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
});
export type UserSummary = z.infer<typeof UserSummarySchema>;

export const ROLE_HOME: Record<Role, string> = {
  patient: "/patient",
  clinician: "/clinician",
  admin: "/admin",
};

// ---- Practice ----

export const PracticeStatusSchema = z.object({
  has_plan: z.boolean(),
  has_active_session: z.boolean(),
});

export const ExerciseSchema = z.object({
  id: z.string(),
  position: z.number(),
  type: z.string(),
  prompt: z.string(),
  instructions: z.string(),
  image_url: z.string().nullable(),
  response_modes: z.array(z.string()),
  cues: z.array(z.string()),
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
  state: SessionStateSchema,
});
export type ResponseResult = z.infer<typeof ResponseResultSchema>;

export const SpeechAcceptedSchema = z.object({ recording_id: z.string() });

export const SpeechStatusSchema = z.object({
  status: z.enum(["pending", "processing", "done", "no_speech", "failed"]),
  result: z.lazy(() => ResponseResultSchema).nullable(),
});
