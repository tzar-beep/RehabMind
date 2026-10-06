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
  children,
}: {
  name: string;
  roleLabel?: string;
  wide?: boolean;
  children: ReactNode;
}) {
  const width = wide ? "max-w-6xl" : "max-w-3xl";
  return (
    <>
      <SkipLink />
      <header className="sticky top-0 z-40 border-b border-line/80 bg-surface/90 shadow-[0_1px_12px_-6px_rgb(28_36_48/0.15)] backdrop-blur-md">
        <div
          className={`mx-auto flex ${width} items-center justify-between gap-4 px-6 py-3`}
        >
          <p className="flex items-center gap-3">
            <BrandMark />
            {roleLabel && (
              <span className="hidden rounded-full border border-accent/25 bg-accent-soft px-3 py-0.5 text-sm font-bold text-accent-hover sm:inline">
                {roleLabel}
              </span>
            )}
          </p>
          <div className="flex items-center gap-3">
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
        tabIndex={-1}
        className={`mx-auto w-full ${width} flex-1 px-6 py-10`}
      >
        {children}
      </main>
    </>
  );
}
