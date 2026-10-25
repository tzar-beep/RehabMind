import { ArrowLeft } from "lucide-react";
import type { Metadata } from "next";
import Link from "next/link";
import { z } from "zod";

import { PersonalWordSchema } from "@/lib/api/schemas";
import { backendGet } from "@/lib/api/server";

import { TalkBoard } from "./TalkBoard";

export const metadata: Metadata = { title: "Talk" };

export default async function TalkPage() {
  const ownWords =
    (await backendGet("/practice/my-words", z.array(PersonalWordSchema))) ?? [];
  return (
    <div className="flex min-h-0 flex-1 flex-col gap-3">
      <div className="flex shrink-0 items-center justify-between gap-4">
        <h1 className="text-2xl font-bold sm:text-3xl">Talk</h1>
        <Link
          href="/patient"
          className="inline-flex min-h-target items-center gap-2 font-bold text-ink-muted hover:text-ink"
        >
          <ArrowLeft aria-hidden="true" size={20} />
          Home
        </Link>
      </div>
      <TalkBoard ownWords={ownWords} />
    </div>
  );
}
