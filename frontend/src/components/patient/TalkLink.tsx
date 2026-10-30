import { MessagesSquare, Quote } from "lucide-react";
import Link from "next/link";

const link =
  "inline-flex min-h-14 items-center justify-center gap-2 rounded-control border-2 border-accent bg-surface px-5 text-xl font-bold text-accent transition-colors hover:bg-accent-soft";

/** The ways to the talk board and everyday phrases, next to the main practice button. */
export function TalkLink() {
  return (
    <>
      <Link href="/patient/talk" className={link}>
        <MessagesSquare aria-hidden="true" size={22} />
        Talk
      </Link>
      <Link href="/patient/phrases" className={link}>
        <Quote aria-hidden="true" size={22} />
        Phrases
      </Link>
    </>
  );
}
