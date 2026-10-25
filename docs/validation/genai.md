# Generated exercise text

Full numbers: [results/genai-audit.md](results/genai-audit.md). Every raw output:
`results/genai-audit.jsonl`.

## Method

`app/scripts/genai_audit.py` runs the production prompts against the local model
(`qwen2.5:3b`, production temperature) for every catalogue picture and exercise type, four
times each, and asks for feedback on 120 benchmark answers. Every output goes through the
production validators with the app's two-attempt retry. Re-run after the switch to BOSS
photos (52 naming pictures): 472 requests, 707 raw generations.

## Results: raw vs shipped

| Task | Valid first time | Valid after retry | Rule-based fallback |
|---|---|---|---|
| Picture naming | 56% | 71% | 29% |
| Sentence building | 61% | 76% | 24% |
| Picture description | 57% | 69% | 31% |
| Feedback | 29% | 31% | 69% (no tip shown) |

What the validators stopped, as a share of raw outputs. None reached a patient: a rejected
output is retried once, then replaced by the rule-based version (or, for feedback, no tip).

| Problem | Raw outputs | Shipped |
|---|---|---|
| Feedback contradicting the score (mostly "nearly right" for a different word) | 23.3% | 0% |
| Wrong first-sound cue | 15.4% | 0% |
| Gave away the answer | 14.7% | 0% |
| Too long | 10.5% | 0% |
| Uncommon word | 2.7% | 0% |
| Sentence over 12 words | 1.4% | 0% |
| Picture not in the allowed list (hallucinated content) | 0% | 0% |

Accepted text averages 6.8 words per sentence, and 97% of its words are everyday English
(Zipf ≥ 4). The first audit (before the "nearly right" rule and the BOSS photos) found 17.8%
answer leaks and 99% valid feedback; that rule is why feedback validity fell.

## What the validators cannot check

Validators check form, safety and leaks, not meaning. In the audit, the model's accepted
meaning cue for the house photo was "It's used for storing things in a room": safe, short,
plain, and wrong. Only clinicians can judge whether a cue helps. That is the Phase 1 content
panel: 24 AI-written naming items and the rule-based items for the same pictures, rated
blind on relevance, clarity, tone and difficulty fit
([protocol](protocols/phase1-slp-panel.md), [items](review-packets/phase1-items.csv)).

## Findings to act on

- **Done:** patients now always see the same fixed question ("What is this?"). A walkthrough
  found an AI question that was safe and short but wrong for its picture ("Name the object
  in this room" for a house), and a predictable question suits people with aphasia better.
  The AI still chooses the picture and writes the cues and feedback.
- **Done:** feedback that calls a different word "close" or "nearly right" is rejected. The
  re-run audit shows why it matters: the model said "nearly" or "almost" for most answers
  that were a different word (feedback valid 31%), and an extra prompt instruction did not
  change that. AI tips were then shown only for close answers.
- **Done (feedback prompt v2):** the old task line asked the model to praise what the patient
  "did well or nearly did", for every outcome. `feedback_generation_v2` gives one instruction
  and one short example per outcome (a different word: thank the patient for trying and
  point to a feature of the picture; never "close" or "nearly"). On the same 120 benchmark
  answers, feedback valid first time rose from 31% to **79%** (87% after the retry), with
  no score contradictions. Most remaining rejections were "rare words" that were really
  possessives ("cup's" is rare in the word-frequency corpus, "cup" is not); the plain-language
  check now reads a possessive as its noun. Re-run: **89%** valid first time, **96%** after
  the retry, 4% without a tip; raw outputs flagged for rare words 8.3%, long sentences 4.5%,
  score contradiction 0.8% (one output, caught). Tips are shown again after any answer that is not
  correct, for the three exercise types the AI personalises.
- **Done (feedback prompt v3):** a walkthrough found accepted v2 tips that described the
  picture wrongly ("look at the handle for holding the bed"): the model cannot see the
  image, and the v2 instruction asked it to point to a feature of the picture. v3 asks for
  a clue about what the word means or is used for ("try thinking of something you use for
  sleeping"), and states that the model cannot see the picture. Audit: 88% valid first
  time, 98% after the retry, no score contradictions. But a later walkthrough found an
  accepted v3 clue that was simply wrong ("something you use for writing notes" for
  *key*): the validators check form and safety, not truth. So the app no longer shows an AI
  tip after a different word; the patient gets the right word with a button to hear it,
  which is itself a recognised cue. AI tips remain after a close answer or a skip, where
  they are about trying again, not about what a word means. Reproduce with
  `uv run python -m app.scripts.genai_audit --repeats 0 --feedback 120`.

- **About 30% of exercise requests fall back to rule-based text.** The fallback is safe, so
  this is a cost (less varied wording), not a risk. Most rejections are answer leaks and long
  prompts, so a prompt revision that states the word limits and forbids naming the target
  should lower it. That would be prompt version 2, re-audited with the same script.
- Blinding in the panel is partial: rule-based questions are always "What is this?". Raters
  are asked to judge the cues, and the analysis reports both sources separately.
