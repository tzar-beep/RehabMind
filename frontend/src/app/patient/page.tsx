import type { Metadata } from "next";

import Link from "next/link";

import { buttonClasses } from "@/components/ui/Button";
import { PracticeStatusSchema } from "@/lib/api/schemas";
import { backendGet, requireRole } from "@/lib/api/server";

export const metadata: Metadata = { title: "Home" };

const JOURNEY = ["Words", "Sentences", "Conversation"];

export default async function PatientHome() {
  const me = await requireRole("patient");
  const status = await backendGet("/practice/status", PracticeStatusSchema);

  return (
    <div className="flex flex-col gap-10">
      <h1 className="text-4xl font-bold">Hello, {me.display_name}</h1>

      <section
        aria-labelledby="today-heading"
        className="rounded-card border border-line bg-surface p-8"
      >
        <h2 id="today-heading" className="mb-3 text-2xl font-bold">
          Today&rsquo;s practice
        </h2>
        {status?.has_plan ? (
          <>
            <p className="mb-6 text-xl text-ink-muted">
              {status.has_active_session
                ? "Pick up where you left off."
                : "A few pictures to name. Go at your own pace."}
            </p>
            <Link href="/patient/practice" className={buttonClasses("primary", "lg")}>
              {status.has_active_session ? "Continue practice" : "Start practice"}
            </Link>
          </>
        ) : (
          <p className="text-xl text-ink-muted">
            Your care team is preparing your practice plan. It will appear here.
          </p>
        )}
      </section>

      <section aria-labelledby="journey-heading">
        <h2 id="journey-heading" className="mb-4 text-xl font-bold">
          Your journey
        </h2>
        <ol className="flex flex-wrap items-center gap-3 text-lg">
          {JOURNEY.map((step, i) => (
            <li key={step} className="flex items-center gap-3">
              <span className="rounded-full border-2 border-line-strong bg-surface px-5 py-2">
                {step}
              </span>
              {i < JOURNEY.length - 1 && (
                <span aria-hidden="true" className="text-ink-muted">
                  →
                </span>
              )}
            </li>
          ))}
        </ol>
      </section>
    </div>
  );
}
