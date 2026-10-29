# Product

<!-- impeccable:product-schema 1 -->

## Platform

web

## Users

- **Patient (primary):** an adult recovering from stroke-related aphasia, practising at home between therapy sessions. Often older, may use one hand, tires quickly, and may have low mood. Job: name pictures, practise everyday phrases and their own words, and use the talk board to say things aloud.
- **Clinician (speech and language therapist):** sets the practice limits and goals, reviews practice data, and audits every AI decision.
- **Family / carer:** sees how often the patient practises (never how well), adds the patient's own words with photos, and sends short notes of encouragement. No clinical access.
- **Admin:** creates accounts, care-team assignments and family links. Sees no clinical data.

When needs conflict, the patient comes first.

## Product Purpose

RehabMind gives people with aphasia short, calm picture exercises at home, filling the gap between limited therapy sessions. Patients answer by speaking, typing or tapping. The system scores each answer and personalises the next exercise, always inside limits set by the patient's clinician. Success means more practice between sessions, which the clinician can see and steer.

Currently an academic project and demo, run on seeded test accounts only, with a real patient pilot as a possible later step.

## Positioning

AI-assisted but clinician-bounded: the AI never acts on its own. Every exercise stays inside versioned limits set by the clinician, and every AI decision is audited. Speech is transcribed on the app's own server and recordings are deleted after transcription. It costs $0 to run, with no paid API keys.

## Operating Context

- Patients use it at home on a laptop or tablet, in short sessions, often with family nearby.
- Clinicians work in four views: overview, sessions, words (per-picture progress) and plan (goals, own words, practice limits), with the AI review one step away.
- Exercise types use real photographs: the BOSS research dataset and Wikimedia Commons scenes (credits in `docs/photo-credits.md`).

## Capabilities and Constraints

- **Stack:** Next.js 16 (App Router, Tailwind 4) frontend; FastAPI, Postgres, Redis and MinIO backend; ARQ worker with local faster-whisper; local Ollama model, or rule-based generation with the AI turned off.
- **Patient features:** seven exercise types, everyday phrases (script training), own words (encrypted family photos, never sent to the AI), talk board, goals measured from practice, mood check-in, break suggestions, and "My information" (who can see what, stop sharing, download a copy).
- **Patient pages:** the user previously required them to fit one screen at laptop sizes without scrolling; phone refinement was deprioritised.
- **Undecided:** hosting and deployment. Vercel can host the frontend only; the backend services need separate hosting.

## Brand Commitments

- Keep the name **RehabMind**.
- Keep it **$0 to run, with no paid API keys**: local speech and local or optional AI only.
- **Tone:** calm and encouraging, with no streak pressure. Family see effort, not scores.
- **Disclaimer:** it is a research prototype, not a diagnostic tool, and the clinician is always the authority.

## Evidence on Hand

- README, `docs/interaction-design.md`, README screenshots in `docs/images/`, and photo credits.
- There is no clinical validation, no real patient data, and no testimonials. Future work must not invent any.

## Product Principles

1. The patient comes first: low effort, large targets, no penalty for a missed day.
2. The clinician is the authority: the AI only works inside clinician-set limits, and every AI decision can be audited.
3. Privacy by default: recordings are not kept, the patient controls sharing, and the family sees activity only.
4. Practice should carry over into real life (own words, everyday phrases, talk board).
5. Honest about what it is: a prototype, never presented as validated.

## Accessibility & Inclusion

Users have aphasia, possible one-handed use, fatigue and low mood. Keep language plain, give every action several ways to answer, and keep targets large. Playwright e2e tests run axe checks against WCAG 2.1 AA tags.
