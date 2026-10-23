import { cn } from "@/lib/utils";

export type WallPicture = { src: string; word: string };

/**
 * Pictures from the practice library, each labelled with the word a patient names it by
 * (all openly licensed; credits in docs/photo-credits.md). Shared by the sign-in page and
 * the patient home so both show the same thing: what practice actually looks like.
 *
 * `fill`: the cells stretch to the wall's height (the parent sets the rows and height);
 * otherwise every cell is square.
 */
export const PRACTICE_PICTURES: WallPicture[] = [
  { src: "/stimuli/photos/apple_01.jpg", word: "apple" },
  { src: "/stimuli/photos/dog_01.jpg", word: "dog" },
  { src: "/stimuli/photos/kettle_01.jpg", word: "kettle" },
  { src: "/stimuli/photos/bicycle_01.jpg", word: "bicycle" },
  { src: "/stimuli/photos/flower_01.jpg", word: "flower" },
  { src: "/stimuli/photos/guitar_01.jpg", word: "guitar" },
];

export function PictureWall({
  pictures = PRACTICE_PICTURES,
  fill = false,
  label,
  className,
}: {
  pictures?: WallPicture[];
  fill?: boolean;
  /** Accessible name; omit to hide the wall from assistive technology (decorative). */
  label?: string;
  className?: string;
}) {
  return (
    <ul
      aria-label={label}
      aria-hidden={label ? undefined : true}
      className={cn(
        "grid grid-cols-3 gap-2 overflow-hidden rounded-card",
        className,
      )}
    >
      {pictures.map((p) => (
        <li
          key={p.src}
          className={cn(
            "relative bg-white/5",
            fill ? "min-h-0" : "aspect-square",
          )}
        >
          {/* eslint-disable-next-line @next/next/no-img-element */}
          <img
            src={p.src}
            alt={label ? p.word : ""}
            className="absolute inset-0 size-full object-cover"
          />
          <span
            aria-hidden="true"
            className="absolute bottom-2 left-2 rounded-md bg-white px-2 py-0.5 text-base font-bold text-ink"
          >
            {p.word}
          </span>
        </li>
      ))}
    </ul>
  );
}
