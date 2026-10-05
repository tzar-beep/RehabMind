import type { ReactNode } from "react";

import { SignOutButton } from "@/components/SignOutButton";
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
      <header className="border-b border-line bg-surface">
        <div className={`mx-auto flex ${width} items-center justify-between gap-4 px-6 py-3`}>
          <p className="text-lg font-bold">
            <span aria-hidden="true" className="mr-2 text-accent">
              ●
            </span>
            Stroke Recovery AI
            {roleLabel && (
              <span className="ml-3 text-base font-normal text-ink-muted">{roleLabel}</span>
            )}
          </p>
          <div className="flex items-center gap-3">
            <span className="hidden text-ink-muted sm:inline">{name}</span>
            <SignOutButton />
          </div>
        </div>
      </header>
      <main id="main" tabIndex={-1} className={`mx-auto w-full ${width} flex-1 px-6 py-10`}>
        {children}
      </main>
    </>
  );
}
