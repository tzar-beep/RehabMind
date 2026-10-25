import { ArrowLeft } from "lucide-react";
import type { Metadata } from "next";
import Link from "next/link";
import { z } from "zod";

import { ScriptSchema } from "@/lib/api/schemas";
import { backendGet } from "@/lib/api/server";

import { Phrases } from "./Phrases";

export const metadata: Metadata = { title: "Everyday phrases" };

export default async function PhrasesPage() {
  const scripts =
    (await backendGet("/practice/phrases", z.array(ScriptSchema))) ?? [];
  return (
    <div className="flex min-h-0 flex-1 flex-col gap-3">
      <div className="flex shrink-0 items-center justify-between gap-4">
        <div>
          <h1 className="text-2xl font-bold sm:text-3xl">Everyday phrases</h1>
          <p className="text-ink-muted">
            Short conversations to practise, one line at a time.
          </p>
        </div>
        <Link
          href="/patient"
          className="inline-flex min-h-target items-center gap-2 font-bold text-ink-muted hover:text-ink"
        >
          <ArrowLeft aria-hidden="true" size={20} />
          Home
        </Link>
      </div>
      <Phrases scripts={scripts} />
    </div>
  );
}
