"""Phase 2 part B dry run: does the speech recogniser repair naming errors?

    uv run python -m app.scripts.speech_fidelity [--write]      # Windows: synthesises audio
    uv run python -m app.scripts.speech_fidelity --audio <dir>  # any OS: your own recordings

The protocol (protocols/phase2-older-adults.md, part B) has each participant read 40 scripted
naming responses: 10 correct names, 10 related words ("cat" for dog), 10 sound errors that
are real words ("log") and 10 that are not words ("dag"). This script builds that list from
the picture catalogue, and, without participants, speaks it with the computer's synthetic
voices (Windows SAPI: two voices, normal and slow rate, standing in for four speakers). Each
recording goes through the app's own recogniser (faster-whisper, the production settings)
and the app's scorer, exactly as a spoken answer would.

  faithful  the transcript says what was scripted
  repaired  the transcript is the target word although an error was scripted (false accept)
  other     anything else

SYNTHETIC SPEECH. Synthetic voices are clearer and more regular than older or aphasic
speakers, so this is a lower bound on the problem, not an estimate of it. With the
`--audio` option, recordings named <item_id>.wav (or .webm) from real readers replace them.
"""

import argparse
import csv
import json
import random
import subprocess
import sys
import tempfile
from collections import Counter, defaultdict
from pathlib import Path

from wordfreq import zipf_frequency

from app.analysis.errors import LEXICON_PATH
from app.analysis.scoring import normalize, score_naming
from app.core.config import get_settings
from app.speech.provider import FasterWhisperProvider

ROOT = Path(__file__).parents[3] / "docs" / "validation"
CATALOG = Path(__file__).parents[1] / "exercises" / "stimuli_catalog.json"
REPORT = ROOT / "results" / "speech-fidelity-simulated.md"
KINDS = ["correct", "semantic", "formal", "nonword"]
PER_KIND = 10
VOICES = [  # (voice, rate): SAPI rate -10..10, 0 = default, negative = slower
    ("Microsoft David Desktop", 0),
    ("Microsoft David Desktop", -3),
    ("Microsoft Zira Desktop", 0),
    ("Microsoft Zira Desktop", -3),
]
VOWELS, CONSONANTS = "aeiou", "bcdfghklmnprstvw"


def neighbours(word: str) -> list[str]:
    """Strings one sound away from `word`: the first consonant or a vowel changed, the
    commonest phonological errors in aphasia ("dag" for dog), and still pronounceable."""
    out = []
    for i, ch in enumerate(word):
        if ch in VOWELS:
            pool = VOWELS
        elif i == 0:
            pool = CONSONANTS
        else:
            continue
        out += [word[:i] + c + word[i + 1 :] for c in pool if c != ch]
    return out


def script(seed: int = 3) -> list[dict]:
    """The 40 scripted responses, 10 of each kind, on different pictures."""
    rng = random.Random(seed)  # noqa: S311 - item selection, not security
    lex = json.loads(LEXICON_PATH.read_text(encoding="utf-8"))
    fields = lex["fields"]
    photos = [
        p
        for p in json.loads(CATALOG.read_text(encoding="utf-8"))["photos"]
        if "picture_naming" in p["exercise_types"] and " " not in p["target"]
    ]
    rng.shuffle(photos)
    rows: list[dict] = []
    counts: Counter = Counter()
    for p in photos:
        target, accepted = p["target"], {a.lower() for a in p["accepted_answers"]} | {p["target"]}
        related = {w for ws in fields.values() if target in ws for w in ws}
        options = {
            "correct": [target],
            "semantic": sorted(related - accepted),
            "formal": [
                w
                for w in neighbours(target)
                if zipf_frequency(w, "en") >= 3.5 and w not in related and w not in accepted
            ],
            "nonword": [w for w in neighbours(target) if zipf_frequency(w, "en") < 1.0],
        }
        # Fill the kind that is furthest behind and possible for this picture.
        for kind in sorted(KINDS, key=lambda k: counts[k]):
            if counts[kind] < PER_KIND and options[kind]:
                counts[kind] += 1
                rows.append(
                    {
                        "kind": kind,
                        "target": target,
                        "scripted": rng.choice(options[kind]),
                        "accepted": sorted(accepted),
                    }
                )
                break
        if all(counts[k] == PER_KIND for k in KINDS):
            break
    for i, r in enumerate(rows, 1):
        r["item_id"] = f"B{i:02d}"
    return rows


def synthesise(rows: list[dict], out: Path) -> None:
    """Speak every scripted response with every voice (Windows SAPI, one PowerShell call)."""
    jobs = [
        {
            "path": str(out / f"{r['item_id']}-v{v}.wav"),
            "text": r["scripted"],
            "voice": name,
            "rate": rate,
        }
        for r in rows
        for v, (name, rate) in enumerate(VOICES)
    ]
    spec = out / "jobs.json"
    spec.write_text(json.dumps(jobs), encoding="utf-8")
    ps = (
        "Add-Type -AssemblyName System.Speech;"
        "$s = New-Object System.Speech.Synthesis.SpeechSynthesizer;"
        f"foreach ($j in (Get-Content -Raw '{spec}' | ConvertFrom-Json)) {{"
        "$s.SelectVoice($j.voice); $s.Rate = $j.rate;"
        "$s.SetOutputToWaveFile($j.path); $s.Speak($j.text) }; $s.SetOutputToNull()"
    )
    subprocess.run(["powershell", "-NoProfile", "-Command", ps], check=True)  # noqa: S603,S607


