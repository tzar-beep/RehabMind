import type { Metadata } from "next";
import { Images, ShieldCheck, SlidersHorizontal, Speech } from "lucide-react";
import { redirect } from "next/navigation";

import { BrandMark } from "@/components/BrandMark";
import { BorderBeam } from "@/components/magicui/border-beam";
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
            fadeBottom={0.9}
          />
          <div className="absolute inset-0 bg-linear-to-r from-brand-deep via-brand-deep/60 to-transparent" />
        </div>

        <BrandMark inverted className="animate-rise" />

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

        <p className="mt-12 hidden text-sm text-brand-muted lg:block">
          University research prototype. Not a medical device.
        </p>
      </div>

      <div className="relative isolate flex items-center justify-center px-6 py-10 sm:py-14">
        <div
          aria-hidden="true"
          className="absolute inset-0 -z-10 bg-[radial-gradient(var(--color-line-strong)_1px,transparent_1px)] opacity-40 mask-[radial-gradient(ellipse_at_center,#000_45%,transparent_90%)] bg-size-[22px_22px]"
        />
        <div className="animate-rise relative w-full max-w-md overflow-hidden rounded-card border border-line bg-surface p-8 shadow-xl shadow-ink/5 [animation-delay:120ms] sm:p-10">
          <BorderBeam
            size={140}
            duration={9}
            borderWidth={2}
            colorFrom="#0f6e6e"
            colorTo="#5ec4b6"
          />
          <h1 className="mb-2 text-3xl font-bold">Sign in</h1>
          <p className="mb-8 text-ink-muted">Welcome back. Take your time.</p>
          <LoginForm />
          <p className="mt-8 border-t border-line pt-6 text-center text-base text-ink-muted">
            Trouble signing in? Ask your care team for help.
          </p>
        </div>
      </div>
    </main>
  );
}
