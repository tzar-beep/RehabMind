import { z } from "zod";

/** Contracts for clinician views. Mirrors backend/app/clinicians/schemas.py. */

const dt = z.string(); // ISO datetime; formatted for display in lib/format.ts

export const OutcomeCountsSchema = z.object({
  correct: z.number(),
  near_miss: z.number(),
  incorrect: z.number(),
  skipped: z.number(),
});
export type OutcomeCounts = z.infer<typeof OutcomeCountsSchema>;

export const PatientListItemSchema = z.object({
  id: z.string(),
  display_name: z.string(),
  sessions_completed: z.number(),
  last_session_at: dt.nullable(),
  recent_responses: z.number(),
  recent_correct: z.number(),
  constraints: z
    .object({
      version: z.number(),
      min_difficulty: z.number(),
      max_difficulty: z.number(),
      allowed_exercise_types: z.array(z.string()),
      allowed_response_modes: z.array(z.string()),
    })
    .nullable(),
});
export type PatientListItem = z.infer<typeof PatientListItemSchema>;

export const ResetInfoSchema = z.object({
  at: dt,
  by: z.string().nullable(),
  reason: z.string(),
});
export type ResetInfo = z.infer<typeof ResetInfoSchema>;

export const PatientOverviewSchema = z.object({
  id: z.string(),
  display_name: z.string(),
  patient_since: dt,
  care_team: z.array(z.string()),
  sessions_total: z.number(),
  sessions_completed: z.number(),
  sessions_stopped_early: z.number(),
  has_active_session: z.boolean(),
  first_session_at: dt.nullable(),
  last_session_at: dt.nullable(),
  outcomes: OutcomeCountsSchema,
  by_mode: z.array(
    z.object({ mode: z.string(), attempted: z.number(), correct: z.number() }),
  ),
  hinted_responses: z.number(),
  median_latency_ms: z.number().nullable(),
  current_working_difficulty: z.number().nullable(),
  last_reset: ResetInfoSchema.nullable().optional(),
});
export type PatientOverview = z.infer<typeof PatientOverviewSchema>;

export const SessionSummarySchema = z.object({
  id: z.string(),
  started_at: dt,
  completed_at: dt.nullable(),
  status: z.string(),
  planned: z.number(),
  outcomes: OutcomeCountsSchema,
  attempted: z.number(),
  avg_difficulty: z.number().nullable(),
  modes: z.array(z.string()),
  duration_s: z.number().nullable(),
  before_reset: z.boolean().optional(),
});
export type SessionSummary = z.infer<typeof SessionSummarySchema>;

export const SessionPageSchema = z.object({
  items: z.array(SessionSummarySchema),
  total: z.number(),
  limit: z.number(),
  offset: z.number(),
});

export const ExerciseDetailSchema = z.object({
  position: z.number(),
  issued_at: dt,
  exercise_type: z.string(),
  difficulty: z.number(),
  source: z.string(),
  status: z.string(),
  picture: z.string().nullable(),
  category: z.string().nullable(),
  image_url: z.string().nullable(),
  target: z.string(),
  prompt: z.string(),
  response_mode: z.string().nullable(),
  response_text: z.string().nullable(),
  outcome: z.string().nullable(),
  match_type: z.string().nullable(),
  hints_used: z.number().nullable(),
  latency_ms: z.number().nullable(),
  transcript_quality: z
    .object({
      no_speech_prob: z.number().nullable(),
      avg_logprob: z.number().nullable(),
      low_confidence_words: z.array(z.string()),
    })
    .nullable(),
  speech_attempts: z.array(
    z.object({ status: z.string(), reason: z.string().nullable() }),
  ),
});
export type ExerciseDetail = z.infer<typeof ExerciseDetailSchema>;

export const SessionDetailSchema = z.object({
  session: SessionSummarySchema,
  exercises: z.array(ExerciseDetailSchema),
});

export const TrendPointSchema = z.object({
  session_id: z.string(),
  started_at: dt,
  attempted: z.number(),
  correct: z.number(),
  near_miss: z.number(),
  incorrect: z.number(),
  skipped: z.number(),
  accuracy: z.number(),
  avg_difficulty: z.number(),
});
export type TrendPoint = z.infer<typeof TrendPointSchema>;

export const ConstraintFieldsSchema = z.object({
  allowed_exercise_types: z.array(z.string()),
  allowed_response_modes: z.array(z.string()),
  allowed_categories: z.array(z.string()).nullable(),
  min_difficulty: z.number(),
  max_difficulty: z.number(),
  max_exercises_per_session: z.number(),
  advance_after_correct: z.number(),
  step_back_after_incorrect: z.number(),
  note: z.string().nullable(),
});
export type ConstraintFields = z.infer<typeof ConstraintFieldsSchema>;

