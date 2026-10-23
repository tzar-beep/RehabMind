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
      <header className="sticky top-0 z-40 border-b border-line bg-surface">
        <div
          className={`mx-auto flex ${width} items-center justify-between gap-4 px-6 py-3`}
        >
          <p className="flex items-center gap-3">
            <BrandMark />
            {roleLabel && (
              <span className="hidden border-l border-line pl-3 text-base text-ink-muted sm:inline">
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
