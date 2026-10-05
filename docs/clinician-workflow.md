# Clinician workflow

Academic prototype. Clinician views report **recorded practice activity only**: no
diagnosis, prognosis, risk score or validated clinical measure is calculated or implied.

## Routes

| Route | Purpose |
|---|---|
| `/clinician` | Dashboard: assigned patients, last practice, completed sessions, last 20 answers, active limits |
| `/clinician/patients/[id]` | Overview: active limits, activity facts, trend charts (≥ 2 sessions with answers) |
| `/clinician/patients/[id]/sessions` | Paginated session history → session detail (exercises in order) |
| `/clinician/patients/[id]/constraints` | Active practice limits, **create new version** (edit → review → save), read-only history, version comparison |
| `/clinician/patients/[id]/ai-generations` | AI audit log grouped per exercise slot: attempts, validation stage, reason codes, what the patient received |

## Demo path

Log in as `clinician@recovery.local` → open **Alex** → Overview → Sessions → a session →
Practice limits → *Create new version* → change a value → *Review changes* → *Save* →
AI audit log → expand an entry showing *Accepted after retry* or *Rule-based exercise used*.
Then log in as `clinician2@recovery.local`: Alex is not listed, and Alex's URLs show
"Patient not available" (the API returns 404).

## APIs (clinician only, assigned patients only)

| Endpoint | Notes |
|---|---|
| `GET /clinicians/me/patients` | Bounded per-patient aggregates (one query each, window function for last 20 answers) |
| `GET /patients/{id}/overview` | Outcome counts, by answer method, hints, median latency, working level, care team |
| `GET /patients/{id}/trends` | Last 20 sessions with answers: accuracy and average difficulty |
| `GET /patients/{id}/sessions?limit&offset` | Paginated summaries |
| `GET /patients/{id}/sessions/{sid}` | Exercises, responses, transcript quality, speech-attempt lifecycle status |
| `GET /patients/{id}/constraints/versions` | Every version, newest first, with author |
| `POST /patients/{id}/constraints` | Existing endpoint; creates the next immutable version |
| `GET /clinical/constraint-options` | Form choices and limits from backend rules (no duplicated constants) |
| `GET /patients/{id}/ai-generations/runs` | AI attempts grouped per exercise slot |

## Security decisions

- Every patient-scoped route resolves the patient through `get_accessible_patient` first;
  unassigned and non-existent patients both return 404 (and denials are audited).
- Patients and admins receive 403 on all clinician views; admin has no clinical access.
- The frontend only *navigates*; `notFound()` mirrors the backend's 404. Route manipulation
  and direct API calls are covered by backend and E2E tests.
- No read model selects audio objects, object keys or URLs; speech attempts expose lifecycle
  status only. Transcripts are labelled as automatic and possibly wrong, with confidence data.
- Constraint versions and AI audit rows remain append-only (DB privileges, unchanged).

## Data model change

`ai_generations.exercise_position` (nullable, reversible migration) records which exercise
slot an AI attempt was for. It groups retries and links a rejected run to the rule-based
exercise the patient actually received. Rows recorded before this column existed are grouped
at read time by transaction timestamp (`created_at` = the exercise's `issued_at`); audit rows
are never rewritten.