def classify(row: dict, heard: str) -> str:
    said = normalize(heard)
    if (
        row["kind"] != "correct"
        and score_naming(heard, row["target"], row["accepted"]).outcome == "correct"
    ):
        return "repaired"
    return "faithful" if said == normalize(row["scripted"]) else "other"


def run(audio_dir: Path | None) -> tuple[list[dict], list[dict]]:
    rows = script()
    s = get_settings()
    stt = FasterWhisperProvider(s.whisper_model, s.whisper_device, s.whisper_compute_type)
    results = []
    with tempfile.TemporaryDirectory() as tmp:
        if audio_dir is None:
            audio_dir = Path(tmp)
            synthesise(rows, audio_dir)
        for r in rows:
            for f in sorted(audio_dir.glob(f"{r['item_id']}*")):
                if f.suffix not in (".wav", ".webm", ".ogg", ".mp4"):
                    continue
                t = stt.transcribe(f.read_bytes(), "en")
                outcome = classify(r, t.text)
                matched = score_naming(t.text, r["target"], r["accepted"]).matched or ""
                unsure = {normalize(w) for w in t.low_confidence_words}
                results.append(
                    {
                        **{k: v for k, v in r.items() if k != "accepted"},
                        "speaker": f.stem.split("-")[-1] if "-" in f.stem else "reader",
                        "heard": t.text,
                        "outcome": outcome,
                        "flagged": outcome == "repaired" and bool(unsure & set(matched.split())),
                    }
                )
                print(
                    f"{r['item_id']} {r['kind']:8} {r['scripted']!r:14} -> {t.text!r} [{outcome}]",
                    flush=True,
                )
    return rows, results


def report(rows: list[dict], results: list[dict], synthetic: bool) -> str:
    by_kind: dict[str, Counter] = defaultdict(Counter)
    flagged: Counter = Counter()
    for r in results:
        by_kind[r["kind"]][r["outcome"]] += 1
        flagged[r["kind"]] += r["flagged"]
    speakers = len({r["speaker"] for r in results})
    lines = [
        "<!-- SYNTHETIC: synthetic voices, not participants. See ../simulated.md -->"
        if synthetic
        else "",
        "# Speech recogniser fidelity (Phase 2 part B)",
        "",
        f"Generated by `app.scripts.speech_fidelity`. {len(rows)} scripted responses × "
        f"{speakers} {'synthetic voices' if synthetic else 'speakers'} = {len(results)} "
        "recordings, transcribed with the production recogniser settings "
        f"(faster-whisper `{get_settings().whisper_model}`, no prompt).",
        "",
        "| Scripted response | Recordings | Faithful | Repaired (false accept) | Other | "
        "Repaired and flagged uncertain |",
        "|---|---|---|---|---|---|",
    ]
    for kind in KINDS:
        c = by_kind[kind]
        n = sum(c.values())
        if not n:
            continue
        rep = "—" if kind == "correct" else f"{c['repaired']} ({c['repaired'] / n:.0%})"
        flag = "—" if kind == "correct" else f"{flagged[kind]}/{c['repaired']}"
        lines.append(
            f"| {kind} | {n} | {c['faithful']} ({c['faithful'] / n:.0%}) | {rep} | "
            f"{c['other']} | {flag} |"
        )
    sound = by_kind["formal"] + by_kind["nonword"]
    n_sound = sum(sound.values())
    if n_sound:
        rate = sound["repaired"] / n_sound
        verdict = (
            "above the protocol's 5% limit: spoken answers should not count towards progression "
            "until fixed"
            if rate > 0.05
            else "within the protocol's 5% limit"
        )
        lines += ["", f"Sound errors repaired into the target: {rate:.1%}, {verdict}."]
    others = [r for r in results if r["outcome"] == "other"]
    if others:
        lines += ["", "Examples of other transcripts:", ""]
        lines += [
            f"- {r['kind']}: scripted “{r['scripted']}” (target {r['target']}), "
            f"heard “{r['heard']}”"
            for r in others[:8]
        ]
    return "\n".join(lines).lstrip("\n") + "\n"


def main() -> None:
    sys.stdout.reconfigure(encoding="utf-8")
    ap = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    ap.add_argument("--audio", type=Path, help="folder of real recordings <item_id>*.wav")
    ap.add_argument("--write", action="store_true")
    args = ap.parse_args()
    rows, results = run(args.audio)
    text = report(rows, results, synthetic=args.audio is None)
    print(text)
    if args.write:
        REPORT.write_text(text, encoding="utf-8")
        out = ROOT / "simulated" / "speech-fidelity.csv"
        out.parent.mkdir(parents=True, exist_ok=True)
        with out.open("w", newline="", encoding="utf-8") as f:
            w = csv.DictWriter(f, fieldnames=list(results[0]))
            w.writeheader()
            w.writerows(results)


if __name__ == "__main__":
    main()
