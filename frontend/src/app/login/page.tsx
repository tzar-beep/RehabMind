import type { Metadata } from "next";
import { redirect } from "next/navigation";

import { BrandMark } from "@/components/BrandMark";
import { Alert } from "@/components/ui/Alert";
import { ROLE_HOME } from "@/lib/api/schemas";
import { getCurrentUser } from "@/lib/api/server";

import { LoginForm } from "./LoginForm";

export const metadata: Metadata = { title: "Sign in" };

// Pictures from the practice library, each with the word a patient names it by
// (all openly licensed; credits in docs/photo-credits.md).
const LIBRARY = [
  { src: "/stimuli/photos/apple_01.jpg", word: "apple" },
  { src: "/stimuli/photos/dog_01.jpg", word: "dog" },
  { src: "/stimuli/photos/kettle_01.jpg", word: "kettle" },
  { src: "/stimuli/photos/bicycle_01.jpg", word: "bicycle" },
  { src: "/stimuli/photos/flower_01.jpg", word: "flower" },
  { src: "/stimuli/photos/guitar_01.jpg", word: "guitar" },
];

const FACTS = [
  { value: "61", label: "real-world photos" },
  { value: "3", label: "exercise types" },
  { value: "0", label: "recordings kept" },
];

export default async function LoginPage({ searchParams }: PageProps<"/login">) {
  const expired = (await searchParams).expired === "1";
  const me = await getCurrentUser();
  if (me) redirect(ROLE_HOME[me.role]);

  return (
    <main
      id="main"
      className="grid h-dvh grid-cols-1 overflow-hidden lg:grid-cols-[minmax(0,1.2fr)_minmax(0,1fr)]"
    >
      {/* Brand panel: the practice library itself, as a picture wall that fills
          whatever height the window has, so the page never scrolls. */}
      <div className="hidden min-h-0 flex-col gap-[clamp(1rem,3.5vh,2rem)] bg-brand-deep p-[clamp(1.5rem,4.5vh,3rem)] text-white lg:flex">
        <BrandMark inverted large />

        <div className="flex max-w-2xl flex-col gap-3">
          <p className="text-[clamp(2rem,6.2vh,3.25rem)] leading-[1.04] font-bold tracking-tight text-balance">
            Practise words, one picture at a time.
          </p>
          <p className="text-[clamp(1rem,2.4vh,1.15rem)] text-brand-muted">
            Short, calm naming exercises for aphasia recovery, within limits
            your care team sets.
          </p>
        </div>

        <ul
          aria-label="Some pictures from the practice library"
          className="grid min-h-0 flex-1 grid-cols-3 grid-rows-2 gap-2 overflow-hidden rounded-card"
        >
          {LIBRARY.map((p) => (
            <li key={p.src} className="relative min-h-0 bg-white/5">
              {/* eslint-disable-next-line @next/next/no-img-element */}
              <img
                src={p.src}
                alt={p.word}
                className="absolute inset-0 size-full object-cover"
              />
              <span
                aria-hidden="true"
                className="absolute bottom-2.5 left-2.5 rounded-md bg-white px-2.5 py-0.5 text-base font-bold text-ink"
              >
                {p.word}
              </span>
            </li>
          ))}
        </ul>

        <p className="text-sm text-brand-muted">
          {FACTS.map((f) => `${f.value} ${f.label}`).join(" · ")} · Research
          prototype
        </p>
      </div>

      <div className="flex min-h-0 items-center justify-center overflow-y-auto bg-surface px-6 py-8 sm:px-12">
        <div className="w-full max-w-sm">
          <div className="mb-10 lg:hidden">
            <BrandMark />
            <p className="mt-3 text-lg text-ink-muted">
              Practise words, one picture at a time.
            </p>
          </div>
          <h1 className="text-3xl font-bold tracking-tight">Sign in</h1>
          <p className="mt-2 mb-8 text-lg text-ink-muted">
            Welcome back. Take your time.
          </p>
          {expired && (
            <div className="mb-6">
              <Alert tone="info">
                You were signed out after a break, to keep your account safe.
                Please sign in again; your practice is saved.
              </Alert>
            </div>
          )}
          <LoginForm />
          <p className="mt-8 text-base text-ink-muted">
            Trouble signing in? Ask your care team for help.
          </p>
        </div>
      </div>
    </main>
  );
}
