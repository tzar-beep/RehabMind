# Validating LLM-generated therapy content for aphasia (RehabMind)

Scope: how to evaluate and demonstrate that LLM-generated exercise text, hints, feedback and clinician summaries are appropriate for post-stroke aphasia rehabilitation, plus evaluation designs a student project can run. Research date: 2026-10-23. Preprints are marked [PREPRINT]. Where I could only see an abstract or a secondary source, it says so.

## 1. Content validity methods (expert panel, CVI, Delphi, rubrics)

### Takeaway
The standard, low-cost way to show "clinical appropriateness" is an expert-panel content-validity study. Each generated item gets a 4-point relevance rating, and you compute I-CVI per item and S-CVI/Ave for the set. Conventional cut-offs are I-CVI >= 0.78 with 6 or more experts and S-CVI/Ave >= 0.90, often reported with a chance-corrected modified kappa. A modified Delphi round can refine the rubric itself.

### Cited Findings
- I-CVI >= 0.78 is the usual threshold, attributed to Lynn (1986) and Polit & Beck (2006), and it applies to panels of 6 or more experts. Secondary sources give a stricter cut-off for 3–5 experts (0.83 in some; Lynn's original guidance for very small panels is usually reported as requiring all experts to agree, I-CVI = 1.00). Check the primary papers before citing a number for small panels. — [contentValidity R package vignette (CRAN)](https://bioconductor.statistik.tu-dortmund.de/cran/web/packages/contentValidity/vignettes/getting-started.html); [MetricGate CVI docs](https://metricgate.com/docs/content-validity-index-cvi/)
- S-CVI/Ave (the mean of the item I-CVIs) >= 0.90 is the conventional benchmark for excellent scale-level content validity (Polit, Beck & Owen 2007, *Res Nurs Health* 30(4):459–467). — [MetricGate CVI calculator](https://metricgate.com/calculator/content-validity-index-cvi)
- Citations: Lynn MR, *Nursing Research* 35(6):382–385 (1986). Polit & Beck, *Res Nurs Health* 29(5):489–497 (2006). The Polit–Beck modified kappa (k*) adjusts I-CVI for chance agreement, and k* >= 0.74 is cited as "excellent". The 0.78/0.90 values are conventions, not fixed rules. — [CASRAI content validity guide](https://www.casrai.org/guides/content-validity); [paperguide CVI glossary](https://paperguide.ai/research-glossary/content-validity-index/)
- Precedent in SLP for LLM content: 12 GPT-4-generated stuttering assessment and intervention programmes (Turkish and English) were reviewed by 12 certified fluency SLPs. Most items were rated appropriate or highly appropriate, but inter-rater reliability across the whole panel was poor (ICC = 0.45), with single-rater ICC 0.65. — [Anadolu Univ. record: content validity of AI-generated stuttering programmes](https://avesis.anadolu.edu.tr/yayin/88900846-16c2-4b4f-9a73-026962846830/content-validity-of-ai-generated-stuttering-assessment-and-intervention-programs-based-on-expert-review-a-comparative-analysis-across-age-groups-and-language-versions)
- Modified Delphi is the method behind the major AI reporting guidelines. DECIDE-AI had 123 experts in round 1, 138 in round 2 and a 16-person consensus meeting. CHART had 531 stakeholders in an asynchronous Delphi plus 48 in synchronous panels. This shows Delphi is the accepted way to build consensus criteria, though those panels are far larger than a student project can manage. — [EQUATOR: DECIDE-AI](https://www.equator-network.org/reporting-guidelines/reporting-guideline-for-the-early-stage-clinical-evaluation-of-decision-support-systems-driven-by-artificial-intelligence-decide-ai/); [EQUATOR: CHART](https://www.equator-network.org/reporting-guidelines/reporting-guideline-for-chatbot-health-advice-studies-the-chart-statement/)

### Inferences
- Feasible design A (content validity). Recruit 3–6 SLPs, or SLP students supervised by an SLP. Sample about 40–60 generated items, stratified by exercise type x difficulty x prompt version, and include fallback (deterministic) items as a hidden comparator. Rate each on 4-point relevance and on 2–4 rubric dimensions (see Section 4). Compute I-CVI, S-CVI/Ave, modified kappa, and ICC or Gwet's AC1 for agreement. The stuttering study's ICC of 0.45 suggests planning for low agreement: report it honestly and use a short calibration/training round with anchor examples first.
- Blind raters to the source (LLM vs. hand-written/fallback vs. catalogue). That turns a descriptive CVI into a comparative non-inferiority-style check: "LLM items rated no worse than clinician-authored items."
- A light "mini-Delphi" (2 rounds, same 3–6 SLPs) can be used to agree the rubric and the automated-check thresholds, rather than to rate items. This documents where the clinical rules in the validator came from.

### Gaps
- I did not retrieve the Lynn (1986) or Polit & Beck (2006) primary texts. The exact small-panel thresholds (all-agree vs. 0.83) need verifying.
- I found no published minimum panel size specific to SLP material review. Lynn's commonly reported range is 3–10 experts, but I did not verify this against the primary source here.

## 2. Published work (2022–2026) on LLMs in SLP and aphasia, and LLM-as-judge

### Takeaway
Evidence is thin and early-stage. No published study I found formally validates LLM-generated aphasia therapy exercises against SLP ratings. The nearest work consists of SLP Likert ratings of ChatGPT output across SLP tasks, expert CVI of GPT-generated stuttering programmes, aphasia-related LLM benchmarks/simulations, and case reports. That makes a well-designed SLP rating study of RehabMind outputs a genuine contribution. LLM-as-judge agrees reasonably with clinicians on objective criteria, but should only supplement humans for subjective or affective qualities such as tone.

### Cited Findings
- Birol et al., *Eur Arch Otorhinolaryngol* 2025;282(6):3267–3280. ChatGPT-4.0 was tested on 6 task types (report writing, assessment materials, clinical decision support, therapy stimulus creation, therapy planning, education materials) across 7 disorder areas, including aphasia. 15 practising SLPs (4 master's, 11 doctoral students) rated accuracy, comprehensiveness and relevance on a 3-point scale, with ICC 0.755. Therapy stimulus creation for aphasia scored accuracy M = 2.80. Speech-sound stimuli were worst (M = 1.60), largely because of invalid or non-existent Turkish words, which is a hallucination failure directly relevant to word-level exercise generation. Stated limitations include no gold standard, author-written prompts, one model only, and a 150-minute survey that deterred participation. — [PMC12122639](https://pmc.ncbi.nlm.nih.gov/articles/PMC12122639/)
- JSLHR (2026, open access): a preclinical simulated-dialogue evaluation of LLMs producing clinician language for Response Elaboration Training in aphasia. It reports that LLMs differ systematically in how well they adapt clinician language to impaired speech, and it is framed as guidance before clinical translation. Full text was blocked (HTTP 403), so this is from the search snippet only. — [JSLHR 10.1044/2026_JSLHR-26-00031](https://pubs.asha.org/doi/10.1044/2026_JSLHR-26-00031)
- [PREPRINT] Roll, Kries, Jin, Wang, Finley, Sumner, Shain, Gwilliams. "The Text Aphasia Battery (TAB): A Clinically-Grounded Benchmark for Aphasia-Like Deficits in Language Models", arXiv:2511.20507 (Nov 2025). It adapts the Quick Aphasia Battery into a text-only test, built with SLPs. Its section headings include an automated evaluation prompt and feature-level inter-rater reliability between automated and human scoring. The PDF body was not machine-readable, so the numbers were not verified. — [arXiv 2511.20507](https://arxiv.org/pdf/2511.20507)
- Frontiers in Rehabilitation Sciences (2025) case report: ChatGPT used with an adult with fluent aphasia to improve written output. The authors note that using LLMs as a direct component of aphasia intervention is a new area. — [Frontiers fresc.2025.1600145](https://www.frontiersin.org/journals/rehabilitation-sciences/articles/10.3389/fresc.2025.1600145/pdf)
- 2025 study benchmarking small language models on interpreting aphasic speech found compact models such as Qwen2.5:1.5b competitive. This is relevant because RehabMind uses Qwen2.5-3B. — [TalkBank: Kollapally 2025](https://talkbank.org/aphasia/publications/2025/Kollapally25.pdf)
- [Workshop paper] Du & Juefei-Xu (ICLR 2023 tiny paper): SLP critique of ChatGPT responses for receptive and expressive language therapy use cases. — [OpenReview PDF](https://openreview.net/pdf/d71591f5d16f8658962344f73065cc3a9a420c49.pdf)
- [PREPRINT] A 2025 paper on paediatric SLP vignettes argues that general LLMs lack domain knowledge and may hallucinate, and proposes retrieval-augmented generation (RAG). This is a proof of concept, not a rating study. — [arXiv 2511.08600](https://arxiv.org/pdf/2511.08600v1)
- LLM-as-judge, review: LLM judges align best with clinicians on objective criteria (factuality, grammaticality, internal consistency) and remain limited on subjective and affective judgments. The role should be "supportive rather than substitutive". Known biases include verbosity, position and self-enhancement. — [Artificial Authority: LLM judges in healthcare (PMC12837895)](https://www.ncbi.nlm.nih.gov/pmc/articles/PMC12837895/)
- [PREPRINT] German clinical open-response study (Jul 2026): the best LLM rater reached kappa 0.694 against a physician–physician ceiling of 0.709, with wide CIs. The authors conclude that statistical alignment does not guarantee clinical caution. — [arXiv 2607.01103](https://arxiv.org/abs/2607.01103)
- [PREPRINT] "Same Verdict, Different Reasons" (2026): LLM judges and clinicians can reach the same completeness verdict for different reasons, so whether LLMs replicate clinical judgment remains open. — [arXiv 2604.16383](https://arxiv.org/pdf/2604.16383)

### Inferences
- RehabMind can position its evaluation as filling a stated gap. Birol et al. found stimulus generation the weakest and most variable task and called for supervision. RehabMind's catalogue-constrained generation plus validators is a design answer to the invalid-word failure they observed, and that claim can be tested quantitatively (Section 6).
- If an LLM judge is used (e.g., a larger local model rating tone and clarity), calibrate it against the SLP ratings on a shared subset. Report kappa or ICC between judge and humans, and use it only to scale the screening of objective criteria. Do not use the same Qwen model as the judge (self-enhancement bias).

### Gaps
- I found no study (peer-reviewed or preprint) that rated LLM-generated aphasia naming/comprehension exercises, cue hierarchies, or feedback with an explicit rubric and error-rate reporting.
- I could not read the full text of the JSLHR 2026 article or of TAB, so their metrics are unverified.

## 3. Aphasia-friendly language guidelines that can become automated checks

### Takeaway
There is good consensus on simple language: short sentences, common vocabulary, simple grammar, one idea per sentence, bolded key words, white space and a large sans-serif font. The evidence base is mostly qualitative and preference-based, so thresholds coded into RehabMind should be presented as guideline-derived heuristics, not validated cut-offs.

### Cited Findings
- Aphasia Institute guidance (2024) recommends common vocabulary, shorter sentences, simpler grammar, larger bold key words and more white space. It also notes that such materials are meant to support conversation rather than stand alone. — [Aphasia Institute guidance](https://aphasia.ca/?p=47615)
- A review notes "good consensus" on simple language, large sans-serif font, bold key words, minimal text volume and spacing. The Stroke Association guide (Herbert et al. 2012) is among the most thorough, covering short sentences, simple vocabulary, sans-serif font and matching images. However, the evidence "largely originates from qualitative studies" of preferences, and the benefit of pictures is contested. — [ACNR article](https://acnr.co.uk/download/21839); [MMU short report](https://e-space.mmu.ac.uk/606883/1/Short%20report%20with%20revisions%20final%20version.pdf)
- Rose et al. 2011 (Aphasia friendly written health information: content and design characteristics), PubMed 21682542: among 40 adults with aphasia, 87.2% ranked the aphasia-friendly aphasia leaflet as most liked, and 56.4% did so for the stroke leaflet. — [PubMed 21682542](https://pubmed.ncbi.nlm.nih.gov/21682542/) (figures from search snippet; the PubMed page did not render)
- A 2025 practical guide to translating scientific publications into aphasia-friendly summaries. — [PubMed 40589613](https://pubmed.ncbi.nlm.nih.gov/40589613/); [ASHA Perspectives 2025](https://pubs.asha.org/doi/10.1044/2025_PERSP-24-00141)
- SUBTLEX-UK (van Heuven, Mandera, Keuleers & Brysbaert 2014, QJEP) gives subtitle-based British English frequencies that predict lexical decision better than the BNC. The Zipf scale = log10(frequency per billion words). Zipf 1–3 is low frequency and 4–7 is high frequency. — [SUBTLEX-UK (Nottingham eprints)](https://eprints.nottingham.ac.uk/2947/); [SUBTLEX-UK search app](https://shiny.psychology.nottingham.ac.uk/lpzwjv/SUBTLEX-UK/)

### Inferences
These are automated checks RehabMind could add to the validator. Thresholds would be set by the SLP mini-Delphi, not by the literature.
- Sentence length: maximum words per sentence and maximum sentences per prompt or hint (e.g., <= 10–12 words in patient-facing text).
- Lexical frequency: the proportion of content words with Zipf >= 4 (SUBTLEX-UK or SUBTLEX-US), and the minimum Zipf of any non-target word. Target words can be low-frequency by design for difficulty grading, but instruction words should not be.
- Syntax: no passive voice, no embedded or relative clauses, and no negation in instructions. These can be detected with a dependency parser such as spaCy.
- Readability: Flesch–Kincaid / Flesch Reading Ease as a secondary metric only. They are unreliable on very short texts.
- One instruction per sentence, imperative or simple question form, and no idioms or figurative language (wordlist-based).
- The lexical frequency of target words also serves as a difficulty-grading check: is "easy" actually higher-frequency than "hard"?

### Gaps
- I found no validated numeric cut-off (e.g., "<= N words per sentence") in the primary aphasia literature. The guidance is qualitative.
- No readability formula has been validated for people with aphasia.

## 4. Feedback tone (motivational, errorless, non-infantilising) and how to rate it

### Takeaway
Two bodies of work apply. Errorless and cueing-hierarchy naming therapy shapes what hints and feedback should do, and it shows feedback itself may matter less than practice. Supported Conversation for Adults with Aphasia (SCA) provides the construct "acknowledging competence" (adult tone, respect), which can be turned into a rated rubric dimension.

### Cited Findings
- Fillingham, Sage & Lambon Ralph (2005–2006) ran single-subject comparisons. Errorful naming with a phonological cue and errorless naming both improved naming for most participants. In a 7-participant crossover, omitting feedback had no detectable effect. — [Western Univ. EBP review (Angle)](https://www.uwo.ca/fhs/lwm/teaching/EBP/2006_07/Angle.pdf); [Manchester research portal](https://research.manchester.ac.uk/en/publications/further-explorations-and-an-overview-of-errorless-and-errorful-th/)
- Conroy, Sage & Lambon Ralph 2009: errorless learning for verb and noun naming was as effective as errorful/hierarchical cueing and more time-efficient. Group studies showed a trend (Conroy 2009) or a reliable advantage (McKissock & Ward 2007) for errorless methods. — [Manchester: errorless and errorful therapy for verb and noun naming](https://research.manchester.ac.uk/en/publications/errorless-and-errorful-therapy-for-verb-and-noun-naming-in-aphasi/); [PMC4476962](https://pmc.ncbi.nlm.nih.gov/articles/PMC4476962)
- Cueing hierarchies can increase support (least-to-most cues, "errorful") or decrease it (most-to-least, towards errorless). — [Zagreb repository review](https://repozitorij.erf.unizg.hr/islandora/object/erf:280/datastream/PDF/view)
- SCA's core concepts are "acknowledging competence" and "revealing competence". The Aphasia Institute's training advises speaking naturally in an adult tone and acknowledging frustration. Kagan et al. 2001 (JSLHR, 20 trained vs. 20 control volunteers): trained partners scored significantly higher on ratings of acknowledging competence, and their partners with aphasia improved on social and message-exchange ratings without being trained themselves. — [JSLHR Kagan 2001](https://pubs.asha.org/doi/10.1044/1092-4388(2001/051)); [Health PEI SCA handout](https://src.healthpei.ca/sites/src.healthpei.ca/files/stroke/Supported_Conversation_with_Adults_with_Aphasia.pdf)

### Inferences
Proposed tone rubric, 1–4 per dimension, rated by SLPs and optionally pre-screened by a calibrated LLM judge:
- (a) Adult and respectful: no childish praise or diminutives, and no over-enthusiasm such as multiple exclamation marks or "Good job, sweetie!". This is drawn from SCA "acknowledging competence".
- (b) Specific, not generic.
- (c) Encouraging without false accuracy: it must not praise an incorrect answer.
- (d) Errorless-consistent hint: the hint moves towards the target, never introduces a competing wrong word, and follows a defined cue order (semantic, then phonemic first sound, then whole word).
- (e) Brief and linguistically simple (ties to Section 3).

Automatable parts: lexicons for infantilising and diminutive phrases, an exclamation-mark count, and a check for praise words co-occurring with an "incorrect" result. Also check that a hint never leaks the full answer at a cue level where it should not.

Given that Fillingham found feedback had no effect on naming learning, RehabMind should not claim efficacy from feedback quality. It should frame tone as an acceptability and engagement property.

### Gaps
- I found no published validated rating scale specifically for the tone of therapy feedback text. The Kagan 2001 measures (acknowledging competence ratings) apply to conversation partners and would need adapting. I could not access the full instrument.
- There is no aphasia-specific study of LLM feedback tone.

## 5. Healthcare AI reporting and evaluation frameworks: what a prototype should document

### Takeaway
For a non-clinical prototype, the most relevant frameworks are TRIPOD-LLM (reporting LLM evaluation studies) and CHART (evaluation of chatbot health outputs), with DECIDE-AI as the next step if it is ever piloted with users. CONSORT-AI and SPIRIT-AI apply only to RCTs. On regulation, intended purpose decides medical-device status (MDCG 2019-11 rev.1, June 2025), so RehabMind should explicitly document a non-medical, research-only intended purpose.

### Cited Findings
- TRIPOD-LLM (Gallifant, Bitterman et al., *Nature Medicine* 31(1):60–69, Jan 2025) extends TRIPOD+AI to LLM studies. It has 19 main items and 50 subitems in a modular structure, with 14 items and 32 subitems applying to all designs. It was developed through an expedited Delphi, emphasises transparency, human oversight and task-specific performance, comes with an interactive checklist website, and is a "living" guideline. — [PubMed 39779929](https://pubmed.ncbi.nlm.nih.gov/39779929/); [PMC11361247](https://pmc.ncbi.nlm.nih.gov/articles/PMC11361247)
- CHART (2025) is a reporting guideline for studies evaluating generative-AI chatbot health advice, with 12 items and 39 subitems. It was published simultaneously in BMC Medicine, JAMA Network Open (doi 10.1001/jamanetworkopen.2025.30220) and Br J Surg, with an explanation-and-elaboration paper in BMJ 2025;390:e083305. — [EQUATOR CHART](https://www.equator-network.org/reporting-guidelines/reporting-guideline-for-chatbot-health-advice-studies-the-chart-statement/)
- DECIDE-AI (Vasey et al., BMJ 2022;377:e070904 and Nat Med 28:924–933) covers early-stage clinical evaluation of AI decision support: small-scale real-world performance, safety and human factors. It has 17 AI-specific items (28 subitems) and 10 generic items. — [EQUATOR DECIDE-AI](https://www.equator-network.org/reporting-guidelines/reporting-guideline-for-the-early-stage-clinical-evaluation-of-decision-support-systems-driven-by-artificial-intelligence-decide-ai/); [Oxford Nat Med PDF](https://eng.ox.ac.uk/media/11453/2022_natmed_bv.pdf)
- WHO guidance on large multi-modal models (18 Jan 2024) has over 40 recommendations for governments, developers and providers. It says LMMs should perform well-defined tasks with necessary accuracy and reliability, and potential users and stakeholders should be engaged from early development. It builds on WHO's 2021 AI-for-health guidance. — [WHO news release](https://www.who.int/news/item/18-01-2024-who-releases-ai-ethics-and-governance-guidance-for-large-multi-modal-models)
- EU: MDCG 2019-11 Rev.1 (June 2025) on qualifying and classifying medical device software. Intended purpose (diagnosis, prevention, monitoring, treatment, etc.) is the central test. Commentators say Rule 11 pushes many AI applications to class IIa/IIb or higher. MDCG 2025-6 addresses the MDR/IVDR interaction with the AI Act: AI that is, or is a safety component of, an MDR device needing notified-body assessment is a high-risk AI system. — [Emergo by UL on MDCG 2019-11 rev.1](https://www.emergobyul.com/news/european-revision-primary-software-guidance-mdcg-2019-11-revision-1-small-changes-meaningful); [mdrregulator.com](https://mdrregulator.com/news/revised-mdcg-2019-11-guidance-updated-approach-to-qualification-and-classification-of-medical-software); [QbD Group](https://qbdgroup.com/en/regulatory-updates/4-key-guidance-documents-released-under-the-eu-mdr-and-ivdr-frameworks) (secondary/industry sources; verify against EUR-Lex and the MDCG texts)

### Inferences
What RehabMind should document. This is a TRIPOD-LLM/CHART-style "evaluation card".
- Model name, version and quantisation (Qwen2.5-3B via Ollama, model digest), decoding parameters (temperature, seed), the full text of the three versioned prompts, and their change log.
- Task definitions and the catalogue, and the validator rules with their clinical rationale and source (Section 3 checks and the SLP-agreed thresholds).
- Fallback rate, retry counts and failure taxonomy taken from the audit log, plus rater characteristics, blinding, sample selection and agreement statistics.
- Limitations: no patient testing, an English-only scope (if so), and a small expert panel.
- An intended-purpose statement, e.g. "research prototype to explore generation of practice material under clinician supervision; not intended for diagnosis or treatment decisions; not a medical device". The clinician progress summaries are the component most at risk of looking like clinical decision support under MDCG 2019-11, so flag them as draft text requiring clinician review.
- DECIDE-AI becomes relevant only if a supervised pilot with people with aphasia is run. Use it to plan human-factors outcomes (usability, acceptability, SLP workload).
- MI-CLAIM (Norgeot et al. 2020, Nat Med, minimum information for clinical AI modelling) is less applicable because RehabMind trains no model. Cite it only to justify that choice. This is not verified in this session.

### Gaps
- I did not retrieve the DECIDE-AI or CHART item lists, or the WHO LMM recommendation list, verbatim.
- I did not verify the AI Act/MDCG 2025-6 details from primary EU text. FDA (2022 CDS guidance) and MHRA (software and AI as a medical device change programme) positions were not researched in this session.

## 6. Automated quantitative checks (lexical frequency, readability, hallucination, seed consistency)

### Takeaway
RehabMind can generate large-N automated metrics cheaply, which complement a small SLP panel. Report them as a "technical validation" table: validator pass rates, hallucination rate against the catalogue, lexical and readability distributions by difficulty level, and consistency across seeds and prompt versions.

### Cited Findings
- Hallucinated or invalid words were the main failure in LLM therapy-stimulus generation (Turkish speech-sound stimuli, accuracy M = 1.60/3). — [Birol et al. 2025, PMC12122639](https://pmc.ncbi.nlm.nih.gov/articles/PMC12122639/)
- LLM judges are most reliable on objective criteria such as factuality and internal consistency, supporting automated checks for those dimensions rather than for tone. — [PMC12837895](https://www.ncbi.nlm.nih.gov/pmc/articles/PMC12837895/)
- SUBTLEX-UK Zipf values (1–3 low, 4–7 high frequency) are publicly available for automated lexical scoring. — [SUBTLEX-UK](https://shiny.psychology.nottingham.ac.uk/lpzwjv/SUBTLEX-UK/)
- TRIPOD-LLM emphasises task-specific performance reporting and transparency about prompts and models. — [PubMed 39779929](https://pubmed.ncbi.nlm.nih.gov/39779929/)

### Inferences
Concrete student-feasible protocol, building on the existing audit log:
1. Generate N = 500–1000 outputs per output type across a grid: 3 prompt versions x 5 or more seeds x difficulty levels x exercise types, at fixed temperature, plus a temperature sweep.
2. Hallucination rate: the percentage of outputs naming a target or distractor word not in the catalogue, or mentioning an image or object absent from the item. Report it before validation (raw LLM) and after validation, retry and fallback (shipped). The "raw vs. shipped" contrast is the key evidence that the safety layer works.
3. Validator metrics: first-pass schema-valid %, clinical-rule pass %, safety pass %, mean retries, and fallback %, broken down by prompt version. Also report validator precision on a hand-labelled sample of about 100: does it reject what an SLP would reject?
4. Linguistic metrics: words per sentence, the percentage of content words with Zipf >= 4, Flesch Reading Ease (secondary), clause count, and the presence of negation or passive voice. Check the monotonic trend across difficulty levels with a Spearman correlation.
5. Consistency across seeds: answer-key agreement (does the correct answer stay correct?), semantic similarity of hints (embedding cosine), and the rate of contradictory feedback for the same input.
6. Clinician-summary faithfulness: every number or claim in a summary must trace to logged session data. Use a rule-based extraction of numbers and dates compared against the DB. Report unsupported-claim rate.
7. Then combine with Section 1 (an SLP CVI on a stratified subsample of 40–60) and an optional LLM-judge screen calibrated on that subsample.

### Gaps
- I found no published benchmark values for hallucination or fallback rates in comparable small local models generating therapy content, so there is no external baseline. RehabMind would need to use its own deterministic fallback, or clinician-authored items, as the comparator.
- Consistency-across-seeds methods (e.g., self-consistency) were not specifically researched in clinical-text literature this session.
