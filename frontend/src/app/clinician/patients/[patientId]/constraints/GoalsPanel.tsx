"use client";

import { Target } from "lucide-react";
import { useRouter } from "next/navigation";
import { useState, type FormEvent } from "react";

import { StatusBadge } from "@/components/clinician/StatusBadge";
import { Alert } from "@/components/ui/Alert";
import { Button } from "@/components/ui/Button";
import { ApiError, apiFetch } from "@/lib/api/client";
import { GoalSchema, type Goal } from "@/lib/api/schemas";
import { formatDate } from "@/lib/format";

const MAX_ACTIVE = 3;
// Picture categories, as the patient reads them in a goal.
const CATEGORIES: Record<string, string> = {
  household: "Home",
  personal: "Everyday",
  food: "Food",
  transport: "Travel",
  animals: "Animals",
  tools: "Tools",
  music: "Music",
  nature: "Outdoors",
};

const field =
  "min-h-target rounded-control border-2 border-line-strong bg-surface px-3 text-base";

function GoalRow({ goal, onEnd }: { goal: Goal; onEnd?: () => void }) {
  const share = Math.min(goal.progress / goal.target, 1);
  return (
    <li className="flex flex-wrap items-center gap-x-6 gap-y-2 px-5 py-4">
      <div className="flex min-w-0 flex-1 flex-col gap-2">
        <div className="flex flex-wrap items-center gap-2">
          <span className="font-bold">{goal.title}</span>
          {goal.status === "achieved" && (
            <StatusBadge tone="success">Reached</StatusBadge>
          )}
          {goal.status === "ended" && (
            <StatusBadge tone="neutral">Ended</StatusBadge>
          )}
        </div>
        <div className="flex items-center gap-3">
          <span
            aria-hidden="true"
            className="h-2 w-40 overflow-hidden rounded-full bg-line"
          >
            <span
              className="block h-full rounded-full bg-chart"
              style={{ width: `${share * 100}%` }}
            />
          </span>
          <span className="text-sm text-ink-muted tabular-nums">
            {goal.progress} of {goal.target}
            {goal.due_on && ` · by ${formatDate(goal.due_on)}`}
          </span>
        </div>
      </div>
      {onEnd && (
        <Button variant="quiet" onClick={onEnd}>
          End goal
        </Button>
      )}
    </li>
  );
}

/**
 * Goals the patient works towards, measured from their practice (never typed in). The
 * patient sees the same plain wording on their home page.
 */
export function GoalsPanel({
  patientId,
  goals,
}: {
  patientId: string;
  goals: Goal[];
}) {
  const router = useRouter();
  const [kind, setKind] = useState<"name_words" | "practice_days">(
    "name_words",
  );
  const [busy, setBusy] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const current = goals.filter((g) => g.status !== "ended");
  const ended = goals.filter((g) => g.status === "ended");
  const activeCount = goals.filter((g) => g.status === "active").length;
  const url = `/patients/${patientId}/goals`;

  async function add(event: FormEvent<HTMLFormElement>) {
    event.preventDefault();
    const formEl = event.currentTarget;
    const form = new FormData(formEl);
    setBusy(true);
    setError(null);
    try {
      await apiFetch(
        url,
        {
          method: "POST",
          json: {
            kind,
            target: Number(form.get("target")),
            category: form.get("category") || null,
            due_on: form.get("due_on") || null,
          },
        },
        GoalSchema,
      );
      formEl.reset();
      router.refresh();
    } catch (e) {
      setError(e instanceof ApiError ? e.message : "That didn't save.");
    } finally {
      setBusy(false);
    }
  }

  async function end(goal: Goal) {
    await apiFetch(`${url}/${goal.id}/end`, { method: "POST" }, GoalSchema);
    router.refresh();
  }

  return (
    <div className="flex flex-col gap-4">
      {current.length > 0 ? (
        <ul className="divide-y divide-line overflow-hidden rounded-card border border-line bg-surface">
          {current.map((g) => (
            <GoalRow
              key={g.id}
              goal={g}
              onEnd={g.status === "active" ? () => end(g) : undefined}
            />
          ))}
        </ul>
      ) : (
        <p className="flex items-center gap-2 text-ink-muted">
          <Target aria-hidden="true" size={18} />
          No goals yet. A goal gives the patient something to work towards.
        </p>
      )}

      {activeCount < MAX_ACTIVE ? (
        <form
          onSubmit={add}
          className="flex flex-col gap-3 rounded-card border border-line bg-surface p-5"
        >
          <p className="font-bold">Add a goal</p>
          <div className="flex flex-wrap items-end gap-3">
            <label className="flex flex-col gap-1 text-sm font-bold">
              Goal
              <select
                className={field}
                value={kind}
                onChange={(e) => setKind(e.target.value as typeof kind)}
              >
                <option value="name_words">Name words on their own</option>
                <option value="practice_days">
                  Practise on days this week
                </option>
              </select>
            </label>
            <label className="flex flex-col gap-1 text-sm font-bold">
              {kind === "name_words" ? "How many words" : "How many days"}
              <input
                key={kind}
                name="target"
                type="number"
                required
                min={1}
                max={kind === "name_words" ? 200 : 7}
                defaultValue={kind === "name_words" ? 10 : 4}
                className={`${field} w-24`}
              />
            </label>
            {kind === "name_words" && (
              <label className="flex flex-col gap-1 text-sm font-bold">
                Pictures
                <select name="category" className={field} defaultValue="">
                  <option value="">Any</option>
                  {Object.entries(CATEGORIES).map(([value, label]) => (
                    <option key={value} value={value}>
                      {label}
                    </option>
                  ))}
                </select>
              </label>
            )}
            <label className="flex flex-col gap-1 text-sm font-bold">
              Aim for (optional)
              <input name="due_on" type="date" className={field} />
            </label>
            <Button type="submit" busy={busy}>
              Add goal
            </Button>
          </div>
          {error && <Alert tone="error">{error}</Alert>}
        </form>
      ) : (
        <p className="text-ink-muted">
          {MAX_ACTIVE} goals at a time keeps practice focused. End one to add
          another.
        </p>
      )}

      {ended.length > 0 && (
        <details>
          <summary className="min-h-target cursor-pointer py-2 font-bold text-accent">
            Ended goals ({ended.length})
          </summary>
          <ul className="divide-y divide-line overflow-hidden rounded-card border border-line bg-surface">
            {ended.map((g) => (
              <GoalRow key={g.id} goal={g} />
            ))}
          </ul>
        </details>
      )}
    </div>
  );
}
