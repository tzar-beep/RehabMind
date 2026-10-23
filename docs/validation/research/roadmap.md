# Turn RehabMind's safeguards into measurable clinical evidence

RehabMind's biggest gap is evidence, not engineering. The team has built sensible safeguards: a deterministic scorer, clinician-bounded progression, and an LLM wrapped in validators with fallback. But it has not yet measured whether any of them does what an aphasia clinician needs. The highest-priority fix is spoken-mode scoring. The same Whisper model family RehabMind uses (small.en) agreed with an SLP on only **73.6% of Philadelphia Naming Test trials** and transcribed just **20% of phonemic errors** correctly. It tends to "hear" the target word instead of the error, which means wrong answers get scored as correct ([SNL 2025](https://2025.neurolang.org/presentation/?id=706)). Next come three no-patient validations that a student team can finish in one semester:

- a norm-derived audit of the hand-assigned 1–5 difficulty levels;
- a "raw LLM vs shipped output" technical validation plus a blinded expert-panel (SLP) rating study using the content validity index (CVI);
- a synthetic-learner simulation showing that the adaptive engine keeps practice in a productive difficulty band better than fixed difficulty.

Only after these, and after review by an Institutional Ethics Committee (IEC) under the ICMR guidelines, should the team run a small single-case study with people with aphasia. It would compare adaptive and fixed item sets with dose held constant. The literature sets the ceiling for honest claims. Comparable apps improve naming of trained words by roughly **13–16 percentage points (d ≈ 0.5)**, with little transfer to untrained words or conversation ([iTalkBetter](https://pmc.ncbi.nlm.nih.gov/articles/PMC11056404/); [Big CACTUS](https://evidence.nihr.ac.uk/alert/computerised-speech-and-language-therapy-can-help-people-with-aphasia-find-words-following-a-stroke)). RehabMind should therefore claim "appropriate, safe, and keeps practice in the right difficulty band". It should not claim that it "improves recovery".

## Spoken scoring is the weakest link because Whisper repairs patients' errors

The expert's concern about whether the scoring is appropriate applies most strongly to speech mode. Whisper's built-in language model pulls atypical productions toward real words. On 5,300 annotated speech errors, WhisperX output the *intended* word for **81% of sound errors** and the actual error only **2%** of the time ([Alderete et al., Interspeech 2025](https://arxiv.org/html/2508.13060v1)). On aphasic picture naming specifically, small.en turned the patient's error into the target word in **29.95% of mismatches** ([SNL 2025](https://2025.neurolang.org/presentation/?id=706)). The broader numbers are worse still. Whisper's word error rate is **38.5% for people with aphasia vs 10.3% for matched controls** ([Sanguedolce et al. 2023](https://preview.aclanthology.org/fix_video/2023.clinicalnlp-1.24/)). It also invents whole phrases in about **1% of AphasiaBank clips**, more often for speakers with long pauses ([Careless Whisper, FAccT 2024](https://arxiv.org/abs/2402.08021v2)). For a naming exercise, every "repaired" error becomes a false accept: the patient hears "correct" for a word they did not produce. That inflates accuracy, and it feeds wrong evidence into the Elo/Rasch ability estimate that drives progression.

The established validation pattern comes from NUVA, the speech verifier used in iTalkBetter. One SLP provides the gold standard. A second, independent SLP sets the human ceiling. The machine is then reported on accuracy, false accepts, false rejects, and Gwet's AC1 (an agreement statistic that is stable when most answers are correct), broken down per patient and by severity. NUVA reached about **90.5–91.3% accuracy against an SLP, with a false-accept rate near 5%**. SLP–SLP agreement was **96.5% (AC1 0.938)**. The team deliberately chose a threshold with fewer false accepts because accepting wrong answers is the more harmful error ([Barbera et al. 2021](https://pmc.ncbi.nlm.nih.gov/articles/PMC8117974/)). RehabMind should copy this structure exactly and treat the **false-accept rate as its primary safety metric**.

The scoring scheme itself needs a clinical anchor. The Philadelphia Naming Test (PNT) scores the *first complete attempt* (1 if correct, 0 if not) and classifies errors as semantic, formal, mixed, unrelated, or neologism ([PNT scoring guide](https://rehabilitationresearch.jefferson.edu/content/dam/academic/research/rehabilitation-research-institute/pnt-glossary-of-terms-scoring-guide.pdf); [NCT02005016 protocol](https://cdn.clinicaltrials.gov/large-docs/16/NCT02005016/Prot_SAP_000.pdf)). These categories can already be assigned automatically from transcripts. The ParAlg algorithm reaches a weighted **F1 of .87** using lexicality, phonological similarity and semantic-embedding similarity ([Casilio et al. 2023](https://pmc.ncbi.nlm.nih.gov/articles/PMC10461785)), and its 12,000-response output is public on Figshare ([MAPPD-12K](https://asha.figshare.com/articles/online_resource/ParAlg_A_paraphasia_algorithm_Casilio_et_al_2023_/22087763/1)). SLTs disagree mainly on whether plurals and derived forms of the target count as correct ([Barbera et al. 2021](https://pmc.ncbi.nlm.nih.gov/articles/PMC8117974/)). A written scoring manual should therefore settle those cases, along with how synonyms and typed misspellings are handled. RehabMind's fuzzy match can silently accept a formal error such as "cap" for "cat" as a typo. A written rule on that one point would answer much of the expert's question.

**What to build:**

- Write a 1–2 page scoring manual reviewed by one SLP. It should specify that the first complete attempt is scored, that self-corrections are logged separately, and how variants, plural/derivative forms, misspelling tolerance and the response window are handled.
- Add a PNT-style error classifier. Use CMUdict/g2p phoneme edit distance for formal similarity, embeddings or WordNet for semantic similarity, and a frequency list to separate real words from non-words.
- Log response latency and the cue level at which each item was produced.
- Harden the ASR. Never pass the target word in `initial_prompt` or hotwords. Enable VAD, set `condition_on_previous_text=False` and temperature 0, and reject low-confidence segments based on `no_speech_prob`, `avg_logprob` and compression ratio. When confidence on the target word is low, label the result "uncertain — confirm" rather than "correct".
- Label speech-mode correctness as "ASR heard the target", and never pool typed and spoken accuracy.

**How to validate scoring:**

1. Build a text test set of 300–500 responses with at least 30 examples per error class, seeded from MAPPD-12K where items overlap.
2. Have two SLPs (or one SLP and one supervised SLP student) blind-label a stratified sample of about 200 responses.
3. Record healthy volunteers producing scripted phonemic and semantic errors and long pauses. Measure how often ASR transcribes the error faithfully vs repairs it vs gets it wrong.
4. With a faculty-sponsored AphasiaBank account, rerun the same metrics locally on real aphasic speech. Students cannot apply for access themselves, and the data must not be uploaded to services that retain it ([AphasiaBank access](https://talkbank.org/aphasia/access.html); [TalkBank rules](https://talkbank.org/share/rules.html)).

## Difficulty levels and exercise formats need grounding in norms and theory

Hand-assigned 1–5 difficulty is the easiest place for a reviewer to push back. In aphasic naming, raw word frequency matters surprisingly little once correlated variables are controlled. Age of acquisition, imageability and length matter for many patients, visual complexity does not, and individual patients' predictors differ from the group's ([Nickels & Howard 1995](https://researchers.mq.edu.au/en/publications/aphasic-naming-what-matters/)). Free norms cover most of what is needed:

- the Glasgow Norms: imageability, familiarity and age of acquisition for 5,553 words, under CC BY ([PMC6538586](https://www.ncbi.nlm.nih.gov/pmc/articles/PMC6538586/));
- the Kuperman age-of-acquisition ratings (30,121 words) and Brysbaert concreteness ratings (37,058 words) ([McMaster](https://experts.mcmaster.ca/scholarly-works/57348); [McMaster](https://experts.mcmaster.ca/scholarly-works/57343));
- MultiPic's 750 normed drawings, extended to 32 languages with name-agreement statistics ([PMC9304413](https://pmc.ncbi.nlm.nih.gov/articles/PMC9304413));
- the BOSS photo norms ([PMC4161371](https://www.ncbi.nlm.nih.gov/pmc/articles/PMC4161371/)).

Hindi is absent from the 32-language MultiPic set. The research turned up no Hindi aphasia naming norms, so any Hindi expansion needs local norming first.

**What to build:** map each of the 61 stimuli to these norms. Compute a weighted z-score composite, with age of acquisition, name agreement and imageability weighted most, then length, frequency, and visual complexity last. Bin the composite into quintiles to get levels 1–5. Then report agreement between the hand-assigned and norm-derived levels (Spearman ρ and weighted κ) as the first validation artefact. Flag low-name-agreement pictures, where a "wrong" answer may be a valid alternative name, and add common alternative names from the norm response distributions to the accepted variants. Seed each patient's item difficulties with the norm-derived prior and let the Rasch/Elo model update them from that patient's own history. This builds the individual-difference finding directly into the design. Licences for most of these norm sets were not confirmed and must be checked before redistribution.

The cueing and feedback design is defensible but needs explicit limits. Semantic Feature Analysis (SFA) has medium-to-large effects on trained items and small effects on untrained ones ([Oh et al. meta-analysis](https://pure.ewha.ac.kr/en/publications/treatment-efficacy-of-semantic-feature-analyses-for-persons-with-/)). Errorless (decreasing-cue) and errorful (increasing-cue) approaches give broadly equivalent gains, and patients with better memory and self-monitoring respond better to both ([Fillingham et al.](https://research.manchester.ac.uk/en/publications/treatment-of-anomia-using-errorless-vs-errorful-learning-are-fron/)). Errorful practice *without* feedback has produced no improvement, so allowing errors is only defensible if feedback follows ([PMC4105211](https://pmc.ncbi.nlm.nih.gov/articles/PMC4105211)). Items that responded to shorter phonemic cues before therapy were the ones most likely to be learned ([Conroy et al. 2012](https://shura.shu.ac.uk/11614/)).

**What to build for cueing:**

- Keep "meaning first, then first sound" as the default hierarchy, extended to five cue levels: SFA-style feature prompt, sentence completion, first phoneme, first syllable, then a whole-word model plus repetition. End every trial with the correct word.
- Add a clinician toggle for "errorless mode".
- Log the cue level reached as a graded score.
- Choose treatment targets "in the zone": items the patient names after a short cue but not spontaneously.

**Measure generalisation instead of assuming it.** Generalisation reaches only untrained words that share semantic or phonological features with trained words ([Kendall et al. 2019](https://repository.up.ac.za/bitstream/2263/75004/1/Kendall_Phonomotor_2019.pdf)), and Big CACTUS found no conversation benefit ([Palmer et al. 2019](https://eprints.whiterose.ac.uk/149577)). Each patient therefore needs three lists: a treated set, an untrained related probe set (never cued), and an untrained unrelated control set. Probe these at three or more baselines and then at fixed intervals.

**Restructure the sentence-level tasks around verbs.** Verb Network Strengthening Treatment (VNeST) trains a verb with its agent and patient ("who can measure? what do they measure?"). It generalised to sentence production for trained and related untrained verbs in all 4 participants ([Edmonds & Kiran 2006](https://aphasiology.pitt.edu/1734/)). Treatment of Underlying Forms (TUF), which trains complex structures first, has group-level meta-analytic support across 46 participants ([JSLHR 2021](https://pubs.asha.org/doi/10.1044/2021_JSLHR-21-00131)). Response Elaboration Training (RET) expands the patient's own utterance and is scored with correct information units (CIUs) ([Wambaugh et al. 2018](https://pubs.asha.org/doi/10.1044/2018_AJSLP-17-0152)).

For the word-tile builder, this means verb-centred templates graded SV → SVO → SVO+adjunct → passive/wh-question, with role-reversal and semantically related distractor tiles so that errors are diagnostic. For scene description, the LLM asks one RET-style expansion question at a time, and the patient's output is scored with CIUs, CIUs per minute and percentage of complete utterances using documented rules, not free-form LLM judgement.

Dosage belongs in the app as well. The best outcomes cluster around **20–50 total hours delivered on 3–5+ days per week** ([RELEASE 2022](https://www.research.ed.ac.uk/en/publications/dosage-intensity-and-frequency-of-language-therapy-for-aphasia-a-/)). Higher intensity brings more dropout ([Cochrane, Brady et al. 2016](https://cora.ucc.ie/handle/10468/6604)). RehabMind should show cumulative hours against a clinician-set target and log adherence as an outcome.

## The LLM safety layer needs "raw vs shipped" numbers and a blinded SLP panel

No published study has rated LLM-generated aphasia exercises, hints or feedback against an explicit rubric with reported error rates. That makes a well-designed rating study of RehabMind's outputs a real contribution rather than a formality. The nearest precedent shows both the risk and the method. Fifteen SLPs rated ChatGPT-4 outputs. Aphasia therapy stimuli scored well (accuracy **M = 2.80/3**). Speech-sound stimuli scored worst (**M = 1.60**), largely because the model produced invalid or non-existent words ([Birol et al. 2025](https://pmc.ncbi.nlm.nih.gov/articles/PMC12122639/)). RehabMind's catalogue-constrained generation plus validators is a design answer to exactly that failure, but only measurement makes it a finding.

The core experiment is cheap. Generate 500–1,000 outputs per output type across three prompt versions, at least five seeds, all difficulty levels and all exercise types. Report each metric twice: for the raw LLM output and for the output actually shipped after validation, retry and fallback. The gap between raw and shipped is the evidence that the safety layer works. The metrics are:

| Metric | Computation |
| --- | --- |
| Hallucination rate | Targets, distractors or objects that are not in the catalogue or item |
| Validator pass rates | First-pass schema, clinical and safety pass rates; mean retries; fallback percentage |
| Validator precision | Checked against about 100 SLP-labelled outputs: does the validator reject what an SLP would reject? |
| Answer-key stability | Whether the correct answer stays the same across seeds |
| Summary faithfulness | Rate of claims in clinician summaries that cannot be traced to a logged database value |

Aphasia-friendly writing guidance can be turned into automatic checks. The consensus calls for short sentences, common words, simple grammar and white space ([Aphasia Institute](https://aphasia.ca/?p=47615)). In one study, **87.2% of 40 adults with aphasia** preferred an aphasia-friendly leaflet ([Rose et al. 2011](https://pubmed.ncbi.nlm.nih.gov/21682542/)). However, the evidence is mostly qualitative and gives no numeric cut-offs ([ACNR](https://acnr.co.uk/download/21839)), so every threshold must be labelled a heuristic agreed by the panel. The checks are:

- maximum words per sentence;
- share of instruction words with a SUBTLEX Zipf frequency of 4 or higher ([SUBTLEX-UK](https://eprints.nottingham.ac.uk/2947/));
- no passive voice, negation or embedded clauses, detected with spaCy;
- hints never contain the target word or a morphological variant of it;
- the first-sound cue matches the target's phoneme rather than its first letter ("phone" starts with /f/);
- no praise attached to an incorrect answer;
- a lexicon of infantilising phrases, plus an exclamation-mark count.

The last two checks put into practice the Supported Conversation for Adults with Aphasia principle of "acknowledging competence" ([Kagan et al. 2001](https://pubs.asha.org/doi/10.1044/1092-4388(2001/051))).

The human layer is a content-validity study. Three to six SLPs rate 40–60 stratified items for relevance on a 4-point scale and on rubric dimensions: adult tone, specificity, no false praise, cue order, and simplicity. Raters are blinded to whether each item came from the LLM or the deterministic fallback, so the result can read "LLM items rated no worse than the clinician-authored fallback". Report I-CVI (target **≥ 0.78** with six or more experts; stricter for smaller panels, which needs checking against Lynn 1986), S-CVI/Ave (**≥ 0.90**) and the modified kappa (**≥ 0.74**) ([contentValidity vignette](https://bioconductor.statistik.tu-dortmund.de/cran/web/packages/contentValidity/vignettes/getting-started.html); [MetricGate](https://metricgate.com/calculator/content-validity-index-cvi)).

Plan for disagreement between raters. A comparable panel rating GPT-4 stuttering programmes had **ICC = 0.45** ([Anadolu](https://avesis.anadolu.edu.tr/yayin/88900846-16c2-4b4f-9a73-026962846830/content-validity-of-ai-generated-stuttering-assessment-and-intervention-programs-based-on-expert-review-a-comparative-analysis-across-age-groups-and-language-versions)), so run a calibration round with anchor examples first. A two-round mini-Delphi with the same SLPs can agree the rubric and the validator thresholds, which documents where the clinical rules came from. An LLM judge can screen objective criteria at scale, but it should complement human raters rather than replace them, especially on tone ([PMC12837895](https://www.ncbi.nlm.nih.gov/pmc/articles/PMC12837895/)). It must be calibrated against the SLP subset and must not be Qwen itself.

Package all of this as a reporting card that follows TRIPOD-LLM ([PubMed 39779929](https://pubmed.ncbi.nlm.nih.gov/39779929/)) and CHART ([EQUATOR](https://www.equator-network.org/reporting-guidelines/reporting-guideline-for-chatbot-health-advice-studies-the-chart-statement/)). It should record the model digest and quantisation, decoding settings, versioned prompts, validator rules with their rationale, the failure taxonomy from the audit log, rater characteristics and limitations. It should also include an explicit intended-purpose statement. Intended purpose is the central test for software-as-medical-device status ([Emergo on MDCG 2019-11 rev.1](https://www.emergobyul.com/news/european-revision-primary-software-guidance-mdcg-2019-11-revision-1-small-changes-meaningful)). The clinician summaries are the component most likely to look like decision support, so label them as drafts that require clinician review.

## Personalization should be shown to keep practice in the right band, not to speed recovery

The expert's second question is whether personalization "actually improves the patient's training experience". The field has never isolated adaptivity as the active ingredient, so this is open ground. Constant Therapy's phase II trial raised WAB-R AQ by **+6.75 vs +0.38** for workbooks, but the control arm also differed in feedback, tracking and dose. The trial was also company-funded and unblinded ([Braley et al. 2021](https://pmc.ncbi.nlm.nih.gov/articles/PMC7907641)). Its "pass → harder, struggle → easier, clinician can override" rule closely matches RehabMind's, which is useful precedent for clinical acceptability but not evidence that adaptivity works. iTalkBetter gained **13% on trained items (d = 0.52)** with no change on untrained items after a mean of 45 hours of practice ([Upton et al. 2024](https://pmc.ncbi.nlm.nih.gov/articles/PMC11056404/)). Large usage logs show that gains depend on dose, with about 4 days per week optimal ([Cordella et al. 2022](https://pmc.ncbi.nlm.nih.gov/articles/PMC9350823)). The plausible causal chain to test is therefore "personalization → in-band practice and engagement → more dose → naming gains". The first two links can be tested without patients.

**Simulation (no ethics review needed, 1–2 weeks).** Generate synthetic Rasch learners with true ability θ, small per-trial learning gains, noise and "bad days". Compare three policies: fixed difficulty at the clinician's starting level, the staircase alone, and the staircase plus Elo targeting P(correct) ≈ 0.8 within clinician bounds. Report:

- the percentage of trials inside the target band;
- exposure to ceiling (above 95%) and floor (below 50%);
- ability-estimate RMSE and the number of trials to convergence;
- simulated learning gain;
- robustness to badly set clinician ranges.

The theoretical anchors are the simulation-derived "85% rule" (whose author cautions that it may not transfer to humans) ([Wilson et al. 2019](https://pmc.ncbi.nlm.nih.gov/articles/PMC6831579)), the challenge point framework ([Guadagnoli & Lee](https://en.wikipedia.org/wiki/Challenge_point_framework)), and evidence that basic Elo predicts learner responses about as well as more complex models ([Pelánek](https://is.muni.cz/publication/1316789)). No aphasia study establishes an optimal practice accuracy. The 70–85% band is a tunable design parameter, not a cited fact, and the errorless-learning tradition argues for a higher band for some patients.

**Instrumentation (build now).** Log every personalization process metric per session, so any future study collects them automatically:

- in-band rate;
- variance of session accuracy;
- sessions spent at ceiling or floor;
- quits after streaks of errors;
- voluntary session length and return rate;
- clinician overrides;
- a pictorial post-session rating of "too easy / just right / too hard", which is a direct patient-reported measure of the target band.

Add a per-item-set switch that turns adaptation on or off. That switch is what makes the later comparison possible.

**Human evaluations without patients.** Have 5–8 SLPs do a cognitive walkthrough of the clinician console and complete SUS, TAM-style trust items, and structured ratings of whether progression decisions on simulated cases were clinically appropriate. Have healthy adults aged 60+ do usability testing and an adaptive-vs-fixed A/B on a deliberately hard novel vocabulary task, measuring in-band rate, enjoyment and persistence, and stating clearly that this is not an aphasia sample. Think-aloud methods exclude people with aphasia, so later patient testing needs adaptations such as short direct tasks and picture cards ([Roper et al. 2018](https://openaccess.city.ac.uk/20242/)).

**Patient study (Phase 3).** Use a single-case experimental design (SCED), with items rather than people randomised, modelled on iTalkBetter. For each of 3–6 participants, split a personalised item pool into matched Set A (adaptive), Set B (fixed difficulty) and Set C (untrained). Hold dose constant across A and B, take three or more baseline probes, and compare probe naming accuracy across the sets as the primary outcome. Analyse with visual analysis, Tau-U, and a mixed-effects logistic model with random effects for participant and item. Report against SCRIBE 2016, the 26-item checklist co-published in *Aphasiology* ([PMC4960517](https://pmc.ncbi.nlm.nih.gov/articles/PMC4960517)). A crossover (adaptive then fixed) suits engagement outcomes better than learning outcomes, because learning carries over between periods. WAB-R AQ and quality-of-life measures are secondary. Expect little change in them, as Big CACTUS saw no gains in functional communication or quality of life ([NIHR](https://evidence.nihr.ac.uk/alert/computerised-speech-and-language-therapy-can-help-people-with-aphasia-find-words-following-a-stroke)).

## A four-phase plan, gated by ethics review and by thresholds

ICMR's guidelines require that "any biomedical or behavioural research involving human participants, their biological materials or data" be approved by a duly constituted ethics committee ([ICMR Bioethics FAQ](https://ethics.ncdirindia.org/FAQ.aspx)). Student projects go through the institution's IEC, usually with a faculty member as principal investigator ([ICMR 2017 guidelines](https://web.iitd.ac.in/~elangovan/ethics/doc/ICMR%20Guidelines%202018.pdf)). The IEC's own standard operating procedure decides whether surveys and healthy-volunteer work qualify for exempt or expedited review. Three points were not verified in this research and must be checked directly before relying on them: the ICMR exemption categories, whether CTRI registration is needed for a software intervention, and obligations under India's DPDP Act 2023.

| Phase | Ethics | Build in codebase | Evaluate | Report / threshold |
| --- | --- | --- | --- | --- |
| **0: Technical validation** (weeks 1–6) | None (simulation, synthetic data, public datasets) | Scoring manual; PNT error classifier; ASR hardening and confidence gating; norm-derived difficulty; aphasia-friendly validator checks; evaluation harness; summary-faithfulness checker; personalization logging and adaptive on/off switch; intended-purpose statement | Raw-vs-shipped LLM grid (500–1,000 outputs per type); scorer test set (≥30 per error class); synthetic-learner simulation; difficulty agreement analysis | Hallucination and fallback rates, raw vs shipped; per-class confusion matrix; in-band %, RMSE; ρ/κ between hand-assigned and norm-derived difficulty |
| **1: Expert validation** (weeks 6–12) | IEC exempt or expedited | Rater interface with blinding; export of samples | 3–6 SLP CVI panel plus mini-Delphi; 2-SLP blind scoring of about 200 responses; SLP console walkthrough with SUS/TAM | I-CVI ≥ 0.78, S-CVI/Ave ≥ 0.90, k* ≥ 0.74; scorer–SLP agreement within one McHugh band of SLP–SLP (design choice); false-accept rate ≤ ~5% (NUVA level) |
| **2: Proxy users** (weeks 10–16) | IEC expedited | Pictorial difficulty ratings; consent screens | Healthy 60+ usability test and adaptive-vs-fixed A/B; scripted-error recordings for ASR fidelity; AphasiaBank replay (faculty access) | Faithful vs repaired error transcription; WER; hallucination on pauses; in-band %, "just right" %, persistence |
| **3: Aphasia SCED** (next term) | Full IEC review; clinical partner; picture-supported consent; check CTRI | Treated/probe/control lists; dose locking | n = 3–6 item-randomised SCED, adaptive vs fixed vs untrained | Tau-U and mixed-model effects per SCRIBE; adherence and hours; benchmark against +13–16 points on trained items |

Most thresholds in the table are conventions or design choices. Only the CVI and modified-kappa thresholds and the NUVA false-accept benchmark come from cited sources, and the write-up should say so. For people with aphasia, Phase 3 needs aphasia-accessible consent with pictures and simple language, caregiver involvement, local storage of audio (which fits RehabMind's local-model design), and an explicit stopping rule for fatigue or distress.

Make claims honestly, and match each claim to its phase:

- **After Phase 0:** "the safety layer reduces hallucinated content from X% to Y%" and "the engine keeps simulated learners in band Z% of the time vs W% for fixed difficulty".
- **After Phase 1:** "SLPs rated generated content as relevant (S-CVI/Ave = …) and no worse than the hand-written fallback".
- **After Phase 3 only:** "in n = 4 participants, items practised adaptively were named better / no better than fixed-difficulty items".

Never pool typed and spoken accuracy. Never describe spoken "correct" as anything more than "ASR heard the target". Never imply effects on conversation or functional communication. Label RehabMind a research prototype, not a medical device. Evidence from commercial apps is mostly company-funded, and saying so strengthens the team's credibility.

## Conclusion

The reviewer's comment covers two questions that most aphasia-tech projects blur together: whether the content and scoring are appropriate, and whether personalization helps. RehabMind can answer the first one almost entirely without patients, because appropriateness is a property of artefacts that SLPs and automated checks can rate. The second splits further. "Personalization keeps practice in the productive band and sustains engagement" can be tested by simulation, logging and proxy users. "Personalization improves language outcomes" needs a dose-controlled patient comparison, which no published aphasia app has yet run.

The most consequential finding is a risk rather than an opportunity. With an off-the-shelf small.en model, speech mode is currently capable of systematically telling patients they were right when they were not. Fixing and measuring that comes before any claim about LLM quality or adaptivity, because a progression engine fed with false accepts personalizes to the wrong patient. A team that leads with its false-accept rate, its raw-vs-shipped hallucination numbers and a pre-registered single-case design will have a stronger and more novel validation story than a team that claims efficacy early.
