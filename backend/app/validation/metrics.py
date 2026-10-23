"""Agreement statistics used in the validation reports (docs/validation/).

Pure functions over paired labels, so the same code scores the app against a benchmark,
one clinician against another, or the app against a clinician.
"""

from collections import Counter
from collections.abc import Sequence


def percent_agreement(a: Sequence[str], b: Sequence[str]) -> float:
    if len(a) != len(b) or not a:
        raise ValueError("need two equal-length, non-empty label lists")
    return sum(x == y for x, y in zip(a, b, strict=True)) / len(a)


def cohen_kappa(a: Sequence[str], b: Sequence[str]) -> float:
    """Chance-corrected agreement between two raters (Cohen 1960)."""
    po = percent_agreement(a, b)
    n = len(a)
    ca, cb = Counter(a), Counter(b)
    pe = sum(ca[k] * cb[k] for k in set(ca) | set(cb)) / (n * n)
    return 1.0 if pe == 1 else (po - pe) / (1 - pe)


def gwet_ac1(a: Sequence[str], b: Sequence[str]) -> float:
    """Gwet's AC1: like kappa, but stable when one category dominates (Gwet 2008)."""
    po = percent_agreement(a, b)
    n = len(a)
    cats = set(a) | set(b)
    if len(cats) < 2:
        return 1.0
    ca, cb = Counter(a), Counter(b)
    pi = {k: (ca[k] + cb[k]) / (2 * n) for k in cats}
    pe = sum(p * (1 - p) for p in pi.values()) / (len(cats) - 1)
    return (po - pe) / (1 - pe)


def _ranks(values: Sequence[float]) -> list[float]:
    """Average ranks (ties share the mean of their positions)."""
    order = sorted(range(len(values)), key=lambda i: values[i])
    ranks = [0.0] * len(values)
    i = 0
    while i < len(order):
        j = i
        while j + 1 < len(order) and values[order[j + 1]] == values[order[i]]:
            j += 1
        for k in range(i, j + 1):
            ranks[order[k]] = (i + j) / 2 + 1
        i = j + 1
    return ranks


def spearman(a: Sequence[float], b: Sequence[float]) -> float:
    """Spearman rank correlation (Pearson correlation of average ranks)."""
    if len(a) != len(b) or len(a) < 2:
        raise ValueError("need two equal-length lists of at least two values")
    ra, rb = _ranks(a), _ranks(b)
    ma, mb = sum(ra) / len(ra), sum(rb) / len(rb)
    cov = sum((x - ma) * (y - mb) for x, y in zip(ra, rb, strict=True))
    va = sum((x - ma) ** 2 for x in ra) ** 0.5
    vb = sum((y - mb) ** 2 for y in rb) ** 0.5
    return cov / (va * vb) if va and vb else 0.0


def confusion(gold: Sequence[str], pred: Sequence[str]) -> dict[str, Counter]:
    table: dict[str, Counter] = {}
    for g, p in zip(gold, pred, strict=True):
        table.setdefault(g, Counter())[p] += 1
    return table


def per_class(gold: Sequence[str], pred: Sequence[str]) -> dict[str, dict[str, float]]:
    """Precision, recall and F1 per gold class."""
    out: dict[str, dict[str, float]] = {}
    for k in sorted(set(gold)):
        tp = sum(g == k and p == k for g, p in zip(gold, pred, strict=True))
        fp = sum(g != k and p == k for g, p in zip(gold, pred, strict=True))
        fn = sum(g == k and p != k for g, p in zip(gold, pred, strict=True))
        precision = tp / (tp + fp) if tp + fp else 0.0
        recall = tp / (tp + fn) if tp + fn else 0.0
        f1 = 2 * precision * recall / (precision + recall) if precision + recall else 0.0
        out[k] = {"precision": precision, "recall": recall, "f1": f1, "n": tp + fn}
    return out


def accept_rates(gold_correct: Sequence[bool], scored_correct: Sequence[bool]) -> dict[str, float]:
    """False-accept rate: wrong answers the app called correct (the safety-relevant error:
    it hides an error from the patient and inflates progression). False-reject rate: right
    answers the app did not accept (frustrating, but visible and recoverable)."""
    wrong = [s for g, s in zip(gold_correct, scored_correct, strict=True) if not g]
    right = [s for g, s in zip(gold_correct, scored_correct, strict=True) if g]
    return {
        "false_accept_rate": sum(wrong) / len(wrong) if wrong else 0.0,
        "false_reject_rate": sum(not s for s in right) / len(right) if right else 0.0,
        "n_wrong": len(wrong),
        "n_right": len(right),
    }


def content_validity(ratings: Sequence[Sequence[int]]) -> dict[str, object]:
    """Content Validity Index (Lynn 1986; Polit & Beck 2006).

    `ratings[i][j]` is expert j's 1-4 relevance rating of item i. An item counts as relevant
    to an expert at 3 or 4. I-CVI = share of experts rating the item relevant; S-CVI/Ave =
    mean I-CVI; S-CVI/UA = share of items every expert rated relevant.
    """
    if not ratings or not all(ratings):
        raise ValueError("need at least one item with at least one rating")
    i_cvi = [sum(r >= 3 for r in item) / len(item) for item in ratings]
    return {
        "i_cvi": i_cvi,
        "s_cvi_ave": sum(i_cvi) / len(i_cvi),
        "s_cvi_ua": sum(v == 1.0 for v in i_cvi) / len(i_cvi),
    }
