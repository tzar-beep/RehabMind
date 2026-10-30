import type { Metadata } from "next";
import { redirect } from "next/navigation";

import { BrandMark } from "@/components/BrandMark";
import { LabelStrip } from "@/components/LabelStrip";
import { Alert } from "@/components/ui/Alert";
import { ROLE_HOME } from "@/lib/api/schemas";
import { getCurrentUser } from "@/lib/api/server";
import { cn } from "@/lib/utils";

import { LoginForm } from "./LoginForm";
import s from "./login.module.css";

export const metadata: Metadata = { title: "Sign in" };

// The label's printed details: what every person signing in can rely on.
const PRINTED = [
  ["Where", "At home"],
  ["Care", "Led by your clinician"],
  ["Pace", "Your own, no streaks"],
] as const;

// Barcode bar widths (decorative), alternating bar and gap: a fixed pattern so the label
// prints the same each time.
const BARS = [
  2, 1, 1, 1, 3, 2, 1, 1, 1, 3, 2, 1, 1, 2, 3, 1, 1, 1, 2, 2, 1, 3, 1, 1, 2, 1, 1, 2, 3, 1,
  1, 2, 1, 1, 2, 3, 1, 1, 2, 1, 3, 1, 1, 2, 1, 1, 2, 2,
];

// Each bar's left edge: the running total of the widths before it.
const BAR_X = BARS.map((_, i) => BARS.slice(0, i).reduce((sum, w) => sum + w, 0));
const BARCODE_WIDTH = BARS.reduce((sum, w) => sum + w, 0);

function Barcode({ className }: { className?: string }) {
  // Even entries are printed bars; odd entries are the gaps between them.
  const rects = BARS.map((w, i) =>
    i % 2 === 0 ? <rect key={i} x={BAR_X[i]} width={w} height="40" /> : null,
  );
  return (
    <svg
      aria-hidden="true"
      viewBox={`0 0 ${BARCODE_WIDTH} 40`}
      preserveAspectRatio="none"
      className={className}
      fill="currentColor"
    >
      {rects}
    </svg>
  );
}

// Text column shared by the headline and the footer, so they line up.
const COLUMN = "mx-auto w-full max-w-[72rem] px-[clamp(1.25rem,4vw,3rem)]";

