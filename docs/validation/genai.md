# Generated exercise text

Full numbers: [results/genai-audit.md](results/genai-audit.md). Every raw output:
`results/genai-audit.jsonl`.

## Method

`app/scripts/genai_audit.py` runs the production prompts against the local model
(`qwen2.5:3b`, production temperature) for every catalogue picture and exercise type, four
times each, and asks for feedback on 120 benchmark answers. Every output goes through the
production validators with the app's two-attempt retry. 600 requests, 827 raw generations.

## Results: raw vs shipped

| Task | Valid first time | Valid after retry | Rule-based fallback |
|---|---|---|---|
| Picture naming | 55% | 69% | 31% |
| Sentence building | 53% | 68% | 32% |
| Picture description | 54% | 72% | 28% |
| Feedback | 92% | 99% | 1% |

What the validators stopped, as a share of raw outputs. None reached a patient: a rejected
output is retried once, then replaced by the rule-based version.

| Problem | Raw outputs | Shipped |
|---|---|---|
| Gave away the answer | 17.8% | 0% |
| Too long | 17.4% | 0% |
| Wrong first-sound cue | 14.5% | 0% |
| Uncommon word (new plain-language check) | 4.8% | 0% |
| Sentence over 12 words (new) | 2.3% | 0% |
| Feedback contradicting the score | 0.4% | 0% |
| Picture not in the allowed list (hallucinated content) | 0% | 0% |

Accepted text averages 7.1 words per sentence, and 95% of its words are everyday English
(Zipf ≥ 4).

## What the validators cannot check

Validators check form, safety and leaks, not meaning. In the audit, the model's accepted
meaning cue for the house photo was "It's used for storing things in a room": safe, short,
plain, and wrong. Only clinicians can judge whether a cue helps. That is the Phase 1 content
panel: 24 AI-written naming items and the rule-based items for the same pictures, rated
blind on relevance, clarity, tone and difficulty fit
([protocol](protocols/phase1-slp-panel.md), [items](review-packets/phase1-items.csv)).

## Findings to act on

- **About 30% of exercise requests fall back to rule-based text.** The fallback is safe, so
  this is a cost (less varied wording), not a risk. Most rejections are answer leaks and long
  prompts, so a prompt revision that states the word limits and forbids naming the target
  should lower it. That would be prompt version 2, re-audited with the same script.
- Blinding in the panel is partial: rule-based questions are always "What is this?". Raters
  are asked to judge the cues, and the analysis reports both sources separately.
