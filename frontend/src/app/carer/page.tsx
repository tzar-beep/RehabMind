import { HeartHandshake, Target } from "lucide-react";
import type { Metadata } from "next";
import { z } from "zod";

import { OwnWords } from "@/components/OwnWords";
import { WeekActivity } from "@/components/patient/WeekActivity";
import {
  CarerSummarySchema,
  MessageListSchema,
  PersonalWordSchema,
  SupportedPatientSchema,
  type Goal,
} from "@/lib/api/schemas";
import { backendGet } from "@/lib/api/server";

import { SendNote } from "./SendNote";

export const metadata: Metadata = { title: "Family" };

function Goals({ goals, name }: { goals: Goal[]; name: string }) {
  if (goals.length === 0)
    return (
      <p className="text-ink-muted">
        {name}&rsquo;s care team hasn&rsquo;t set goals yet.
      </p>
    );
  return (
    <ul className="flex flex-col gap-4">
      {goals.map((g) => (
        <li key={g.id} className="flex flex-col gap-1.5">
          <span className="font-bold">{g.title}</span>
          <span className="flex items-center gap-3">
            <span
              aria-hidden="true"
              className="h-2.5 w-48 overflow-hidden rounded-full bg-line"
            >
              <span
                className="block h-full rounded-full bg-chart"
                style={{
                  width: `${Math.min(g.progress / g.target, 1) * 100}%`,
                }}
              />
            </span>
            <span className="text-sm text-ink-muted tabular-nums">
              {g.status === "achieved"
                ? "Reached!"
                : `${g.progress} of ${g.target}`}
            </span>
          </span>
        </li>
      ))}
    </ul>
  );
}

/**
 * Family and carers help practice at home: they see how often (never how well) the
 * patient practises, the goals their care team set, and add the patient's own words.
 */
export default async function CarerHome() {
  const patients = await backendGet(
    "/carer/patients",
    z.array(SupportedPatientSchema),
  );
  const patient = patients?.[0];
  if (!patient)
    return (
      <div className="flex flex-col gap-3">
        <h1 className="text-3xl font-bold">Welcome</h1>
        <p className="text-lg text-ink-muted">
          Your account isn&rsquo;t linked to anyone yet. Please ask the care
          team to link it.
        </p>
      </div>
    );
  const [summary, words, sent] = await Promise.all([
    backendGet(`/carer/patients/${patient.id}`, CarerSummarySchema),
    backendGet(
      `/carer/patients/${patient.id}/words`,
      z.array(PersonalWordSchema),
    ),
    backendGet(`/carer/patients/${patient.id}/messages`, MessageListSchema),
  ]);
  const name = patient.display_name;

  return (
    <div className="flex flex-col gap-8">
      <div className="flex flex-col gap-1">
        <p className="flex items-center gap-2 text-ink-muted">
          <HeartHandshake aria-hidden="true" size={18} />
          You support {name} ({patient.relationship})
        </p>
        <h1 className="text-3xl font-bold">How {name} is getting on</h1>
        <p className="max-w-prose text-ink-muted">
          Practice that happens most days helps most. Here you can see how often{" "}
          {name} practises, what they are working towards, and add words from
          their own life.
        </p>
      </div>

      <div className="grid gap-6 lg:grid-cols-[minmax(0,1.6fr)_minmax(0,1fr)]">
        {summary && <WeekActivity activity={summary.activity} />}
        <section
          aria-labelledby="goals-heading"
          className="flex flex-col gap-4 rounded-card border border-line bg-surface shadow-card p-5"
        >
          <h2
            id="goals-heading"
            className="flex items-center gap-2 text-xl font-bold"
          >
            <Target aria-hidden="true" size={20} />
            {name}&rsquo;s goals
          </h2>
          <Goals goals={summary?.goals ?? []} name={name} />
          <div className="mt-2 border-t border-line pt-4">
            <SendNote patientId={patient.id} name={name} sent={sent ?? []} />
          </div>
        </section>
      </div>

      <section aria-labelledby="words-heading" className="flex flex-col gap-3">
        <div>
          <h2 id="words-heading" className="text-2xl font-bold">
            {name}&rsquo;s own words
          </h2>
          <p className="max-w-prose text-ink-muted">
            Photos of the people, pets and things in {name}&rsquo;s life. They
            appear in practice alongside the usual pictures: words that matter
            to someone are often the ones that come back first.
          </p>
        </div>
        <OwnWords
          apiBase={`/carer/patients/${patient.id}/words`}
          patientName={name}
          words={words ?? []}
        />
      </section>
    </div>
  );
}
