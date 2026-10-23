# Demonstrating that adaptive personalization improves digital aphasia training: evidence, outcome measures, feasible evaluation designs

Scope note: these notes come from about 14 searches and fetches (October 2026). Claims are sourced inline. Items not verified in this session are in "Gaps" or marked as inference.

## 1. How established digital aphasia tools personalise, and how they showed benefit

### Takeaway
No major aphasia app has isolated adaptivity as the active ingredient. Constant Therapy, iTalkBetter and Big CACTUS each showed that a whole package (adaptive practice, high dose and self-management) beats workbooks, usual care or no therapy, mainly on trained-item naming. Effects on functional communication and quality of life are weak or absent. A "personalised vs fixed difficulty" comparison is therefore an open niche that RehabMind could plausibly claim.

### Cited Findings
**Constant Therapy (Kiran / Des Roches group; company-affiliated)**
- Des Roches et al. 2015 (Front Hum Neurosci): 51 people with aphasia (stroke or TBI) over 10 weeks. Both arms had one clinician session a week; the experimental arm also practised at home with the app. Both groups improved on therapy tasks, and the experimental group used the app more. — [Frontiers 2015 PDF](https://www.frontiersin.org/journals/human-neuroscience/articles/10.3389/fnhum.2014.01015/pdf)
- Braley et al. 2021 (Front Neurol), a phase II fully virtual RCT (NCT04488029): Constant Therapy-Research vs paper workbooks in chronic post-stroke aphasia, 36 enrolled and 32 completed (17 vs 15), stratified by severity, unblinded. — [PMC7907641](https://pmc.ncbi.nlm.nih.gov/articles/PMC7907641)
  - Adaptation mechanism: the "NeuroPerformance Engine". A passed exercise leads to a harder task on the same skill next session; a struggled exercise leads to an easier one. Staff could also edit homework manually. No formal thresholds or algorithm are published. — [PMC7907641](https://pmc.ncbi.nlm.nih.gov/articles/PMC7907641)
  - WAB-R AQ: +6.75 for CT-R (61.62 to 68.37) vs +0.38 for workbook. Mixed-model group × time interaction about 6.4 (p<0.01); the paper itself reports both 6.43 and 6.36. The authors call the gain clinically meaningful (above a 5-point threshold). WAB-LQ interaction 3.97 (p<0.01), WAB-CQ 4.01 (p<0.05). BTACT (cognition) and SAQOL-39 (quality of life) were not significant. No Cohen's d was reported. Dose was at least 30 min/day, 5 days/week. Authors were employees of the company, which funded the study. — [PMC7907641](https://pmc.ncbi.nlm.nih.gov/articles/PMC7907641); company summary [CT one-pager](https://constanttherapyhealth.com/wp-content/uploads/2024/03/201-Study-one-pager-elec.pdf)
  - Note: the control arm differed in more than adaptivity (feedback, staff-modifiable homework, tracking). The authors list these differences as limitations, so the trial does not isolate adaptive difficulty. — [PMC7907641](https://pmc.ncbi.nlm.nih.gov/articles/PMC7907641)
- Godlove et al. 2019 (Front Neurol), a retrospective analysis of 3,686 platform users: home and clinic users reached 90% task accuracy in a similar number of sessions (median 3), and home users practised more often. This is observational. — [Frontiers Neurol 2019](https://www.frontiersin.org/journals/neurology/articles/10.3389/fneur.2019.00140/pdf)
- Cordella et al. 2022 (JMIR), a retrospective cohort of 2,249 users over 10 weeks: improvements depended on dose. Higher-frequency groups had larger effects, and about 4 days/week was the optimal frequency. This shows that platform log data can support "engagement → outcome" analyses. — [JMIR 2022 / PMC9350823](https://pmc.ncbi.nlm.nih.gov/articles/PMC9350823)

**iTalkBetter / NUVA (UCL; Upton et al. 2024, eClinicalMedicine)**
- Design: phase II, item-randomised, repeated measures (NCT04566081). Each participant had 110 trained and 110 matched untrained words, with a no-therapy control block, then a 6-week therapy block, then 12-week maintenance. 32 recruited, 27 analysed, chronic aphasia (mean 83 months post-stroke). — [PMC11056404](https://pmc.ncbi.nlm.nih.gov/articles/PMC11056404/)
- Adaptation: real-time speech verification (NUVA) classifies each naming attempt. That result drives the next cue level (error-reducing phonological cues) and immediate feedback, and correct responses lead to harder items. The detailed rules are in the supplement. — [PMC11056404](https://pmc.ncbi.nlm.nih.gov/articles/PMC11056404/)
- Dose and engagement: target 60 h; achieved mean 45 h (SD 16), about 17,500 trials. 6 of 27 participants did under 30 h (time, illness, fatigue, motivation). Staff phoned and emailed to prompt participants. Gamified, and no dropouts were attributed to engagement. — [PMC11056404](https://pmc.ncbi.nlm.nih.gov/articles/PMC11056404/)
- Results: trained items +13% (about 29 words), untrained items no change. Block × item interaction F(1,26)=10.41, p=0.003, d=0.52, maintained at 12 weeks. Picture description showed a main effect of block (+4.4 information-carrying words, d=0.42) but no item interaction. — [PMC11056404](https://pmc.ncbi.nlm.nih.gov/articles/PMC11056404/)
- NUVA software paper: Barbera et al. 2021, Computer Speech & Language. — [UCL iTalkBetter page](https://www.ucl.ac.uk/icn/research/research-groups/neurotherapeutics/digital-interventions-neuro-rehabilitation-italkbetter)

**Big CACTUS (StepByStep; Palmer et al., Lancet Neurology 2019;18:821-833)**
- Design: 278 participants from 20 NHS trusts, three arms: usual care; usual care plus 6 months of daily computerised word-finding therapy, tailored per person, at home; usual care plus attention control (puzzle books). — [Sheffield CTRU impact](https://sheffield.ac.uk/ctru/impact/stroke); [NIHR Alert](https://evidence.nihr.ac.uk/alert/computerised-speech-and-language-therapy-can-help-people-with-aphasia-find-words-following-a-stroke)
- Word finding on personalised trained words: +16.2% vs usual care (95% CI 12.7 to 19.6) and +14.4% vs attention control (95% CI 10.8 to 18.1). Both exceeded the 10% minimal clinically important difference, and gains were maintained at 9 and 12 months. Functional communication, perceived communication, participation and quality of life did not improve. — [NIHR Alert](https://evidence.nihr.ac.uk/alert/computerised-speech-and-language-therapy-can-help-people-with-aphasia-find-words-following-a-stroke)
- Practice: about 28 h on average in the computer group vs 3.8 h of usual therapy. The therapy may be cost-effective for mild and moderate word-finding difficulty. — [Sheffield CTRU impact](https://sheffield.ac.uk/ctru/impact/stroke); [NIHR Alert](https://evidence.nihr.ac.uk/alert/computerised-speech-and-language-therapy-can-help-people-with-aphasia-find-words-following-a-stroke)

**Other tools**
- Lingraphica TalkPath: over 13,500 SLP-designed exercises. Benefit claims come from the company's own research, and I found no independent trial. — [Lingraphica TalkPath](https://lingraphica.com/talkpath-therapy-aphasia-app/)
- Tactus Therapy: over 20 apps based on SFA, PCA and VNeST techniques. I found no peer-reviewed efficacy study of the Naming Therapy app. — [Tactus](https://tactustherapy.com/?p=583)
- VITHEA (INESC-ID, Portugal): a research prototype virtual therapist using automatic speech recognition for word naming. The 2011 evaluation reports ASR accuracy, not patient outcomes. — [VITHEA project](https://www.hlt.inesc-id.pt/w/VITHEA_(Virtual_Therapist_for_Aphasia_treatment)); [ACL W11-2301](https://preview.aclanthology.org/fix_video/W11-2301.pdf)

### Inferences
- The field's accepted evidence pattern is: trained items improve with moderate effects (d about 0.5, or about 13-16 percentage points); untrained items and functional communication change little. RehabMind should state any claim about personalization against this pattern and should not promise functional gains.
- None of these trials compares adaptive vs fixed difficulty while holding dose and content constant. A dismantling comparison (same app, adaptive engine on vs off) is the cleanest way to answer "does personalization help?", and it is novel.
- In every trial, adaptivity is entangled with dose. A plausible mechanism for RehabMind to test is "personalization → more engagement/adherence → more dose → better naming", which is consistent with the dose-response findings of Cordella 2022.
- Constant Therapy's rule (pass → harder, struggle → easier, with clinician override) is very close to RehabMind's clinician-bounded rule. RehabMind can cite it as precedent for clinical acceptability.

### Gaps
- Exact Big CACTUS StepByStep difficulty algorithm, and whether percentage points or percent: not retrieved.
- Aphasia Scripts (Cherney et al.) and the "Language Therapy" apps: not searched this session. The original Aphasia Scripts studies were small, mostly pre-post or crossover; verify before citing.
- The exact iTalkBetter adaptive rules (in the supplementary material) were not read.

## 2. Adaptive difficulty theory: target success rates, challenge point, Elo/IRT

### Takeaway
There is solid theoretical support for keeping learners in a "desirable difficulty" band. In simple learning models the optimal training accuracy is about 85%; in motor learning the challenge point framework links optimal difficulty to the learner's skill. Elo-style learner models are validated and widely used in adaptive education. The specific numbers come from models, not aphasia patients, so RehabMind should treat its target band (for example 70-85%) as a tunable design parameter and justify it as such.

### Cited Findings
- Wilson, Shenhav, Straccia & Cohen 2019, "The Eighty Five Percent Rule for optimal learning" (Nature Communications 10:4646): for gradient-descent learners on binary classification, the optimal training error is about 15.87%, i.e. about 85% accuracy. It was demonstrated in artificial and biologically plausible neural networks. Wilson cautioned that the number came from simple simulated tasks and may not transfer directly to human learning. — [PMC6831579](https://pmc.ncbi.nlm.nih.gov/articles/PMC6831579); [Neuroscience News](https://neurosciencenews.com/learning-optimized-15171/)
- Challenge Point Framework (Guadagnoli & Lee 2004): harder tasks raise learning potential but lower performance during practice. The optimal challenge point maximises learning while keeping the performance cost of practice low, and depends on the learner's skill and task difficulty. — [Wikipedia summary](https://en.wikipedia.org/wiki/Challenge_point_framework)
- In stroke rehabilitation, protocols use the framework to match tasks to ability ("neither too easy nor too difficult") and warn that very hard tasks may cause compensatory patterns. A 2022 Frontiers paper builds an adaptive difficulty algorithm on the framework. A scoping review of 100 papers views the framework favourably but notes a lack of applied research. — [NCT01819506 protocol](https://cdn.clinicaltrials.gov/large-docs/06/NCT01819506/Prot_000.pdf); [Frontiers Hum Neurosci 2022](https://www.frontiersin.org/journals/human-neuroscience/articles/10.3389/fnhum.2022.968669/pdf); [Leeds Beckett scoping review](https://eprints.leedsbeckett.ac.uk/id/eprint/12281)
- Elo in adaptive learning (Pelánek 2016, Computers & Education): each answer is treated as a "match" between learner and item, and the same update estimates both learner skill and item difficulty. Pelánek argues it is simple, robust and effective. Follow-up work (UMUAI 2017) separates prior knowledge, current knowledge and question construction. In EDM comparisons, basic Elo predicted about as well as more complex models. — [Pelánek CAE-elo PDF](https://www.fi.muni.cz/~xpelanek/publications/CAE-elo.pdf); [UMUAI 2017](https://www.muni.cz/en/research/publications/1359654); [EDM 2015](https://is.muni.cz/publication/1316789)

### Inferences
- RehabMind's design (Elo/Rasch ability estimate plus a staircase rule) lets it target success probability directly. With a Rasch model, choosing items where P(correct) is about 0.75-0.85 is the formal version of the 85% rule and the challenge point. Errorless-learning traditions in aphasia argue for a higher target (fewer errors), so the band should stay inside clinician limits. This is a design argument, not established evidence.
- An "N correct → up, M incorrect → down" staircase converges to a predictable success rate. For example, a 3-up/1-down style rule converges near 79%, a classic psychophysics result (verify before citing). This can be shown analytically and in simulation (see Section 5).

### Gaps
- I found no aphasia-specific study that establishes an optimal practice accuracy. The errorless vs errorful learning literature in aphasia (e.g., Fillingham et al.) was not searched.
- Applications of IRT/Elo specifically in rehabilitation apps were not found this session.

## 3. Study designs, reporting standards and sample sizes

### Takeaway
Single-case experimental designs (SCEDs) are as common as group designs in aphasiology and are the realistic way for a student team to test personalised vs fixed difficulty. Strong options are an item-randomised within-subject design (as in iTalkBetter) or an alternating-treatments / multiple-baseline SCED, reported to SCRIBE 2016 and appraised with RoBiNT.

### Cited Findings
- SCRIBE 2016: a 26-item reporting checklist for single-case designs, developed through two Delphi surveys and a consensus meeting. It covers withdrawal/reversal, multiple baseline, alternating treatments, changing criterion, their combinations, and adaptive designs. It was co-published in Aphasiology and other journals, with an Explanation & Elaboration paper by Tate et al. 2016. SCED research is about as frequent as between-groups research in aphasiology, and its reporting is often incomplete. — [SCRIBE PMC4960517](https://pmc.ncbi.nlm.nih.gov/articles/PMC4960517); [PMC4873717](https://www.ncbi.nlm.nih.gov/pmc/articles/PMC4873717/)
- The item-randomised within-subject design works with a feasible n: iTalkBetter randomised items (not people) into trained and untrained sets matched on psycholinguistic variables and baseline accuracy, used a no-therapy control block, and detected d=0.52 with n=27. — [PMC11056404](https://pmc.ncbi.nlm.nih.gov/articles/PMC11056404/)
- Pilot RCT scale in this field: Braley 2021 had n=32 completers (enough to show WAB-AQ differences) but was not blinded and was confounded. — [PMC7907641](https://pmc.ncbi.nlm.nih.gov/articles/PMC7907641)

### Inferences
- **Recommended patient design (if ethics is approved):** a within-subject, item-randomised, two-condition SCED. Split each participant's personalised item pool into matched sets: Set A practised with the adaptive engine on, Set B with fixed difficulty (the clinician's starting level, no progression), Set C untrained. Interleave the conditions (alternating-treatments) or stagger them (multiple baseline across item sets), with three or more baseline probes. Primary outcome: probe naming accuracy on A vs B vs C. Secondary outcomes: time-in-target-band, session completion and frustration ratings per condition. Hold dose constant per condition, which avoids the dose confound in Braley.
- Analyse with visual analysis plus Tau-U or nonoverlap statistics per participant, and a mixed-effects logistic regression (item × session × condition, random effects for participant and item) across participants. Report against SCRIBE and self-rate with RoBiNT.
- A crossover (adaptive for 2 weeks, then fixed for 2 weeks, order randomised) is the simplest group-level alternative. Carry-over of learning makes naming outcomes hard to interpret, so it suits engagement and UX outcomes better than learning outcomes.
- Sample size: a pilot or feasibility study does not need a power calculation for efficacy. Common rules of thumb are about 12 per arm (Julious 2005) or about 30 total. For SCEDs, 3-6 participants with replications across behaviours is typical. These are standard methods heuristics not retrieved this session; verify before citing.

### Gaps
- RoBiNT scale (Tate et al. 2013/2015, 15 items: internal and external validity subscales): not retrieved. Verify the details.
- Pilot sample-size references (Julious 2005; Whitehead 2016; Lancaster 2004) were not verified this session.

## 4. Outcome measures

### Takeaway
Use a tiered battery. (1) Primary: proximal probe naming accuracy on trained vs untrained items, which is the field's standard and the outcome most likely to show an effect. (2) Process and engagement: time-in-target-band, adherence, session completion and dose, which are where personalization should act first. (3) Experience: SUS or UEQ, adapted to be aphasia-friendly. (4) Distal impairment and function (WAB-R AQ, CAT, CETI, ALA, SAQOL-39) only if patient access allows, and expect small or no changes.

### Cited Findings
- Trained vs untrained naming accuracy was the primary outcome in iTalkBetter (13% gain on trained items, none on untrained) and Big CACTUS (personalised word-finding list). — [PMC11056404](https://pmc.ncbi.nlm.nih.gov/articles/PMC11056404/); [NIHR Alert](https://evidence.nihr.ac.uk/alert/computerised-speech-and-language-therapy-can-help-people-with-aphasia-find-words-following-a-stroke)
- WAB-R AQ (5-point meaningful change cited), LQ and CQ, plus BTACT and SAQOL-39, were used in Braley 2021. — [PMC7907641](https://pmc.ncbi.nlm.nih.gov/articles/PMC7907641)
- Generalisation measure: information-carrying words in spoken picture description. — [PMC11056404](https://pmc.ncbi.nlm.nih.gov/articles/PMC11056404/)
- Engagement metrics already reported in the literature: hours achieved vs target (45/60 h), trial counts and share of participants under half the target dose; days per week of app use as a dose variable. — [PMC11056404](https://pmc.ncbi.nlm.nih.gov/articles/PMC11056404/); [Cordella JMIR 2022](https://pmc.ncbi.nlm.nih.gov/articles/PMC9350823)
- Big CACTUS found no change in functional communication, participation or quality of life despite naming gains. — [NIHR Alert](https://evidence.nihr.ac.uk/alert/computerised-speech-and-language-therapy-can-help-people-with-aphasia-find-words-following-a-stroke)
- SUS with people with aphasia: the ComVida app study used an adapted SUS after observed tasks. Users found the app easy, though some needed a communication partner. — [ComVida / AIMMA](https://comum.rcaap.pt/handle/10400.26/49059)

### Inferences
- **Personalization-specific process metrics RehabMind can log now:** proportion of trials in the target success band (e.g., 70-85%) per session; variance of session accuracy; number of sessions spent at ceiling (above 95%) or floor (below 50%); number of steps until the ability estimate stabilises; voluntary session length and return rate; within-session quit events after error streaks; clinician overrides. Comparing these under adaptive vs fixed conditions is the most direct evidence for "improves the training experience", which is exactly the expert's framing.
- For clinician acceptance, use TAM/UTAUT-style items (perceived usefulness, ease of use, intention to use, trust in the progression rule) plus qualitative interviews.
- For aphasia-friendly experience ratings, use short pictorial Likert scales (e.g., faces) about difficulty ("too easy / just right / too hard"), enjoyment and fatigue after each session. The "just right" rate is a direct patient-reported measure of the target band.

### Gaps
- Psychometric details (MCIDs) for CAT, CETI, ALA and UEQ were not retrieved. TAM/UTAUT use in SLP technology was not searched.

## 5. No-patient evidence options

### Takeaway
Without patients, the team can still build a credible three-part evidence package: (a) simulation with synthetic IRT learners, showing the engine keeps simulated users in the target band and estimates ability accurately vs fixed difficulty; (b) expert review and usability testing with SLPs (heuristics, SUS, TAM, think-aloud); (c) usability testing with healthy older adults, plus an aphasia-friendly design audit. This is honest "technical and usability validation", not efficacy evidence.

### Cited Findings
- Elo/IRT models can be evaluated by their predictive accuracy (as in EDM benchmark studies), which supports simulation-based and replay validation of RehabMind's estimator. — [Pelánek EDM 2015](https://is.muni.cz/publication/1316789); [Pelánek 2016](https://www.fi.muni.cz/~xpelanek/publications/CAE-elo.pdf)
- The 85% rule was itself derived and demonstrated purely through simulation with synthetic learners, which is a precedent for simulation evidence about difficulty policies. — [PMC6831579](https://pmc.ncbi.nlm.nih.gov/articles/PMC6831579)
- Classic usability methods (think-aloud, written task scenarios) exclude people with aphasia. Adaptations include short direct tasks and physical artefacts such as picture cards (Roper et al. 2018, ASSETS). — [City Research Online](https://openaccess.city.ac.uk/20242/)
- An aphasia accessibility model (AIMMA) was built from a literature review plus SLP interview and then used to adapt an app. Adapted and unadapted versions were compared. — [ComVida / AIMMA](https://comum.rcaap.pt/handle/10400.26/49059)
- Usability tests of the Aphasia Create app with six participants with aphasia produced design guidelines, and noted that older users are often unfamiliar with touch devices. — [Springer ASSETS 2015](https://www.springerprofessional.de/doi/10.1145/2700648.2811360)

### Inferences
- **Simulation study spec (doable in about 1-2 weeks):**
  - Generate synthetic learners with true ability θ (e.g., about N(0,1)) per objective, with a learning gain per practice trial (e.g., θ increases by a small amount on effortful success) and optional fatigue or noise. Items have Rasch difficulty b.
  - Compare three policies: (1) fixed difficulty at the clinician start level; (2) staircase only; (3) staircase plus Elo targeting P(correct) about 0.8, clamped to the clinician range.
  - Metrics: percentage of trials in the 70-85% band, ability-estimate RMSE and convergence trials, simulated learning gain after K trials, ceiling and floor exposure, and robustness to mis-set clinician ranges and to sudden ability drops (bad days).
  - Report with seeds, sensitivity analysis over N and M, and plots. This directly evidences that the algorithm does what it claims, but it is not a clinical benefit claim.
- Replay validation: if any de-identified response logs exist (e.g., from team pilots or healthy volunteers), fit Elo offline and report AUC or log-loss for next-response prediction vs baselines.
- SLP evaluation (5-8 SLPs): cognitive walkthrough of the clinician console, heuristic review, SUS, TAM items, and structured judgement of whether the progression decisions on simulated cases are clinically appropriate. Expert-agreement data like this is persuasive for the industry expert's concern.
- Healthy older adults (60+): usability, comprehension of LLM-worded instructions, and A/B of adaptive vs fixed on a deliberately hard novel task (e.g., naming rare or low-frequency items or a novel vocabulary) to measure in-band rate, enjoyment, perceived difficulty and session persistence. This gives an ethically simpler proxy for "personalization improves training experience". Be explicit that it is not an aphasia sample.
- Audit the LLM-generated wording against aphasia-friendly writing guidelines (short sentences, key words in bold, supporting images) and have SLPs rate a sample of messages for appropriateness and safety.

### Gaps
- No published simulation study of an aphasia-app difficulty engine was found. Consolidated, validated aphasia-friendly UX guidelines and validated aphasia SUS variants were not found.

## 6. Ethics and feasibility (including India / ICMR)

### Takeaway
Under ICMR's 2017 National Ethical Guidelines, any research involving human participants or their data needs review by a duly constituted ethics committee. In practice, student projects go through the institution's IEC, whose SOP decides whether exempt or expedited review applies. Pure simulation needs no ethics review. SLP surveys and usability tests and healthy-volunteer studies usually need at least IEC exempt or expedited review. Studies with people with aphasia need full review, an aphasia-accessible consent process, and likely a clinical partner.

### Cited Findings
- ICMR Bioethics Unit FAQ: "any biomedical or behavioural research involving human participants, their biological materials or data" requires approval of a duly constituted Ethics Committee (it refers to Section 3.15 of the 2017 guidelines). — [ICMR Bioethics FAQ](https://ethics.ncdirindia.org/FAQ.aspx)
- The 2017 guidelines added socio-behavioural research and responsible-conduct sections. Proposals are cleared by the Institutional Ethics Committee. — [ICMR Guidelines PDF (IIT Delhi mirror)](https://web.iitd.ac.in/~elangovan/ethics/doc/ICMR%20Guidelines%202018.pdf); [JNU summary](https://www.jnu.ac.in/node/1832)

### Inferences
- **Tiered plan:** Tier 0 is simulation and replay (no ethics needed). Tier 1 is SLP expert evaluation and healthy older adults (seek IEC exempt or expedited review; anonymous, minimal-risk). Tier 2 is a small SCED with 3-6 people with chronic aphasia via a hospital or SLP partner (full IEC review; aphasia-friendly consent with pictures; caregiver involvement; data protection under India's DPDP Act 2023, unverified here). If the study is framed as a clinical trial of an intervention, CTRI registration is likely expected; verify.
- To start the ethics paperwork early, a faculty supervisor as PI is typically required for student submissions. Check the institution's SOP.

### Gaps
- The exact ICMR 2017 provisions on exemption categories (e.g., Section 4 "exempted from review" for less-than-minimal-risk research) and the CTRI registration requirements for software interventions were not retrieved. Read the guidelines' ethical review procedures directly before relying on these points.

---

## Concrete recommendations (synthesis for report writer)
1. Reframe the claim as "personalization keeps practice in the productive difficulty band and sustains engagement" (testable now), not "personalization improves language recovery" (needs patients and a large n).
2. Run the synthetic-learner simulation (adaptive vs fixed vs staircase-only) and publish the in-band rate, estimator accuracy and robustness plots. Cite Wilson 2019, the challenge point framework and Pelánek's Elo work as the rationale.
3. Instrument the app now with personalization process metrics (in-band rate, ceiling and floor exposure, quits after error streaks, "just right" ratings, clinician overrides) so that any future study collects them automatically.
4. Run an SLP evaluation (5-8 SLPs: SUS, TAM, rating progression decisions on simulated cases and LLM feedback quality) and a healthy-older-adult A/B on usability and experience under IEC exempt or expedited review.
5. Pre-register a SCRIBE-compliant, item-randomised, within-subject SCED (adaptive vs fixed vs untrained item sets, dose held constant, n=3-6) as the next step with a clinical partner, using the iTalkBetter design as a template.
6. Benchmark expectations against the literature: trained-item gains of about 13-16 percentage points (d about 0.5) and weak transfer. Report evidence strength honestly; most commercial-app evidence is company-funded.
