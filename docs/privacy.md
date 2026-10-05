# Privacy

## Patient audio (V1: ephemeral)

```
browser MediaRecorder (≤15 s, ≤2 MB)
  → POST /practice/exercises/{id}/speech        (patient session, exercise ownership checked)
  → AES-256-GCM encrypt in the API               (key: AUDIO_ENCRYPTION_KEY; AAD = object key)
  → private, unversioned bucket `ephemeral-audio`
  → ARQ worker: decrypt → decode in memory → faster-whisper (self-hosted)
  → delete object (always: success, no-speech, or failure)
  → score transcript; store transcript + STT confidence only
```

- No audio in the database, logs, browser storage, or the frontend bundle.
- `audio_assets` keeps lifecycle metadata only (status, size, timestamps, `deleted_at`).
- Safety nets: a sweep every 5 min fails and deletes recordings stuck >10 min; the bucket
  expires any object after 1 day; bucket versioning is refused by `bootstrap_storage.py`.
- Audio never leaves our infrastructure: STT runs locally, not via a cloud API.
- Development uses synthetic speech only (e.g. Windows SAPI); `*.wav`/`*.webm` are git-ignored.
- Future clinician-approved retention would be a policy in `app/storage/audio.py`; not in V1.

## Transcripts

Stored with the response for clinician review, with `low_confidence_words` and
`no_speech_prob` so uncertainty is visible. Whisper is configured not to "fix" speech
(no prompt, no previous-text conditioning, temperature 0). Transcripts are estimates, not
clinical judgements.

Unreliable transcripts are **never scored**; the patient is asked to try again or type:
`no_speech_prob ≥ 0.6`, `avg_logprob < −1.0`, empty text, or a known Whisper hallucination
("thanks for watching", "thank you", "subscribe", …). Found in e2e: Whisper transcribed a
test tone as "Thanks for watching!".

## Clinician views

Authorized clinicians see transcripts (labelled as automatic and possibly wrong), recognition
confidence and the lifecycle status of each recording attempt. They never see audio, storage
keys or URLs: no clinician endpoint selects them.

## Other data

- AI providers (Phase 4) receive pseudonymous IDs and minimal context only.
- Logs redact passwords, tokens, cookies and audio-related keys; no request bodies are logged.
- Dev seed accounts never load outside `APP_ENV=development`.
