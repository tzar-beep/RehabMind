# Ethics, data protection and consent

The team is in India. The ICMR National Ethical Guidelines for Biomedical and Health
Research Involving Human Participants (2017) require any research with human participants
or their data to be approved by a properly constituted ethics committee. For a student
project that is the institution's ethics committee (IEC), with a faculty member as principal
investigator.

**Check with your IEC before relying on these points** (the background research could not
verify them): which review route (exempt, expedited, full) the IEC's own procedures assign
to each phase; whether Clinical Trials Registry of India (CTRI) registration is expected for
Phase 3; and what the Digital Personal Data Protection Act 2023 requires of the project.

| Phase | Participants | Likely review route |
|---|---|---|
| 0 | none (synthetic data, simulation) | no review |
| 1 | clinicians rating materials | exempt or expedited |
| 2 | healthy adults 60+ | expedited |
| 3 | people with aphasia | full review |

## Ethics application outline

1. **Title, investigators, supervisor, clinical partner** (Phase 3).
2. **Background**: aphasia practice between therapy sessions; the industry review; what
   Phase 0 showed ([../README.md](../README.md)).
3. **Aims and design**: from the phase protocol.
4. **Participants**: inclusion and exclusion criteria, recruitment, sample size rationale
   (feasibility, not power).
5. **Risks and their management**: fatigue or frustration (short sessions, stop any time,
   difficulty kept within clinician limits); misleading feedback (deterministic scoring, AI
   text validated before display, no medical claims); privacy (below). Overall: minimal
   risk for Phases 1-2; low risk for Phase 3 with clinical oversight.
6. **Benefits**: none guaranteed; practice may help word finding.
7. **Consent**: written; for Phase 3 aphasia-friendly with supported communication and an
   optional family member present; capacity judged by the clinical partner.
8. **Data management**: below.
9. **Intended purpose**: RehabMind is a research prototype, not a medical device, and is not
   used for diagnosis or treatment decisions.

## Data management

- The app runs on the project's own server or a local machine. No cloud AI services; the
  language and speech models run locally.
- Voice recordings are encrypted, transcribed and deleted, normally within seconds
  ([../../privacy.md](../../privacy.md)). Only transcripts and scores are kept.
- Study accounts use study codes, not real names, as display names.
- Analysis files come from `app.scripts.study_data export`: pseudonymised with a keyed hash
  whose secret is held only by the principal investigator, study days instead of dates, no
  free-text answers.
- Consent forms and the code list linking study codes to people are stored on paper or
  encrypted storage, separately from study data, by the principal investigator.
- Retention: as the IEC requires (commonly 3-5 years), then deletion.

## Aphasia-friendly participant information (Phase 3 template)

Follow aphasia-friendly guidance: one idea per line, short everyday words, key words in
bold, a picture next to each point, plenty of white space, large font (at least 16-18 pt).
Read it together; the family member may help. Replace [ ] with your details and add a
picture to each line.

> **What is this?**
> We are testing a **picture naming app**.
>
> **What will I do?**
> **Name pictures** on a tablet. About **20 minutes**, **4 days a week**, for **6 weeks**.
> A speech therapist will **check your naming** each week.
>
> **Do I have to?**
> **No.** You can **stop at any time**. Your care will **not change**.
>
> **Is it safe?**
> The app **does not** give medical advice. Your therapist **stays in charge**.
>
> **What about my voice?**
> Your voice is turned into words, then **deleted**.
> We keep your **answers**, not your name.
>
> **Questions?** Call [name] on [number].

## Consent form (Phase 3 template)

Each statement with a picture and two large boxes, **YES** (tick) and **NO** (cross). The
participant marks each box; a witness signs if the participant cannot write.

| Statement | YES | NO |
|---|---|---|
| I understand what the study is | ☐ | ☐ |
| I know I can stop at any time | ☐ | ☐ |
| I agree to use the app at home | ☐ | ☐ |
| I agree to naming checks with the therapist | ☐ | ☐ |
| I agree my answers are used for the study (no name) | ☐ | ☐ |
| I want to take part | ☐ | ☐ |

Signature or mark, date, witness, person taking consent. Phases 1-2 use a standard written
consent form with the same points in plain language.
