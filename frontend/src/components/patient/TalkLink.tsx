import { MessagesSquare } from "lucide-react";
import Link from "next/link";

/** The way to the talk board, next to the main practice button. */
export function TalkLink() {
  return (
    <Link
      href="/patient/talk"
      className="inline-flex min-h-14 items-center justify-center gap-2 rounded-control border-2 border-white/40 px-6 text-xl font-bold text-white transition-colors hover:bg-white/10"
    >
      <MessagesSquare aria-hidden="true" size={22} />
      Talk
    </Link>
  );
}
