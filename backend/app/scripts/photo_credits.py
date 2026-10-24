"""Regenerate docs/photo-credits.md from the stimulus catalogue (attribution for CC BY /
CC BY-SA photos). Usage:  uv run python -m app.scripts.photo_credits"""

from pathlib import Path

from app.exercises.catalog import load_catalog

TARGET = Path(__file__).resolve().parents[3] / "docs" / "photo-credits.md"


def main() -> None:
    photos = sorted(load_catalog()["photos"], key=lambda p: p["image_path"])
    boss = [p for p in photos if p.get("norms")]
    commons = [p for p in photos if not p.get("norms")]
    lines = [
        "# Photo credits",
        "",
        "Every picture in RehabMind is a real photograph. Each was resized to at most 640 px",
        "and re-encoded (metadata removed); no other changes were made. Generated from",
        "`backend/app/exercises/stimuli_catalog.json` by",
        "`uv run python -m app.scripts.photo_credits`.",
        "The same credits are shown in the app at `/credits`.",
        "",
        "## Objects: Bank of Standardized Stimuli (BOSS)",
        "",
        f"{len(boss)} photos from the BOSS, a research set of normed object photos made for",
        "picture-naming studies: Brodeur, Dionne-Dostie, Montreuil & Lepage (2010), *PLOS ONE*",
        "5(5): e10773; Brodeur, Guérard & Bouras (2014), *PLOS ONE* 9(9): e106953. Copyright",
        "Mathieu B. Brodeur; licence [CC BY-SA 3.0](https://creativecommons.org/licenses/by-sa/3.0).",
        "Downloaded from the authors' public folder. Name agreement is the share of BOSS",
        "participants who gave the photo its most common name.",
        "",
        "| File | Word | BOSS file | Most common name | Name agreement | Source |",
        "|---|---|---|---|---|---|",
    ]
    for p in boss:
        n = p["norms"]
        lines.append(
            f"| `{p['image_path'].rsplit('/', 1)[-1]}` | {p['target']} | {n['boss_file']} "
            f"| {n['modal_name']} | {n['name_agreement']:.0%} | [BOSS]({p['source_url']}) |"
        )
    lines += [
        "",
        "## Scenes: Wikimedia Commons",
        "",
        "| File | Author | Licence | Source |",
        "|---|---|---|---|",
    ]
    for p in commons:
        author = (p["attribution"] or "See source").replace("|", "/").replace("\n", " ")
        lines.append(
            f"| `{p['image_path'].rsplit('/', 1)[-1]}` | {author} | {p['license']} "
            f"| [Commons]({p['source_url']}) |"
        )
    TARGET.write_text("\n".join(lines) + "\n", encoding="utf-8")
    print(f"wrote {TARGET.name}: {len(boss)} BOSS + {len(commons)} Commons photos")


if __name__ == "__main__":
    main()
