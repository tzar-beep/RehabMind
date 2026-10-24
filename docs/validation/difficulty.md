# Difficulty levels

Full numbers: [results/difficulty.md](results/difficulty.md).

Each catalogue picture has a hand-assigned difficulty from 1 to 5. Picture-naming difficulty
in aphasia is best predicted by age of acquisition, imageability, word length and name
agreement, more than by raw frequency (Nickels & Howard 1995). The audit checks the hand
levels against an independent estimate from word norms.

## Method

`app/exercises/norms.py` combines two predictors available offline:

- **frequency**: wordfreq Zipf score (lower = rarer = harder);
- **length**: syllable count (more = harder), plus a small penalty for two-word names.

Each is standardised; the weighted sum ranks the 54 distinct target words, and the ranking
is cut into five equal levels. Agreement with the catalogue is Spearman's ρ.

## Results

The picture library is now real photographs only: 52 object photos from the Bank of
Standardized Stimuli (BOSS), each with published name agreement.

| Catalogue level compared with | Items | Spearman ρ |
|---|---|---|
| Word frequency and length (norm level) | 52 | 0.84 |
| BOSS name agreement (reversed) | 52 | -0.08 |

The hand-assigned levels follow word frequency and length closely, but they ignore name
agreement: pictures that people name inconsistently are spread across all levels. The
lowest-agreement photos are the television (24% call it "TV", the most common name),
airplane (38%), egg (40%), bicycle (43%, most say "bike") and sofa (50%, most say
"couch"). Low name agreement makes naming harder and scoring less certain, so these are the
first items for the clinician panel to review: raise their level, or replace the photo with
another BOSS exemplar that has higher agreement. Four items also differ from the norm level by
two or more (banana, tomato, sofa, umbrella). Nothing in the catalogue was changed
automatically.

## Next steps

- Add Kuperman age-of-acquisition and Glasgow imageability norms (both freely available;
  check the licences before redistributing the data) and re-run the audit.
- Ask the Phase 1 panel to review the low-name-agreement and flagged items above.
- No Hindi picture-naming norms were found; a Hindi version would need local norming first.