export default async function LoginPage({ searchParams }: PageProps<"/login">) {
  const expired = (await searchParams).expired === "1";
  const me = await getCurrentUser();
  if (me) redirect(ROLE_HOME[me.role]);

  return (
    <main id="main" className="flex min-h-dvh flex-col overflow-x-hidden bg-canvas text-ink">
      <header className="px-[clamp(1.25rem,4vw,3rem)] pt-[clamp(1.25rem,4vh,2.25rem)]">
        <BrandMark />
      </header>

      <div className="flex flex-1 flex-col justify-center gap-[clamp(1.25rem,4vh,2.25rem)] py-8">
        <div className={cn(COLUMN, "grid items-end gap-x-12 gap-y-3 lg:grid-cols-[minmax(0,1.25fr)_minmax(0,1fr)]")}>
          <p className="max-w-[20ch] text-[1.6rem] leading-[1.05] font-bold tracking-[-0.025em] text-balance sm:text-[clamp(2rem,6.4vh,3.5rem)]">
            Aphasia practice at home, guided by your care team.
          </p>
          <div className="hidden max-w-[44ch] text-[clamp(1.05rem,2.4vh,1.2rem)] text-ink-muted sm:block lg:pb-1">
            <p>
              Short speech and language exercises between therapy sessions,
              for people recovering from stroke.
            </p>
            <p className="mt-2 font-bold text-ink">
              Patients, family, clinicians and admins all sign in here.
            </p>
          </div>
        </div>

        {/* The wristband: a slim strap across the page, with the label clipped onto it. */}
        <div className="relative lg:pl-[max(1.5rem,calc((100vw-72rem)/2))]">
          <div
            aria-hidden="true"
            className={cn(
              "strap",
              s.fasten,
              "absolute inset-y-0 right-[-3rem] my-auto hidden h-24 items-center rounded-l-full pl-4 lg:left-[max(1.5rem,calc((100vw-72rem)/2))] lg:flex",
            )}
          >
            <span className={cn("strap-stud", s.press, "size-14 shrink-0 rounded-full")} />
            <div className="ml-auto flex items-center gap-[clamp(2.25rem,4vw,3.5rem)] pr-16">
              {Array.from({ length: 10 }, (_, i) => (
                <span key={i} className={"strap-hole size-6 shrink-0 rounded-full"} />
              ))}
            </div>
          </div>

          <section
            aria-labelledby="sign-in-heading"
            className="relative mx-3 overflow-hidden rounded-card border border-line bg-surface shadow-card shadow-float sm:mx-6 lg:mx-0 lg:ml-36 lg:w-[min(52rem,calc(100vw-22rem))]"
          >
            <LabelStrip aside="One sign-in for the whole care team">
              Speech and language practice
            </LabelStrip>

            <div className="grid gap-x-8 gap-y-5 p-[clamp(1.25rem,2.5vw,2rem)] lg:grid-cols-[minmax(0,1fr)_auto]">
              <div className="min-w-0">
                <div className="flex flex-wrap items-baseline justify-between gap-x-6 gap-y-1 border-b border-line pb-3">
                  <h1
                    id="sign-in-heading"
                    className="text-[clamp(1.75rem,4vh,2.25rem)] leading-none font-bold tracking-tight"
                  >
                    Sign in
                  </h1>
                  <p className="text-lg text-ink-muted">Welcome back. Take your time.</p>
                </div>

                {expired && (
                  <div className="mt-4">
                    <Alert tone="info">
                      You were signed out after a break, to keep your account
                      safe. Please sign in again; your practice is saved.
                    </Alert>
                  </div>
                )}

                <div className="mt-[clamp(1rem,3vh,1.5rem)]">
                  <LoginForm inline />
                </div>

                {/* Printed details in fixed, ruled cells. */}
                <dl className="mt-[clamp(1rem,3vh,1.5rem)] grid gap-y-1.5 border-t border-line pt-3 sm:grid-cols-3 sm:pt-0">
                  {PRINTED.map(([term, detail], i) => (
                    <div
                      key={term}
                      className={cn(
                        "flex gap-2 text-[0.95rem] sm:pt-3",
                        i > 0 && "sm:border-l sm:border-line sm:pl-4",
                      )}
                    >
                      <dt className="font-bold">{term}</dt>
                      <dd className="text-ink-muted">{detail}</dd>
                    </div>
                  ))}
                </dl>
              </div>

              {/* Barcode panel, after a tear line. */}
              <div
                aria-hidden="true"
                className="hidden w-32 flex-col justify-center gap-2 border-l border-dashed border-line-strong/50 pl-7 lg:flex"
              >
                <Barcode className="h-28 w-full text-ink" />
                <span className="text-center text-xs font-bold tracking-[0.14em] text-ink-muted">
                  REHABMIND
                </span>
              </div>
            </div>

            {/* The slots the strap passes through, top and bottom. */}
            <span aria-hidden="true" className="absolute top-3 left-1/2 hidden h-1.5 w-24 -translate-x-1/2 rounded-full bg-[#b3dbd4] lg:block" />
            <span aria-hidden="true" className="absolute bottom-3 left-1/2 hidden h-1.5 w-24 -translate-x-1/2 rounded-full bg-[#b3dbd4] lg:block" />
          </section>
        </div>

        <div className={cn(COLUMN, "flex flex-col gap-1 text-base text-ink-muted md:flex-row md:justify-between md:gap-8")}>
          <p>Trouble signing in? Ask your care team for help.</p>
          <p>Research prototype, not a diagnostic tool. Your clinician is always the authority.</p>
        </div>
      </div>
    </main>
  );
}
