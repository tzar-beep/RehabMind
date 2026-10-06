import type { Metadata } from "next";
import {
  Check,
  Images,
  Lightbulb,
  ShieldCheck,
  SlidersHorizontal,
  Speech,
} from "lucide-react";
import { redirect } from "next/navigation";

import { BrandMark } from "@/components/BrandMark";
import { GlyphMatrix } from "@/components/magicui/glyph-matrix";
import { ROLE_HOME } from "@/lib/api/schemas";
import { getCurrentUser } from "@/lib/api/server";

import { LoginForm } from "./LoginForm";

export const metadata: Metadata = { title: "Sign in" };

const FEATURES = [
  { icon: Images, text: "Picture exercises with real-world photos" },
  { icon: Speech, text: "Answer by typing or by speaking" },
  { icon: SlidersHorizontal, text: "Your clinician sets the pace and limits" },
  { icon: ShieldCheck, text: "Voice recordings are deleted after use" },
];

const FACTS = [
  { value: "61", label: "real-world photos" },
  { value: "3", label: "exercise types" },
  { value: "0", label: "recordings kept" },
];

/** Decorative previews of real exercises, peeking out from behind the sign-in card. */
function ExercisePreviews() {
  return (
    <div aria-hidden="true" className="hidden xl:block">
      <div className="animate-rise absolute -top-20 -right-10 z-10 w-44 rotate-6 rounded-2xl border border-line bg-surface p-3 shadow-xl shadow-ink/10 [animation-delay:300ms]">
        {/* eslint-disable-next-line @next/next/no-img-element */}
        <img
          src="/stimuli/photos/apple_01.jpg"
          alt=""
          width={200}
          height={130}
          className="h-20 w-full rounded-xl object-cover"
        />
        <p className="mt-2 text-center text-base font-bold">What is this?</p>
        <p className="mt-2 flex items-center gap-2 rounded-lg bg-accent-soft px-2 py-1.5 text-sm">
          <Lightbulb size={16} className="shrink-0 text-warning" />
          It starts with “a…”
        </p>
      </div>
      <div className="animate-rise absolute -bottom-24 -left-10 z-10 w-auto -rotate-3 rounded-2xl border border-line bg-surface px-4 py-3 shadow-xl shadow-ink/10 [animation-delay:420ms]">
        <p className="text-sm font-bold text-ink-muted">Build a sentence</p>
        <div className="mt-1.5 flex gap-1.5">
          {["The", "bird", "is", "flying"].map((w) => (
            <span
              key={w}
              className="rounded-lg bg-accent px-2.5 py-1 text-sm font-bold text-white"
            >
              {w}
            </span>
          ))}
        </div>
        <p className="mt-2 flex items-center gap-2 text-sm font-bold text-success">
          <span className="grid size-6 place-items-center rounded-full bg-success-soft">
            <Check size={14} strokeWidth={3} />
          </span>
          Nice work.
        </p>
      </div>
    </div>
  );
}

export default async function LoginPage() {
  const me = await getCurrentUser();
  if (me) redirect(ROLE_HOME[me.role]);

  return (
    <main
      id="main"
      className="grid flex-1 grid-cols-1 lg:grid-cols-[minmax(0,1.1fr)_minmax(0,1fr)]"
    >
      <div className="relative isolate flex flex-col overflow-hidden bg-brand-deep px-6 py-8 text-white sm:px-10 lg:min-h-full lg:p-14">
        <div className="absolute inset-0 -z-10">
          <GlyphMatrix
            glyphs="abcdefghijklmnopqrstuvwxyz"
            color="#5ec4b6"
            cellSize={20}
            mutationRate={0.015}
            interval={160}
            settleAfter={4000}
            fadeBottom={0.9}
          />
          <div className="absolute inset-0 bg-linear-to-r from-brand-deep via-brand-deep/60 to-transparent" />
        </div>

        <BrandMark inverted large className="animate-rise" />

        <div className="mt-8 max-w-lg lg:mt-auto">
          <p className="animate-rise text-3xl leading-tight font-bold text-balance [animation-delay:80ms] sm:text-4xl lg:text-5xl">
            Practise words, one picture at a time.
          </p>
          <p className="animate-rise mt-4 hidden text-lg text-brand-muted [animation-delay:160ms] sm:block">
            Short, calm language exercises for aphasia recovery, shaped around
            you by your care team.
          </p>
          <ul className="mt-10 hidden gap-4 lg:grid">
            {FEATURES.map(({ icon: Icon, text }, i) => (
              <li
                key={text}
                className="animate-rise flex items-center gap-4"
                style={{ animationDelay: `${240 + i * 80}ms` }}
              >
                <span
                  aria-hidden="true"
                  className="grid size-11 shrink-0 place-items-center rounded-xl bg-white/10 ring-1 ring-white/20"
                >
                  <Icon className="size-5" />
                </span>
                <span className="text-lg">{text}</span>
              </li>
            ))}
          </ul>
        </div>

        <div className="mt-12 hidden lg:block">
          <dl className="grid max-w-lg grid-cols-3 gap-px overflow-hidden rounded-2xl bg-white/15 ring-1 ring-white/15">
            {FACTS.map((f) => (
              <div key={f.label} className="bg-brand-deep/80 px-4 py-3">
                <dt className="sr-only">{f.label}</dt>
                <dd className="text-2xl font-bold">{f.value}</dd>
                <dd aria-hidden="true" className="text-sm text-brand-muted">
                  {f.label}
                </dd>
              </div>
            ))}
          </dl>
          <p className="mt-4 text-sm text-brand-muted">
            University research prototype. Not a medical device.
          </p>
        </div>
      </div>

      <div className="relative isolate flex items-center justify-center overflow-x-clip px-6 py-10 sm:py-14">
        <div
          aria-hidden="true"
          className="absolute inset-0 -z-10 bg-[radial-gradient(var(--color-line-strong)_1px,transparent_1px)] opacity-40 mask-[radial-gradient(ellipse_at_center,#000_45%,transparent_90%)] bg-size-[22px_22px]"
        />
        <div className="relative w-full max-w-md xl:my-16">
          <ExercisePreviews />
          <div className="animate-rise relative w-full max-w-md rounded-card border border-line bg-surface p-8 shadow-card [animation-delay:120ms] sm:p-10">
            <h1 className="mb-2 text-3xl font-bold">Sign in</h1>
            <p className="mb-8 text-ink-muted">Welcome back. Take your time.</p>
            <LoginForm />
            <p className="mt-8 border-t border-line pt-6 text-center text-base text-ink-muted">
              Trouble signing in? Ask your care team for help.
            </p>
          </div>
        </div>
      </div>
    </main>
  );
}
