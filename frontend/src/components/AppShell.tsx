import Link from "next/link";
import type { ReactNode } from "react";

import { BrandMark } from "@/components/BrandMark";
import { SignOutButton } from "@/components/SignOutButton";
import { Avatar } from "@/components/ui/Avatar";
import { SkipLink } from "@/components/ui/SkipLink";

/** Shared page frame: one predictable header, one main region. */
export function AppShell({
  name,
  roleLabel,
  wide = false,
  fit = false,
  children,
}: {
  name: string;
  roleLabel?: string;
  /** true: the clinician and admin consoles; false: the patient's area. */
  wide?: boolean;
  /**
   * true (the patient's area): exactly one screen tall. Each page lays itself out in the
   * height that is left, so nothing needs scrolling; main only scrolls as a last resort on
   * very small screens. Credits move into the header.
   */
  fit?: boolean;
  children: ReactNode;
}) {
  const width = wide ? "max-w-6xl" : "max-w-5xl";
  const credits = (
    <Link
      href="/credits"
      className="inline-flex min-h-target items-center text-sm text-ink-muted underline underline-offset-4 hover:text-ink"
    >
      Photo credits
    </Link>
  );
  return (
    <div className={fit ? "flex h-dvh flex-col" : "contents"}>
      <SkipLink />
      <header className={`strap z-40 ${fit ? "shrink-0" : "sticky top-0"}`}>
        <div
          className={`mx-auto flex ${width} items-center justify-between gap-4 px-6 py-2`}
        >
          <p className="flex items-center gap-3">
            <span
              aria-hidden="true"
              className="strap-stud hidden size-7 shrink-0 rounded-full sm:block"
            />
            <BrandMark />
            {roleLabel && (
              <span className="hidden border-l border-accent/30 pl-3 text-base text-ink-muted sm:inline">
                {roleLabel}
              </span>
            )}
          </p>
          {/* The strap's punched holes, in whatever room the header has left. */}
          <span
            aria-hidden="true"
            className="hidden h-3.5 min-w-0 flex-1 justify-evenly overflow-hidden lg:flex"
          >
            {[0, 1, 2, 3, 4].map((i) => (
              <span
                key={i}
                className="strap-hole size-3.5 shrink-0 rounded-full"
              />
            ))}
          </span>
          <div className="flex items-center gap-3">
            {/* On a phone the header has no room: the home page shows the link instead. */}
            {fit && (
              <span className="hidden sm:contents">
                <Link
                  href="/patient/my-information"
                  className="inline-flex min-h-target items-center text-sm text-ink-muted underline underline-offset-4 hover:text-ink"
                >
                  My information
                </Link>
                {credits}
              </span>
            )}
            <span className="hidden items-center gap-2.5 sm:flex">
              <Avatar name={name} size="sm" />
              <span className="font-bold">{name}</span>
            </span>
            <SignOutButton />
          </div>
        </div>
      </header>
      <main
        id="main"
        // In the one-screen area main can scroll as a last resort: keyboard users must reach it.
        tabIndex={fit ? 0 : -1}
        className={
          fit
            ? `mx-auto flex min-h-0 w-full ${width} flex-1 flex-col overflow-y-auto px-4 py-3 sm:px-6 sm:py-4`
            : `mx-auto w-full ${width} flex-1 px-6 py-6 sm:py-10`
        }
      >
        {children}
      </main>
      {!fit && (
        <footer className={`mx-auto w-full ${width} px-6 pb-6`}>
          {credits}
        </footer>
      )}
    </div>
  );
}
