"""Regenerate docs/photo-credits.md from the stimulus catalogue (attribution for CC BY /
CC BY-SA photos). Usage:  uv run python -m app.scripts.photo_credits"""

from pathlib import Path

from app.exercises.catalog import load_catalog

TARGET = Path(__file__).resolve().parents[3] / "docs" / "photo-credits.md"


def main() -> None:
    photos = load_catalog()["photos"]
    lines = [
        "# Photo credits",
        "",
        "Real-world photographs used as exercise stimuli. All come from",
        "[Wikimedia Commons](https://commons.wikimedia.org) under the licence shown; each was",
        "resized to at most 640 px and re-encoded (metadata removed). No other changes were made.",
        "Generated from `backend/app/exercises/stimuli_catalog.json` by",
        "`uv run python -m app.scripts.photo_credits`.",
        "",
        "Line drawings: [Lucide](https://lucide.dev) icons, ISC licence.",
        "",
        "| File | Author | Licence | Source |",
        "|---|---|---|---|",
    ]
    for p in sorted(photos, key=lambda p: p["image_path"]):
        author = (p["attribution"] or "See source").replace("|", "/").replace("\n", " ")
        lines.append(
            f"| `{p['image_path'].rsplit('/', 1)[-1]}` | {author} | {p['license']} "
            f"| [Commons]({p['source_url']}) |"
        )
    TARGET.write_text("\n".join(lines) + "\n", encoding="utf-8")
    print(f"wrote {TARGET.name}: {len(photos)} photos")


if __name__ == "__main__":
    main()
