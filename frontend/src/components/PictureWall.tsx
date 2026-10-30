import { cn } from "@/lib/utils";

export type WallPicture = { src: string; word: string };

/**
 * Pictures from the practice library, each labelled with the word a patient names it by.
 * Object photos come from the Bank of Standardized Stimuli (BOSS, CC BY-SA 3.0); credits
 * are on the /credits page. Shared by the sign-in page and
 * the patient home so both show the same thing: what practice actually looks like.
 *
 * `fill`: the cells stretch to the wall's height (the parent sets the rows and height);
 * otherwise every cell is square.
 */
export const PRACTICE_PICTURES: WallPicture[] = [
  { src: "/stimuli/photos/boss_apple07.jpg", word: "apple" },
  { src: "/stimuli/photos/boss_saintbernard.jpg", word: "dog" },
  { src: "/stimuli/photos/boss_kettle01.jpg", word: "kettle" },
  { src: "/stimuli/photos/boss_bicycle.jpg", word: "bicycle" },
  { src: "/stimuli/photos/boss_hibiscusflower02.jpg", word: "flower" },
  { src: "/stimuli/photos/boss_acousticguitar02.jpg", word: "guitar" },
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
        "grid grid-cols-3 gap-px overflow-hidden rounded-control border border-line bg-line",
        className,
      )}
    >
      {pictures.map((p) => (
        <li
          key={p.src}
          className={cn(
            "relative bg-white",
            fill ? "min-h-0" : "aspect-square",
          )}
        >
          {/* eslint-disable-next-line @next/next/no-img-element */}
          <img
            src={p.src}
            alt={label ? p.word : ""}
            // BOSS photos are objects on white: show the whole object, never crop it.
            className="absolute inset-0 size-full object-contain p-3"
          />
          <span
            aria-hidden="true"
            className="absolute bottom-2 left-2 rounded-md bg-brand-deep px-2 py-0.5 text-base font-bold text-white"
          >
            {p.word}
          </span>
        </li>
      ))}
    </ul>
  );
}
