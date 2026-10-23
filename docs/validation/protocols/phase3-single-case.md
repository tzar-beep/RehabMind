# Phase 3 protocol: single-case study with people with aphasia

**Aim.** For each of 3-6 people with post-stroke aphasia, compare practice under
ability-guided progression with practice under the step rule, on (1) naming of practised
pictures and (2) how well practice is pitched.

**Prerequisites.** A clinical partner (a hospital or clinic SLP who identifies participants,
does the naming probes and has clinical responsibility); full IEC review; aphasia-friendly
consent; a decision on trial registration (check whether CTRI registration applies to a
software-delivered behavioural intervention). See [ethics-and-consent.md](ethics-and-consent.md).

## Design

Single-case experimental design (SCED), alternating treatments within participants,
replicated across participants. Reported against the SCRIBE 2016 checklist (Tate et al.,
co-published in *Aphasiology*).

| Phase | Length | What happens |
|---|---|---|
| Baseline | 3 probe sessions over 1-2 weeks | The SLP shows the 60-item probe set (below) on paper, no practice |
| Treatment | 6 weeks, 4 sessions a week, 20 pictures each | Home practice in RehabMind; mode alternates by session in a pre-registered random order |
| Probes during treatment | weekly | Same 60 items, scored by the SLP |
| Post and maintenance | at the end and 4 weeks later | Same 60 items |

Practice of about 20-30 minutes, 4 days a week, matches the dose that went with gains in
large app-based studies (Cordella et al. 2022) and in Big CACTUS (around 28 hours in total).

**Items.** From the catalogue and personally relevant pictures (added to the catalogue by
the team after SLP review), build a 60-item probe set per participant from items named
incorrectly at baseline: 40 practised (included in the constraint set's categories), 20
unpractised controls (excluded categories), matched on the difficulty audit's norms.

**Why alternate by session, not by item.** RehabMind sets progression per constraint
version, so the mode switches between sessions. The comparison is on session-level outcomes
and on probe accuracy for items practised mostly under each mode; a stricter design
(separate item sets per mode) would need a per-item mode, which is a future change.

## Participants

Inclusion: aphasia after stroke at least 6 months earlier; word-finding difficulty
confirmed by the SLP (for example on a naming test); able to see pictures and use a tablet
with or without help; able to give consent with supported communication.
Exclusion: severe comprehension difficulty preventing consent; progressive neurological
conditions; current intensive naming therapy.

## Outcomes

| Outcome | Measure | Source |
|---|---|---|
| Primary | Probe naming accuracy on practised items | SLP-scored probes |
| Secondary | Share of answers in the productive band; sessions rated "just right" | `study_data analyse` |
| Secondary | Adherence: sessions done of sessions planned; total practice time | app data |
| Secondary | Unpractised-item accuracy (generalisation) | probes |
| Descriptive | Shift in error types (semantic vs phonological) | app error types |
| Optional | WAB-R Aphasia Quotient, quality of life | SLP, before and after only |

Expect little change in WAB-R or quality of life: Big CACTUS found word-finding gains
without gains in conversation.

## Analysis

- Visual analysis of probe accuracy per phase (level, trend, overlap).
- Non-overlap of all pairs (NAP) and Tau-U between baseline and treatment, and between
  modes (`study_data analyse` reports NAP on session accuracy).
- Mixed-effects logistic regression on probe answers: correct ~ phase × practised + (1 |
  participant) + (1 | item).
- Benchmark: apps with practice of this kind improved trained items by about 13-16
  percentage points (iTalkBetter; Big CACTUS). Report the result whichever way it goes.

## Safety and stopping rules

- Sessions end whenever the participant chooses; "Stop for today" is always visible.
- The SLP checks in weekly. Stop a participant's participation on distress, fatigue that
  persists across sessions, or at their or their family's request.
- A clinician remains responsible for the patient's care throughout. RehabMind does not
  replace therapy.

## Pre-registration

Before the first baseline probe, register the protocol (OSF or CTRI, as decided), including
the random mode order, the probe items and the analysis above.
