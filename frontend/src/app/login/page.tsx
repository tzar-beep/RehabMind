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
      className="grid h-dvh grid-cols-1 overflow-hidden lg:grid-cols-[minmax(0,1.15fr)_minmax(0,1fr)]"
    >
      <div className="hidden min-h-0 flex-col gap-8 overflow-hidden bg-brand-deep text-white lg:flex lg:px-14 lg:py-12">
        <BrandMark inverted large className="hidden lg:inline-flex" />

        <div className="flex max-w-xl flex-col gap-4">
          <p className="text-3xl leading-[1.05] font-bold tracking-tight text-balance sm:text-4xl lg:text-5xl">
            Practise words, one picture at a time.
          </p>
          <p className="text-lg text-brand-muted">
            Short, calm naming exercises for aphasia recovery. Answer by typing
            or speaking, within limits your care team sets.
          </p>
        </div>

        <ul
          aria-label="Some pictures from the practice library"
          // Two rows of three, as wide as the window height allows so the page never scrolls.
          className="grid w-[clamp(15rem,calc((100dvh-37rem)*1.5),36rem)] grid-cols-3 gap-3"
        >
          {LIBRARY.map((p) => (
            <li key={p.src} className="flex flex-col gap-1.5">
              {/* eslint-disable-next-line @next/next/no-img-element */}
              <img
                src={p.src}
                alt={p.word}
                width={200}
                height={200}
                className="aspect-square w-full rounded-lg object-cover"
              />
              <span aria-hidden="true" className="text-base font-bold">
                {p.word}
              </span>
            </li>
          ))}
        </ul>

        <div className="mt-auto hidden flex-col gap-4 lg:flex [@media(max-height:760px)]:hidden">
          <dl className="grid max-w-xl grid-cols-3 gap-px overflow-hidden rounded-card bg-white/15">
            {FACTS.map((f) => (
              <div key={f.label} className="bg-brand-deep px-4 py-3">
                <dt className="sr-only">{f.label}</dt>
                <dd className="text-2xl font-bold tabular-nums">{f.value}</dd>
                <dd aria-hidden="true" className="text-sm text-brand-muted">
                  {f.label}
                </dd>
              </div>
            ))}
          </dl>
          <p className="text-sm text-brand-muted">
            University research prototype. Not a medical device.
          </p>
        </div>
      </div>

      <div className="flex min-h-0 items-center justify-center overflow-y-auto bg-surface px-6 py-8 sm:px-10">
        <div className="w-full max-w-md">
          <div className="mb-8 lg:hidden">
            <BrandMark />
            <p className="mt-3 text-lg text-ink-muted">
              Practise words, one picture at a time.
            </p>
          </div>
          <h1 className="mb-2 text-2xl font-bold tracking-tight">Sign in</h1>
          <p className="mb-8 text-lg text-ink-muted">
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
          <p className="mt-10 text-base text-ink-muted">
            Trouble signing in? Ask your care team for help.
          </p>
        </div>
      </div>
    </main>
  );
}
