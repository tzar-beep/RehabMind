import { Compass } from "lucide-react";
import type { Metadata } from "next";
import Link from "next/link";

import { BrandMark } from "@/components/BrandMark";
import { buttonClasses } from "@/components/ui/Button";

export const metadata: Metadata = { title: "Page not found" };

/** Any unknown address. "/" sends signed-in people to their own home, others to sign-in. */
export default function NotFound() {
  return (
    <main
      id="main"
      className="flex flex-1 flex-col items-center justify-center gap-6 px-6 py-16 text-center"
    >
      <BrandMark />
      <span
        aria-hidden="true"
        className="grid size-16 place-items-center rounded-full bg-accent-soft text-accent"
      >
        <Compass size={32} />
      </span>
      <h1 className="text-3xl font-bold">This page does not exist</h1>
      <p className="max-w-md text-lg text-ink-muted">
        The link may be old or mistyped. Nothing has been lost.
      </p>
      <Link href="/" className={buttonClasses("primary", "lg")}>
        Go to my home page
      </Link>
    </main>
  );
}
