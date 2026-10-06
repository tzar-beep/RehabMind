import { Image as ImageIcon, Lightbulb, MessageSquareText } from "lucide-react";
import type { Metadata } from "next";
import Link from "next/link";

import { buttonClasses } from "@/components/ui/Button";
import { PracticeStatusSchema } from "@/lib/api/schemas";
import { backendGet, requireRole } from "@/lib/api/server";

export const metadata: Metadata = { title: "Home" };

const STEPS = [
  {
    icon: ImageIcon,
    title: "Look at the picture",
    text: "Take as long as you need.",
  },
  {
    icon: MessageSquareText,
    title: "Give your answer",
    text: "Type it, tap the words or say it.",
  },
  {
    icon: Lightbulb,
    title: "Ask for a hint",
    text: "Hints are there whenever you want one.",
  },
];

export default async function PatientHome() {
  const me = await requireRole("patient");
  const status = await backendGet("/practice/status", PracticeStatusSchema);

  return (
    <div className="flex flex-col gap-10">
      <h1 className="text-4xl font-bold">Hello, {me.display_name}</h1>

      <section
        aria-labelledby="today-heading"
        className="rounded-card border border-line bg-surface p-8 shadow-card"
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
            <Link
              href="/patient/practice"
              className={buttonClasses("primary", "lg")}
            >
              {status.has_active_session
                ? "Continue practice"
                : "Start practice"}
            </Link>
          </>
        ) : (
          <p className="text-xl text-ink-muted">
            Your care team is preparing your practice plan. It will appear here.
          </p>
        )}
      </section>

      <section aria-labelledby="how-heading">
        <h2 id="how-heading" className="mb-4 text-xl font-bold">
          How practice works
        </h2>
        <ol className="grid gap-4 sm:grid-cols-3">
          {STEPS.map(({ icon: Icon, title, text }, i) => (
            <li
              key={title}
              className="flex gap-4 rounded-card border border-line bg-surface p-5 sm:flex-col sm:gap-3"
            >
              <span
                aria-hidden="true"
                className="grid size-11 shrink-0 place-items-center rounded-full bg-accent-soft text-accent"
              >
                <Icon size={22} />
              </span>
              <span className="flex flex-col gap-1">
                <span className="text-lg font-bold">
                  <span className="text-ink-muted">{i + 1}. </span>
                  {title}
                </span>
                <span className="text-ink-muted">{text}</span>
              </span>
            </li>
          ))}
        </ol>
      </section>
    </div>
  );
}
