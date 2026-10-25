# Interaction design: the practice session

How the patient's practice behaves, moment by moment. Each interaction is specified with
Saffer's microinteraction model (trigger, rules, feedback, loops and modes). The session as
a whole is designed as a story with a peak and an ending, because people judge an
experience mostly by its best moment and how it ends (Kahneman's peak-end rule).

The patient side is a **transient** product (Cooper): short visits, one task, used by
people who may have reading difficulty, word-finding difficulty and weakness in one hand.
So: one primary action per screen, large targets, nothing that depends on reading alone,
no dialogs, and every mistake undoable.

## The session as a story

| Plot point | What the patient experiences | Designed for |
|---|---|---|
| Opening | Home: "Hello, Alex", one large "Start practice" | Clear what to do; no setup |
| Rising action | Picture → answer → feedback, 8 times, progress bar fills | Each step feels like progress |
| Crisis | Can't find the word | Hints (meaning, then first sound), "I'm not sure" without penalty, the right word to hear afterwards |
| **Peak** | Naming a picture on their own | Check icon with a single soft ring, "Nice work.", hear the word |
| **Ending** | Practice complete | The words named today, with their pictures; then "How did that feel?" |
| After | Back home | The week view; "Keep going" if they stopped early |

## Microinteractions

### Hear the question

| | |
|---|---|
| Trigger | Speaker button beside every question (manual) |
| Rules | Reads the question with the device's own voice, en-GB, 0.8× speed; "___" is read as "blank"; nothing leaves the device. Hidden if the device cannot speak |
| Feedback | The spoken question |
| Loops | Can be repeated any number of times |

### Listen-first word repetition

| | |
|---|---|
| Trigger | A word-repetition exercise answered by typing |
| Rules | The written word is hidden ("Listen to the word.") so repetition is not copying; "Hear it" plays it; "Show the word" reveals it. Shown at once when speaking, or if the device cannot speak |
| Feedback | The spoken word; the word itself after "Show the word" |

### Microphone level

| | |
|---|---|
| Trigger | System: recording starts |
| Rules | Input level from the microphone (RMS, Web Audio) drives five bars. Above the voice threshold the bars turn accent-coloured: "I can hear you". If no voice after 3 seconds, a prompt appears |
| Feedback | Live bars (visual); "I can't hear you yet. Try speaking a little louder, or closer to the device." (text, announced) |
| Loops | Runs until "Stop"; the 15-second limit still applies. Without Web Audio, recording works without the meter |
| Why | "I didn't catch that" was the commonest speech failure, found only after the recording. Feedback during the action prevents it |

### "Is that what you said?"

| | |
|---|---|
| Trigger | System: a spoken answer that would be scored correct |
| Rules | Shown before scoring: "I heard “door”." with Hear it, Yes, No, try again. Yes scores it; No discards it and keeps the picture open. Wrong words are scored at once with no question |
| Feedback | The large heard word; then the normal result, or "Thanks for telling me. Try again, or type your answer." |
| Why | The recogniser turns some sound errors into the target word (docs/validation/simulated.md) |

### The result (peak)

| | |
|---|---|
| Trigger | System: an answer is scored |
| Rules | Correct: success icon with one soft expanding ring (0.9 s, once). Anything else: a calm heart icon, never red. The right word is shown large with Hear it. An AI tip only after a close answer or a skip: after a different word the model's "meaning clues" were sometimes wrong |
| Feedback | Visual and verbal; the ring ends invisible and is removed by reduced motion |
| Loops | The ring is small and brief on purpose: it is seen up to eight times a session, so it must not become noise |

### Practice complete (ending)

| | |
|---|---|
| Trigger | System: the last picture is answered |
| Rules | Progress ring, "You practised 8 pictures", then **Words you named today**: each correctly named word once, with its picture, appearing one after another. If none were named: **Words you practised today**, never a list of misses. Then the difficulty rating. Read from the server, so answers before a "Keep going" count |
| Feedback | The patient's own achievements, in pictures, as the last thing they see |

### Stop for today, and undo

| | |
|---|---|
| Trigger | "Stop for today" (always visible during practice) |
| Rules | Stops at once, no "Are you sure?". For 30 minutes the home page's main action becomes **Keep going** (back to the same picture), with "Start new practice" beside it. Only if something was answered and no new session was started |
| Feedback | "You stopped after 3 pictures. You can carry on where you left off." |
| Modes | A one-off undo: it disappears when used, when a new practice starts, or after 30 minutes |
| Why | A mis-tap (tremor, one-handed use) must not cost the session, and a confirmation dialog on every stop would be excise |

## States checked for each control

Every interactive control has default, hover, focus (3 px blue ring),
disabled and busy states; speech has idle, recording (heard / not yet heard), checking,
confirm and retry; the practice screen has loading (skeleton in the same shape), error
(with a way home), answering, feedback and complete. All motion is removed under
`prefers-reduced-motion`.
