import type { Metadata } from "next";
import Link from "next/link";
import { z } from "zod";

import { BrandMark } from "@/components/BrandMark";
import { SkipLink } from "@/components/ui/SkipLink";
import { backendGet, getCurrentUser } from "@/lib/api/server";
import { ROLE_HOME } from "@/lib/api/schemas";

export const metadata: Metadata = { title: "Photo credits" };

const CreditSchema = z.object({
  image: z.string(),
  word: z.string(),
  source: z.string(),
  attribution: z.string(),
  license: z.string(),
  license_url: z.string().nullable(),
  source_url: z.string(),
  name_agreement: z.number().nullable(),
});

/** Public: the photo licences require credit where the photos are used. */
export default async function CreditsPage() {
  const [credits, me] = await Promise.all([
    backendGet("/stimuli/credits", z.array(CreditSchema)),
    getCurrentUser(),
  ]);
  const list = credits ?? [];
  const boss = list.filter((c) => c.name_agreement !== null);
  const scenes = list.filter((c) => c.name_agreement === null);

  return (
    <>
      <SkipLink />
      <header className="strap">
        <div className="mx-auto flex max-w-5xl items-center justify-between gap-4 px-6 py-3">
          <p className="flex items-center gap-3">
            <BrandMark />
          </p>
          <Link
            href={me ? ROLE_HOME[me.role] : "/login"}
            className="font-bold text-ink underline-offset-4 hover:underline"
          >
            {me ? "Back to the app" : "Sign in"}
          </Link>
        </div>
      </header>
      <main
        id="main"
        tabIndex={-1}
        className="mx-auto w-full max-w-5xl flex-1 px-6 py-10"
      >
        <h1 className="text-2xl font-bold tracking-tight">Photo credits</h1>
        <p className="mt-2 max-w-prose text-ink-muted">
          Every picture in RehabMind is a real photograph. Objects come from a
          research dataset made for picture-naming studies; scenes come from
          Wikimedia Commons.
        </p>

        <section aria-labelledby="boss" className="mt-10 flex flex-col gap-3">
          <h2 id="boss" className="text-xl font-bold">
            Objects: Bank of Standardized Stimuli (BOSS)
          </h2>
          <p className="max-w-prose text-ink-muted">
            {boss.length} photos by Mathieu B. Brodeur and colleagues, licensed{" "}
            <a
              href="https://creativecommons.org/licenses/by-sa/3.0"
              className="text-accent underline underline-offset-4"
            >
              CC BY-SA 3.0
            </a>
            . Brodeur et al. (2010, 2014), <i>PLOS ONE</i>. Resized for the app;
            otherwise unchanged. Name agreement is the share of people in the
            BOSS study who gave the photo its most common name.
          </p>
          <ul className="grid grid-cols-1 gap-px overflow-hidden rounded-card border border-line bg-line min-[480px]:grid-cols-2 md:grid-cols-3 lg:grid-cols-4">
            {boss.map((c) => (
              <li
                key={c.image}
                className="flex items-center gap-3 bg-surface p-3"
              >
                {/* eslint-disable-next-line @next/next/no-img-element */}
                <img
                  src={c.image}
                  alt=""
                  width={56}
                  height={56}
                  loading="lazy"
                  className="size-14 shrink-0 object-contain"
                />
                <span className="flex min-w-0 flex-col">
                  <a
                    href={c.source_url}
                    className="font-bold text-accent underline-offset-4 hover:underline"
                  >
                    {c.word}
                  </a>
                  <span className="text-sm text-ink-muted tabular-nums">
                    Name agreement {Math.round((c.name_agreement ?? 0) * 100)}%
                  </span>
                </span>
              </li>
            ))}
          </ul>
        </section>

        <section aria-labelledby="scenes" className="mt-10 flex flex-col gap-3">
          <h2 id="scenes" className="text-xl font-bold">
            Scenes: Wikimedia Commons
          </h2>
          <ul className="divide-y divide-line overflow-hidden rounded-card border border-line bg-surface shadow-card">
            {scenes.map((c) => (
              <li key={c.image} className="flex items-center gap-4 px-4 py-3">
                {/* eslint-disable-next-line @next/next/no-img-element */}
                <img
                  src={c.image}
                  alt=""
                  width={64}
                  height={48}
                  loading="lazy"
                  className="h-12 w-16 shrink-0 rounded object-cover"
                />
                <span className="flex min-w-0 flex-col">
                  <span className="font-bold">{c.word}</span>
                  <span className="text-sm text-ink-muted">
                    {c.attribution} ·{" "}
                    {c.license_url ? (
                      <a
                        href={c.license_url}
                        className="underline underline-offset-4"
                      >
                        {c.license}
                      </a>
                    ) : (
                      c.license
                    )}{" "}
                    ·{" "}
                    <a
                      href={c.source_url}
                      className="underline underline-offset-4"
                    >
                      source
                    </a>
                  </span>
                </span>
              </li>
            ))}
          </ul>
        </section>
      </main>
    </>
  );
}
