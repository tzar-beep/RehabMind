import {
  ArrowLeft,
  Download,
  ShieldCheck,
  Stethoscope,
  Users,
} from "lucide-react";
import type { Metadata } from "next";
import Link from "next/link";

import { WhoCanSeeSchema } from "@/lib/api/schemas";
import { backendGet } from "@/lib/api/server";

import { StopSharing } from "./StopSharing";

export const metadata: Metadata = { title: "My information" };

export default async function MyInformation() {
  const who = await backendGet("/practice/my-information", WhoCanSeeSchema);
  return (
    <div className="flex min-h-0 flex-1 flex-col gap-4">
      <div className="flex shrink-0 items-center justify-between gap-4">
        <h1 className="text-2xl font-bold sm:text-3xl">My information</h1>
        <Link
          href="/patient"
          className="inline-flex min-h-target items-center gap-2 font-bold text-ink-muted hover:text-ink"
        >
          <ArrowLeft aria-hidden="true" size={20} />
          Home
        </Link>
      </div>

      <div className="grid min-h-0 flex-1 gap-4 overflow-y-auto lg:grid-cols-2">
        <section
          aria-labelledby="who-heading"
          className="flex flex-col gap-4 rounded-card border border-line bg-surface shadow-card p-5"
        >
          <h2 id="who-heading" className="text-xl font-bold">
            Who can see your practice
          </h2>
          <div className="flex flex-col gap-2">
            <p className="flex items-center gap-2 font-bold">
              <Stethoscope
                aria-hidden="true"
                size={18}
                className="text-accent"
              />
              Your care team
            </p>
            <p className="text-ink-muted">
              {who?.care_team.length
                ? `${who.care_team.join(", ")}: your answers and progress, to plan your practice.`
                : "No one yet."}
            </p>
          </div>
          <div className="flex flex-col gap-2">
            <p className="flex items-center gap-2 font-bold">
              <Users aria-hidden="true" size={18} className="text-accent" />
              Your family
            </p>
            <p className="text-ink-muted">
              How often you practise and your goals. Never your answers.
            </p>
            {who?.family.length ? (
              <ul className="flex flex-col gap-2">
                {who.family.map((f) => (
                  <li
                    key={f.user_id}
                    className="flex flex-wrap items-center justify-between gap-3 rounded-control border border-line px-4 py-2"
                  >
                    <span>
                      <strong>{f.name}</strong>{" "}
                      <span className="text-ink-muted">({f.relationship})</span>
                    </span>
                    <StopSharing userId={f.user_id} name={f.name} />
                  </li>
                ))}
              </ul>
            ) : (
              <p className="text-ink-muted">No family members are linked.</p>
            )}
          </div>
        </section>

        <section
          aria-labelledby="kept-heading"
          className="flex flex-col gap-4 rounded-card border border-line bg-surface shadow-card p-5"
        >
          <h2 id="kept-heading" className="text-xl font-bold">
            What is kept
          </h2>
          <ul className="flex flex-col gap-2 text-lg">
            <li className="flex gap-2">
              <ShieldCheck
                aria-hidden="true"
                size={22}
                className="mt-0.5 shrink-0 text-success"
              />
              Your answers, as text, and how practice went.
            </li>
            <li className="flex gap-2">
              <ShieldCheck
                aria-hidden="true"
                size={22}
                className="mt-0.5 shrink-0 text-success"
              />
              Your voice recordings are deleted straight after they are turned
              into words.
            </li>
            <li className="flex gap-2">
              <ShieldCheck
                aria-hidden="true"
                size={22}
                className="mt-0.5 shrink-0 text-success"
              />
              Photos of your own words are locked: only you, your family and
              your care team can see them.
            </li>
          </ul>
          <a
            href="/api/v1/practice/my-information/export"
            download
            className="inline-flex min-h-target w-fit items-center gap-2 rounded-control border-2 border-accent px-4 font-bold text-accent hover:bg-accent-soft"
          >
            <Download aria-hidden="true" size={20} />
            Download my information
          </a>
        </section>
      </div>
    </div>
  );
}
