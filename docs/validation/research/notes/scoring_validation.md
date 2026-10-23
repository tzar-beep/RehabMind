# Validating automated scoring of aphasic naming/speech responses (RehabMind)

Research date: 2026-10-23. English focus. RehabMind context: picture naming + sentence building, typed or spoken, faster-whisper small.en ASR, deterministic NLP scorer (normalisation, fuzzy match vs canonical + variants, concept coverage, word order), mostly correct/incorrect output.

## (a) Clinically recognised response-scoring schemes (PNT, BNT, self-corrections, partial responses) and which categories can be auto-classified from text

### Takeaway
The Philadelphia Naming Test (PNT; Roach et al., 1996, MRRI/Jefferson) is the reference taxonomy: score the *first complete attempt*, then classify errors as semantic, formal, mixed, unrelated, neologism (plus no-response/description/other). Most of these categories have already been auto-classified from transcripts (ParAlg, weighted F1 .78-.87), using lexicality (frequency norms), phonological similarity and word-embedding semantic similarity, so RehabMind can adopt this route rather than invent a scheme.

### Cited Findings
- PNT scoring rules originate from Roach et al. (1996) "The Philadelphia Naming Test: Scoring and rationale"; the complexity of the scoring guidelines is cited as a barrier to clinical use — [Casilio et al. 2023, JSLHR, via search summary](https://pubs.asha.org/doi/10.1044/2023_JSLHR-22-00439)
- MRRI/Jefferson publishes the PNT scoring protocol, glossary of terms/scoring guide and administration instructions as PDFs — [MRRI PNT page](https://mrri.org/?p=869); [PNT glossary/scoring guide](https://rehabilitationresearch.jefferson.edu/content/dam/academic/research/rehabilitation-research-institute/pnt-glossary-of-terms-scoring-guide.pdf); [admin instructions](https://rehabilitationresearch.jefferson.edu/content/dam/academic/research/rehabilitation-research-institute/pnt-admin-instructions.pdf) (the scoring-protocol PDF URL returned 404 on 2026-10-23)
- "Complete Attempt" is defined as the first response that is minimally CV or VC (schwa not counted as a vowel); scorers are told to be liberal in identifying fragments and bypassing them to find the true first complete attempt, and to re-listen to the recording for acoustic/prosodic cues of self-interruption — [PNT glossary/scoring guide](https://rehabilitationresearch.jefferson.edu/content/dam/academic/research/rehabilitation-research-institute/pnt-glossary-of-terms-scoring-guide.pdf) (via search summary)
- Consequence: in conventional PNT scoring a later self-correction does not rescue an incorrect first complete attempt; fragments that are self-interrupted are labelled fragments — [PNT glossary/scoring guide](https://rehabilitationresearch.jefferson.edu/content/dam/academic/research/rehabilitation-research-institute/pnt-glossary-of-terms-scoring-guide.pdf) (via search summary; verify against full PDF)
- A treatment-trial protocol uses dichotomous 1/0 scoring of the first complete attempt, ignoring minor sound distortions/additions/omissions, and converts item scores into a logit-scaled ability score for PNT short forms — [Dosage and Predictors of Naming Treatment Response, NCT02005016 protocol](https://cdn.clinicaltrials.gov/large-docs/16/NCT02005016/Prot_SAP_000.pdf)
- PNT error categories: formal, semantic, mixed, neologistic, unrelated; classification first decides real-word vs non-word, then phonological and semantic relatedness to target; neologisms may be phonologically related ("tat" for hat) or not ("blil" for hat) — [Fergadiotis et al. 2016, AJSLP](https://pubs.asha.org/doi/10.1044/2016_AJSLP-15-0147); [PMC10461785 (Casilio et al. 2023)](https://pmc.ncbi.nlm.nih.gov/articles/PMC10461785)
- Automated components: lexicality judged via word-frequency norms (>97% accurate), phonological similarity ~91% accurate, semantic classification 86-90% — [Fergadiotis, Gorman & Bedrick 2016 (figshare)](https://asha.figshare.com/articles/figure/Algorithmic_Classification_of_Paraphasias_Fergadiotis_et_al_2016_/14963559); [OHSU record](https://ohsu.elsevierpure.com/en/publications/algorithmic-classification-of-five-characteristic-types-of-paraph)
- 2016 algorithm tested on 7,111 paraphasias from the MAPPD database and replicated human scoring for major categories with high accuracy — [Fergadiotis et al. 2016](https://ohsu.elsevierpure.com/en/publications/algorithmic-classification-of-five-characteristic-types-of-paraph)
- ParAlg (Casilio, Fergadiotis et al., JSLHR 2023): multinomial classification of 11,999 archival PNT responses into six paraphasia types; weighted-average F1 .87 when lexical responses are orthographically transcribed vs .78 with all-phonemic transcription; human-side disagreements mostly about phonological similarity, ParAlg-side errors mostly about semantic similarity; released MAPPD-12K output on Figshare — [ParAlg (OHSU)](https://ohsu.elsevierpure.com/en/publications/paralg-a-paraphasia-algorithm-for-multinomial-classification-of-p); [Figshare resource](https://asha.figshare.com/articles/online_resource/ParAlg_A_paraphasia_algorithm_Casilio_et_al_2023_/22087763/1); [PMC10461785](https://pmc.ncbi.nlm.nih.gov/articles/PMC10461785)
- Semantic component originally used word2vec; a 2022 preprint describes replacing it to improve semantic-similarity judgments — [EasyChair preprint](https://easychair.org/publications/preprint/Vlsk)
- In the NUVA study SLT ground truth used six response categories (Correct, No Response, Filler, Phonological Error, Circumlocution, Other) collapsed to Correct/Incorrect, single-word response within a 6 s limit; authors note SLTs may differ on whether derivatives (plurals, nominalisations, verbalisations) are correct — [Barbera et al. 2021, NUVA (PMC)](https://pmc.ncbi.nlm.nih.gov/articles/PMC8117974/)

### Inferences
- RehabMind's binary correct/incorrect output is clinically defensible (dichotomous first-complete-attempt scoring is standard in treatment trials), but the project must state explicitly which response it scores (first complete attempt vs final/best attempt) and how it treats plurals/derivatives, synonyms and minor articulation errors, because these are the known points of SLT disagreement.
- Text-only auto-classification feasible for RehabMind: (1) no response / empty; (2) correct (exact/variant); (3) semantic (real word, high WordNet/embedding similarity, low phonological overlap); (4) formal (real word, phonologically similar e.g. normalised phoneme edit distance via CMUdict/g2p, low semantic similarity); (5) mixed (both); (6) unrelated (real word, neither); (7) neologism (non-word per dictionary/frequency list); (8) circumlocution/description (multi-word response containing target-concept attributes). This mirrors the ParAlg pipeline.
- A typed response cannot show phonological errors the same way as speech; typed answers will show orthographic (spelling) errors, which are a different construct (written naming). Fuzzy-matching that accepts misspellings may silently accept formal/phonological-type errors — needs an explicit policy.
- Delays: PNT/NUVA use a fixed response window (NUVA 6 s); RehabMind should log latency and could flag "delayed correct" separately rather than collapse it.

### Gaps
- Exact PNT phonological-similarity criterion (shared-phoneme rule) and the full official scoring protocol could not be retrieved (404); report writer should cite Roach et al. 1996 and the MRRI glossary.
- Boston Naming Test scoring details (spontaneous vs stimulus-cued vs phonemic-cued correct, 20 s rule) were not retrieved in this session; no source gathered.
- No source found on dialect handling in PNT scoring.
- McKinney-Bock & Bedrick and "CompCoder" were not located in searches; no verified numbers.

## (b) Prior work on automatic scoring / ASR for aphasic speech and how it was validated

### Takeaway
The best-validated naming verifier (NUVA, 2021) reached 89.5-91.3% accuracy vs an SLT, against SLT-SLT agreement of 96.5% (Gwet's AC1 0.938), with per-patient false-accept and false-reject rates reported; Whisper on aphasic speech shows WER ~38.5% vs 10.3% for controls, and a 2025 PNT study using the same model as RehabMind (WhisperX small.en) matched an SLP only 73.6-75.4% of the time, transcribing just 20% of phonemic paraphasias correctly.

### Cited Findings
**NUVA / iTALKbetter (Barbera et al., Computer Speech & Language 2021)**
- 8 British-English speakers with chronic post-stroke anomia, 220 items, 1,760 recordings; primary SLT scored online without feedback — [NUVA (PMC8117974)](https://pmc.ncbi.nlm.nih.gov/articles/PMC8117974/)
- Human-human: Gwet's AC1 0.938 (95% CI 0.923-0.953), 96.53% agreement; per-patient AC1 0.850-0.992. Gwet's AC1 chosen over kappa; interpreted with McHugh's benchmarks (.80-.90 strong; >.90 almost perfect) — [NUVA (PMC8117974)](https://pmc.ncbi.nlm.nih.gov/articles/PMC8117974/); [arXiv 2102.05408](https://arxiv.org/pdf/2102.05408)
- Vs SLT1: NUVA fixed acc 0.905 (FP 0.049, FN 0.046, F1 0.855); NUVA adapted acc 0.913 (FP 0.057, FN 0.031); SLT2 acc 0.965 (FP 0.016, FN 0.018); Google STT baseline acc 0.882 (FP 0.020, FN 0.098) — [NUVA (PMC8117974)](https://pmc.ncbi.nlm.nih.gov/articles/PMC8117974/)
- 10-fold CV: mean accuracy 0.895 (SD 0.03, range 0.836-0.936), FP 0.066, FN 0.039 — [NUVA table](https://pmc.ncbi.nlm.nih.gov/articles/PMC8117974/table/tbl0009)
- Fixed threshold chosen for iTALKbetter trial deployment because of lower false-positive rate; NUVA significantly worse than SLT2 for the most severely impaired patients (P2, P3, P5); authors call results proof of concept — [NUVA (PMC8117974)](https://pmc.ncbi.nlm.nih.gov/articles/PMC8117974/)
- Prior systems as summarised by NUVA: VITHEA (Abad et al. 2013) 82% average accuracy (69-93%); Ballard et al. 2019 ~75-80% (65.1-82.8%) — NUVA text and table disagree; Wade et al. 2001 ~80% with small vocabulary and speaker training — [NUVA (PMC8117974)](https://pmc.ncbi.nlm.nih.gov/articles/PMC8117974/)

**VITHEA (Portuguese)**
- Online "virtual therapist" with word-naming via keyword spotting on a hybrid HMM/MLP recogniser, tuned per patient; evaluated on recorded therapy sessions — [Abad et al., Interspeech 2012](https://papers.cool/venue/abad12@interspeech_2012@ISCA); [2011 workshop paper](https://preview.aclanthology.org/fix_video/W11-2301.pdf)

**Whisper on post-stroke aphasia**
- Whisper WER 38.5% in people with aphasia vs 10.3% in age-matched controls (p<0.001); worse with more severe aphasia and left frontal lesions — [Sanguedolce et al., ClinicalNLP 2023](https://preview.aclanthology.org/fix_video/2023.clinicalnlp-1.24/)
- Fine-tuned Whisper on stroke data gave large WER reduction and, tested on AphasiaBank, beat prior ASRs trained on that database — [Sanguedolce et al., Interspeech 2024 "When Whisper listens to aphasia"](https://spiral.imperial.ac.uk/entities/publication/3fc3eced-8426-4cd4-936f-06ff3ecee7b9) (exact WERs not extracted; PDF unreadable via fetch)
- Baseline Whisper performs poorly on single-word clinical (naming) utterances; fine-tuning cuts WER substantially but zero-shot generalisation to TORGO (dysarthria) is limited — [Application of Whisper in Clinical Practice: Post-Stroke Speech Assessment during a Naming Task, NeurIPS 2025 workshop](https://neurips.cc/virtual/2025/124949)
- Whisper Large-V3 on English AphasiaBank: CER from 25.28% (unannotated words) to 87.82% (filled pauses); prompting cut filled-pause CER to 44.04% — [ETS Montreal, "Evaluating ASR for aphasia"](https://pure.etsmtl.ca/en/publications/evaluating-asr-for-aphasia-a-framework-for-clinically-relevant-tr/) (via search summary)

**PNT + WhisperX small.en (most directly relevant to RehabMind)**
- Parchure, Coslett et al. (UPenn), SNL 2025 poster: 3,660 PNT trials from 21 people with post-stroke aphasia transcribed by WhisperX small.en vs experienced SLP; 73.63% match (75.43% excusing homophones/spelling/plurals); SLP-SLP match >80%; semantic errors transcribed correctly 96.36%, phonemic errors only 20.17%; mismatches: introducing phonemic errors 38.65% (e.g., "base" for "vase"), lexicalising the error to the target 29.95%, skipped trial 23.62%; authors attribute this to the model auto-correcting lower-quality speech — [SNL 2025 poster C7](https://2025.neurolang.org/presentation/?id=706)

**Spontaneous-speech / paraphasia detection**
- Le, Licata & Mower Provost (Speech Communication 2018): ASR on AphasiaBank spontaneous speech, new recognition benchmark, quantitative measures robust to ASR errors that predict WAB-R AQ without manual transcripts — [Le et al. 2018 PDF](https://talkbank.org/aphasia/publications/2018/Le18.pdf); [Interspeech 2017](https://www.isca-archive.org/interspeech_2017/le17_interspeech.html)
- Perez et al. 2023: seq2seq model trained end-to-end for ASR + paraphasia detection, improving word- and utterance-level detection — [arXiv 2312.10518](https://arxiv.org/abs/2312.10518v1); Perez et al. 2024: multiclass paraphasia detection; single-sequence model beats GPT baselines — [arXiv 2407.11345](https://www.arxiv.org/abs/2407.11345)
- 2026 CLAP-based word-naming recognition reports up to 90% accuracy, beating classification and ASR baselines on French post-stroke data — [arXiv 2602.14584](https://arxiv.org/html/2602.14584v1)
- Core-lexicon automatic scoring reliability study (AphasiaBank) — [Dalton et al. 2021 poster](https://talkbank.org/aphasia/posters/21NAC-Dalton.pdf) (results not extracted)

### Inferences
- The accepted validation pattern in this literature is: SLT gold standard, a second independent SLT to establish the human ceiling, report accuracy + FP (false accept) + FN (false reject) + chance-corrected agreement, per patient and by severity, plus comparison with an off-the-shelf ASR baseline. RehabMind should copy this structure.
- Because RehabMind uses small.en, the UPenn PNT result (~74% match, 20% phonemic errors captured) is the most realistic prior expectation for spoken naming; speech-mode correctness scores must not be presented as equivalent to typed-mode scores.

### Gaps
- Exact WER numbers for Le & Provost 2018 and Sanguedolce 2024 not extracted (PDFs not machine-readable via fetch).
- Fraser et al. (spontaneous speech/PPA classification), McKinney-Bock & Bedrick, CompCoder: not retrieved; no verified figures.
- No study found that reports Cohen's kappa between an automated naming scorer and clinicians for English typed responses.

## (c) Validation metrics, gold-standard construction and a concrete protocol with limited clinician access

### Takeaway
Use a two-layer validation: (1) ASR fidelity ("does the transcript match what was said?") and (2) scorer agreement ("does the score match an SLP's first-complete-attempt judgment?"), reporting percent agreement, Cohen's kappa and Gwet's AC1 (robust when most responses are correct), and separately false-accept vs false-reject rates, benchmarked against SLP-SLP agreement on the same items.

### Cited Findings
- NUVA used Gwet's AC1 rather than kappa and McHugh's interpretation bands; human-human agreement provides the ceiling for the machine — [NUVA (PMC8117974)](https://pmc.ncbi.nlm.nih.gov/articles/PMC8117974/)
- False positives (accepting wrong answers) were treated as more harmful in deployment: the lower-FP threshold was chosen for the iTALKbetter trial — [NUVA (PMC8117974)](https://pmc.ncbi.nlm.nih.gov/articles/PMC8117974/)
- ParAlg reported weighted F1 against human codes and analysed the direction of disagreements (phonological vs semantic) — [PMC10461785](https://pmc.ncbi.nlm.nih.gov/articles/PMC10461785)
- AphasiaBank access: password-protected, open to researchers/educators/clinicians who work with aphasia; apply via email with affiliation and intended use; students cannot apply themselves — a faculty advisor must request access per student with start/end dates (granted < 1 year) — [AphasiaBank](https://talkbank.org/aphasia/); [Access levels](https://talkbank.org/aphasia/access.html)
- Ground rules: protected data may not be reposted or shared with non-members; commercial users may develop algorithms but data may not be included in models; uploads to web services only if the service guarantees no retention — [TalkBank Ground Rules](https://talkbank.org/share/rules.html)
- AphasiaBank site carries a notice that the repository is under review for possible modification under US Administration directives (as of 2026) — [AphasiaBank](https://talkbank.org/aphasia/)
- MAPPD-derived PNT response data (MAPPD-12K ParAlg output) is publicly released on Figshare — a source of real PNT error responses (text/phonemic) with human codes — [Figshare](https://asha.figshare.com/articles/online_resource/ParAlg_A_paraphasia_algorithm_Casilio_et_al_2023_/22087763/1)
- SFU Speech Error Database (SFUSED) provides 5,300 annotated word and phonological errors usable to test ASR fidelity — [Alderete et al., Interspeech 2025](https://arxiv.org/html/2508.13060v1)

### Inferences (proposed protocol for RehabMind)
1. **Write a scoring manual first** (1-2 pages): which attempt is scored (recommend first complete attempt, with "final attempt" logged separately as a self-correction flag), accepted variants/synonyms per item, plural/derivative policy, typed misspelling tolerance, response window. Have one SLP review it — this alone answers "is the scoring appropriate for aphasia rehab".
2. **Text-level scorer validation (no audio, low clinician burden)**: build a test set of typed/transcribed responses per item: correct, accepted variants, and simulated errors in each PNT class (semantic, formal, mixed, unrelated, neologism, circumlocution, no response, partial/fragment). Seed realistic errors from the public MAPPD-12K PNT responses where items overlap. Target ~300-500 responses so each error class has >=30 examples. Report confusion matrix, false-accept rate (wrong scored correct) and false-reject rate (correct scored wrong) per class.
3. **Clinician labelling**: 2 SLPs (or 1 SLP + 1 trained SLP student) independently label a stratified subset (e.g., 200 items) blind to the scorer. Compute SLP-SLP agreement (percent, Cohen's kappa, Gwet's AC1) then scorer-SLP agreement; success criterion: scorer-SLP agreement not more than one McHugh band below SLP-SLP, and FP rate <= ~5% (NUVA-level). Adjudicate disagreements and fold into the manual.
4. **ASR fidelity layer**: record healthy volunteers reading/naming plus deliberately producing scripted phonemic and semantic errors (simulated paraphasias) and pauses; measure (a) WER, (b) "faithful vs corrected vs incorrect" rate on error tokens (SFUSED categories), (c) hallucination on silence/long pauses. With AphasiaBank access (via supervisor), run the same metrics on real aphasic speech locally (no upload, per ground rules).
5. **Report per modality and severity**; never pool typed and spoken accuracy; for continuous outputs (e.g., concept coverage for sentences) use ICC against SLP ratings.
6. Kappa paradox: with mostly-correct responses kappa can be low despite high agreement — report AC1 alongside kappa (as NUVA did).

### Gaps
- No primary source gathered on formal sample-size calculations for kappa/AC1 (e.g., Sim & Wright, Donner & Eliasziw); the 200-500 item figures above are inferences anchored on NUVA (1,760 attempts, 8 patients) and ParAlg scale, not a power calculation.
- No source found for ICC thresholds in aphasia discourse scoring in this session.

## (d) Risks of Whisper on aphasic/dysarthric speech and mitigations

### Takeaway
Whisper's language-model prior pulls atypical productions toward real target words: in PNT data WhisperX small.en lexicalised phonemic errors into the target ~30% of mismatches and captured only 20% of phonemic paraphasias, which would directly inflate a naming scorer's accuracy (false accepts); Whisper also hallucinates whole phrases (~1% of AphasiaBank segments), more so with long pauses.

### Cited Findings
- "Careless Whisper" (FAccT 2024): ~1% of transcriptions of AphasiaBank audio (13,000+ clips) contained entire hallucinated phrases/sentences absent from the audio; 38% of hallucinations contained explicit harms; hallucinations disproportionately occur for speakers with longer non-vocal durations, common in aphasia — [arXiv 2402.08021](https://arxiv.org/abs/2402.08021v2); [Koenecke et al. PDF](https://talkbank.org/aphasia/publications/2024/Koenecke24.pdf); [Language Log](https://languagelog.ldc.upenn.edu/nll/?p=66682)
- WhisperX on 5,300 annotated speech errors: for sound errors 81% "Corrected" (output the intended unspoken word), only 2% "Faithful" (output the actual error), 17% incorrect; word errors 43% corrected, 31% faithful — i.e., ASR mostly erases phonological errors — [Alderete et al., Interspeech 2025](https://arxiv.org/html/2508.13060v1)
- In PNT aphasic speech, WhisperX small.en lexicalised phonemic errors to the target in 29.95% of mismatches and captured phonemic errors only 20.17% of the time; authors attribute this to auto-correction — [SNL 2025 poster](https://2025.neurolang.org/presentation/?id=706)
- Baseline Whisper is poor on single-word utterances; fine-tuning on clinical data helps but generalises poorly to unseen populations — [NeurIPS 2025 workshop](https://neurips.cc/virtual/2025/124949)
- Mitigation research: sparse-autoencoder steering reduced hallucination on non-speech audio from 72.63% to 14.11% (Whisper small) — not tested on disordered speech — [Interspeech 2026 Aparin et al. listing](https://papers.cool/venue/aparin26@interspeech_2026@ISCA); [arXiv 2606.07473](https://arxiv.org/pdf/2606.07473)
- Prompting reduced filled-pause CER on AphasiaBank (87.82% -> 44.04%) — [ETS "Evaluating ASR for aphasia"](https://pure.etsmtl.ca/en/publications/evaluating-asr-for-aphasia-a-framework-for-clinically-relevant-tr/)

### Inferences (mitigations for RehabMind)
- Do **not** pass the target word in Whisper's initial_prompt/hotwords for naming items — that biases toward the target and increases false accepts.
- Use VAD (faster-whisper vad_filter), condition_on_previous_text=False, temperature 0, and reject segments with high no_speech_prob / low avg_logprob / high compression ratio; treat low-confidence word-level probabilities on the target word as "uncertain — confirm" rather than correct.
- Show the transcript to the patient/clinician and allow manual override; log audio for audit (with consent).
- Treat spoken-mode "correct" as "ASR heard the target" and label it as such; flag that phonemic paraphasias are likely under-detected.
- Validate with the faithful/corrected/incorrect metric on scripted error productions, and report false-accept rate as the primary safety metric.

### Gaps
- No published Whisper results on aphasic speech specifically using faster-whisper (CTranslate2) were found; small.en behaviour inferred from the WhisperX small.en poster (WhisperX uses faster-whisper backend — not verified in this session).
- No study found that quantifies how target-word prompting changes false-accept rate in naming.
