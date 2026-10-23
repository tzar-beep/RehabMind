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

| Comparison | Spearman ρ |
|---|---|
| All 84 naming items | 0.80 |
| Line drawings | 0.91 |
| Photos | 0.68 |

Six items differ by two or more levels and are listed for clinician review, for example the
banana photos (catalogue level 1, norm level 4: a three-syllable word, but a very
recognisable photo) and the tomato photo (2 vs 5). Photos agree less than drawings because a
clear photo makes a word easier than its norms suggest: visual recognisability is not in the
estimate. Nothing in the catalogue was changed automatically.

## Next steps

- Add Kuperman age-of-acquisition and Glasgow imageability norms (both freely available;
  check the licences before redistributing the data) and re-run the audit.
- Ask the Phase 1 panel to rate name agreement for the 6 flagged items.
- No Hindi picture-naming norms were found; a Hindi version would need local norming first.