export const ConstraintVersionSchema = ConstraintFieldsSchema.extend({
  id: z.string(),
  version: z.number(),
  is_active: z.boolean(),
  created_at: dt,
  created_by: z.string(),
});
export type ConstraintVersion = z.infer<typeof ConstraintVersionSchema>;

export const ConstraintOptionsSchema = z.object({
  exercise_types: z.array(
    z.object({ value: z.string(), available: z.boolean() }),
  ),
  response_modes: z.array(z.string()),
  categories: z.record(z.string(), z.record(z.string(), z.number())),
  difficulty: z.tuple([z.number(), z.number()]),
  max_exercises_per_session: z.tuple([z.number(), z.number()]),
  progression_rule: z.tuple([z.number(), z.number()]),
});
export type ConstraintOptions = z.infer<typeof ConstraintOptionsSchema>;

export const AIRunSchema = z.object({
  session_id: z.string(),
  position: z.number().nullable(),
  created_at: dt,
  result: z.enum([
    "ai_generated",
    "ai_generated_after_retry",
    "rule_based_used",
    "no_exercise",
  ]),
  provider: z.string(),
  model: z.string(),
  prompt_version: z.string(),
  constraint_version: z.number(),
  target_difficulty: z.number(),
  recent_outcomes: z.array(z.string()),
  candidates: z.number(),
  selection_reason: z.string().nullable(),
  attempts: z.array(
    z.object({
      attempt: z.number(),
      status: z.string(),
      failed_stage: z.string().nullable(),
      reason_codes: z.array(z.string()),
      latency_ms: z.number(),
      output: z.record(z.string(), z.unknown()).nullable(),
    }),
  ),
  final_exercise: z
    .object({
      id: z.string(),
      source: z.string(),
      difficulty: z.number(),
      picture: z.string().nullable(),
      prompt: z.string(),
    })
    .nullable(),
});
export type AIRun = z.infer<typeof AIRunSchema>;

/** Which AI provider is configured (real local LLM via Ollama, offline fake, or none). */
export const AIStatusSchema = z.object({
  provider: z.string(),
  model: z.string().nullable(),
  generative: z.boolean(),
  reachable: z.boolean(),
  model_available: z.boolean(),
  demo_view: z.boolean(),
});
export type AIStatus = z.infer<typeof AIStatusSchema>;

/** GenAI use case 3: clinician-facing progress summary (AI draft or rule-based fallback). */
export const ProgressSummarySchema = z.object({
  summary: z.string(),
  strengths: z.array(z.string()),
  focus_areas: z.array(z.string()),
  source: z.enum(["ai", "rules"]),
  provider: z.string().nullable(),
  model: z.string().nullable(),
  prompt_version: z.string().nullable(),
  created_at: dt.nullable(),
  figures: z.record(z.string(), z.unknown()),
});
export type ProgressSummary = z.infer<typeof ProgressSummarySchema>;

const PipelineGenerationSchema = z.object({
  task: z.string(),
  prompt_version: z.string(),
  context: z.record(z.string(), z.unknown()),
  system_prompt: z.string().nullable(),
  user_prompt: z.string().nullable(),
  attempts: z.array(
    z.object({
      attempt: z.number(),
      status: z.string(),
      failed_stage: z.string().nullable(),
      reason_codes: z.array(z.string()),
      latency_ms: z.number(),
      provider: z.string(),
      model: z.string(),
      raw_output: z.string().nullable(),
      usage: z.record(z.string(), z.number()).nullable(),
    }),
  ),
  output: z.record(z.string(), z.unknown()).nullable(),
});
export type PipelineGeneration = z.infer<typeof PipelineGenerationSchema>;

export const PipelineSchema = z.object({
  status: AIStatusSchema,
  abilities: z.record(
    z.string(),
    z.object({
      objective: z.string(),
      attempts: z.number(),
      ability: z.number(),
      recent_accuracy: z.number().nullable(),
      trend: z.string(),
      status: z.string(),
    }),
  ),
  traces: z.array(
    z.object({
      position: z.number(),
      issued_at: dt,
      objective: z.string(),
      objective_label: z.string(),
      exercise_type: z.string(),
      difficulty: z.number(),
      source: z.string(),
      picture: z.string().nullable(),
      image_url: z.string().nullable(),
      shown: z.object({
        prompt: z.string().nullable(),
        cues: z.array(z.string()),
        words: z.array(z.string()).nullable(),
      }),
      generation: PipelineGenerationSchema.nullable(),
      response: z
        .object({
          text: z.string().nullable(),
          mode: z.string(),
          outcome: z.string(),
          score: z.number(),
          match_type: z.string().nullable(),
          concepts_matched: z.array(z.string()).nullable(),
          concepts_missing: z.array(z.string()).nullable(),
          hints_used: z.number().nullable(),
        })
        .nullable(),
      feedback: PipelineGenerationSchema.nullable(),
    }),
  ),
});
export type Pipeline = z.infer<typeof PipelineSchema>;
