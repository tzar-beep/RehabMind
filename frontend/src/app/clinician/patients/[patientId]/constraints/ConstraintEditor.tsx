"use client";

import { useRouter } from "next/navigation";
import { useRef, useState, type ReactNode } from "react";

import { constraintRows } from "@/components/clinician/ConstraintSummary";
import { Alert } from "@/components/ui/Alert";
import { Button } from "@/components/ui/Button";
import { ApiError, apiFetch } from "@/lib/api/client";
import {
  ConstraintVersionSchema,
  type ConstraintFields,
  type ConstraintOptions,
  type ConstraintVersion,
} from "@/lib/api/clinician";
import {
  changedKeys,
  picturesAvailable,
  validateConstraints,
} from "@/lib/constraints";
import { exerciseType, responseMode } from "@/lib/format";

const DEFAULTS: ConstraintFields = {
  allowed_exercise_types: ["picture_naming"],
  allowed_response_modes: ["text"],
  allowed_categories: null,
  min_difficulty: 1,
  max_difficulty: 2,
  max_exercises_per_session: 8,
  advance_after_correct: 3,
  step_back_after_incorrect: 2,
  note: null,
};

type Step = "closed" | "editing" | "review";

function Fieldset({
  legend,
  error,
  children,
}: {
  legend: string;
  error?: string;
  children: ReactNode;
}) {
  return (
    <fieldset
      className="flex flex-col gap-2"
      aria-invalid={error ? true : undefined}
    >
      <legend className="mb-1 font-bold">{legend}</legend>
      {children}
      {error && (
        <p role="alert" className="text-sm font-bold text-danger">
          {error}
        </p>
      )}
    </fieldset>
  );
}

function Check({
  label,
  checked,
  disabled,
  onChange,
}: {
  label: ReactNode;
  checked: boolean;
  disabled?: boolean;
  onChange: (on: boolean) => void;
}) {
  return (
    <label
      className={`flex min-h-target items-center gap-3 ${disabled ? "text-ink-muted" : ""}`}
    >
      <input
        type="checkbox"
        className="size-5 accent-[var(--color-accent)]"
        checked={checked}
        disabled={disabled}
        onChange={(e) => onChange(e.target.checked)}
      />
      {label}
    </label>
  );
}

function NumberField({
  id,
  label,
  value,
  min,
  max,
  error,
  hint,
  onChange,
}: {
  id: string;
  label: string;
  value: number;
  min: number;
  max: number;
  error?: string;
  hint?: string;
  onChange: (v: number) => void;
}) {
  return (
    <div className="flex flex-col gap-1">
      <label htmlFor={id} className="font-bold">
        {label}
      </label>
      {hint && (
        <p id={`${id}-hint`} className="text-sm text-ink-muted">
          {hint}
        </p>
      )}
      <input
        id={id}
        type="number"
        inputMode="numeric"
        min={min}
        max={max}
        value={Number.isNaN(value) ? "" : value}
        onChange={(e) => onChange(e.target.valueAsNumber)}
        aria-invalid={error ? true : undefined}
        aria-describedby={
          [hint && `${id}-hint`, error && `${id}-error`]
            .filter(Boolean)
            .join(" ") || undefined
        }
        className={`min-h-target w-32 rounded-control border-2 bg-surface px-3 text-lg ${error ? "border-danger" : "border-line-strong"}`}
      />
      {error && (
        <p id={`${id}-error`} className="text-sm font-bold text-danger">
          {error}
        </p>
      )}
    </div>
  );
}

const toggle = (list: string[], value: string, on: boolean) =>
  on ? [...new Set([...list, value])] : list.filter((v) => v !== value);

/**
 * Creates a NEW immutable constraint version (never edits an existing one):
 * edit → review changes → save. The server re-validates and enforces authorization.
 */
export function ConstraintEditor({
  patientId,
  current,
  options,
}: {
  patientId: string;
  current: ConstraintVersion | null;
  options: ConstraintOptions;
}) {
  const router = useRouter();
  const start: ConstraintFields = current
    ? { ...current, note: null }
    : DEFAULTS;
  const [step, setStep] = useState<Step>("closed");
  const [v, setV] = useState<ConstraintFields>(start);
  const [showErrors, setShowErrors] = useState(false);
  const [saving, setSaving] = useState(false);
  const [serverError, setServerError] = useState<string | null>(null);
  const [saved, setSaved] = useState<number | null>(null);
  const heading = useRef<HTMLHeadingElement>(null);

  const errors = validateConstraints(v, options);
  const shown = showErrors ? errors : {};
  const changed = current ? changedKeys(current, v) : null;
  const pictures = picturesAvailable(v, options);
  const set = <K extends keyof ConstraintFields>(
    k: K,
    value: ConstraintFields[K],
  ) => setV((prev) => ({ ...prev, [k]: value }));

  function open() {
    setV(start);
    setSaved(null);
    setServerError(null);
    setShowErrors(false);
    setStep("editing");
  }

  function review() {
    setShowErrors(true);
    if (Object.keys(errors).length) return;
    setStep("review");
    requestAnimationFrame(() => heading.current?.focus());
  }

  async function save() {
    setSaving(true);
    setServerError(null);
    try {
      const created = await apiFetch(
        `/patients/${patientId}/constraints`,
        { method: "POST", json: { ...v, note: v.note?.trim() || null } },
        ConstraintVersionSchema.pick({ version: true }),
      );
      setSaved(created!.version);
      setStep("closed");
      router.refresh();
    } catch (e) {
      setServerError(
        e instanceof ApiError && e.status === 422
          ? "The server rejected these limits. Please check the values and try again."
          : e instanceof ApiError
            ? e.message
            : "The new version could not be saved. Please try again.",
      );
    } finally {
      setSaving(false);
    }
  }

  if (step === "closed") {
    return (
      <div className="flex flex-col gap-4">
        {saved !== null && (
          <Alert tone="success">
            Version {saved} created and now active. It applies from the
            patient&rsquo;s next exercise, including during a session in
            progress.
          </Alert>
        )}
        <div>
          <Button onClick={open}>
            {current
              ? `Create new version (v${current.version + 1})`
              : "Set practice limits"}
          </Button>
        </div>
      </div>
    );
  }

  const nextVersion = (current?.version ?? 0) + 1;

  if (step === "review") {
    const before = current ? constraintRows(current) : null;
    const after = constraintRows(v);
    return (
      <section
        aria-labelledby="review-heading"
        className="flex flex-col gap-4 rounded-card border-2 border-accent bg-surface p-6"
      >
        <h3
          id="review-heading"
          ref={heading}
          tabIndex={-1}
          className="text-xl font-bold"
        >
          Review version {nextVersion}
        </h3>
        <p className="text-ink-muted">
          Saving creates a new version. Version {current?.version ?? "—"} stays
          in the history unchanged.
        </p>
        <table className="w-full text-left">
          <caption className="sr-only">
            Changes in version {nextVersion}
          </caption>
          <thead className="text-sm text-ink-muted">
            <tr>
              <th scope="col" className="py-2 pr-4">
                Setting
              </th>
              {before && (
                <th scope="col" className="py-2 pr-4">
                  Current (v{current!.version})
                </th>
              )}
              <th scope="col" className="py-2">
                New (v{nextVersion})
              </th>
            </tr>
          </thead>
          <tbody className="divide-y divide-line">
            {after.map((row, i) => {
              const diff = before && before[i].value !== row.value;
              return (
                <tr
                  key={row.label}
                  className={diff ? "bg-accent-soft" : undefined}
                >
                  <th scope="row" className="py-2 pr-4 font-normal">
                    {row.label}
                    {diff && (
                      <span className="ml-2 text-sm font-bold">(changed)</span>
                    )}
                  </th>
                  {before && <td className="py-2 pr-4">{before[i].value}</td>}
                  <td className="py-2 font-bold">{row.value}</td>
                </tr>
              );
            })}
          </tbody>
        </table>
        {v.note && <p>Note: {v.note}</p>}
        {changed && changed.length === 0 && (
          <Alert tone="warning">
            No limits have changed. Go back to make a change.
          </Alert>
        )}
        {serverError && <Alert tone="error">{serverError}</Alert>}
        <div className="flex flex-wrap gap-3">
          <Button onClick={save} busy={saving} disabled={changed?.length === 0}>
            {saving ? "Saving…" : `Save as version ${nextVersion}`}
          </Button>
          <Button
            variant="secondary"
            onClick={() => setStep("editing")}
            disabled={saving}
          >
            Back to editing
          </Button>
        </div>
      </section>
    );
  }

  const sessionRange = options.max_exercises_per_session;
  const ruleRange = options.progression_rule;
  return (
    <form
      noValidate
      onSubmit={(e) => {
        e.preventDefault();
        review();
      }}
      className="flex flex-col gap-6 rounded-card border-2 border-accent bg-surface p-6"
      aria-labelledby="editor-heading"
    >
      <div>
        <h3 id="editor-heading" className="text-xl font-bold">
          New version {nextVersion}
        </h3>
        <p className="text-ink-muted">
          {current ? `Starting from version ${current.version}. ` : ""}Nothing
          is saved until you review and confirm.
        </p>
      </div>

      <div className="grid gap-6 md:grid-cols-2">
        <Fieldset legend="Exercise types" error={shown.allowed_exercise_types}>
          {options.exercise_types.map((t) => (
            <Check
              key={t.value}
              label={
                <>
                  {exerciseType(t.value)}
                  {!t.available && (
                    <span className="text-sm"> (not yet available)</span>
                  )}
                </>
              }
              checked={v.allowed_exercise_types.includes(t.value)}
              disabled={
                !t.available && !v.allowed_exercise_types.includes(t.value)
              }
              onChange={(on) =>
                set(
                  "allowed_exercise_types",
                  toggle(v.allowed_exercise_types, t.value, on),
                )
              }
            />
          ))}
        </Fieldset>

        <div className="flex flex-col gap-6">
          <Fieldset
            legend="Answer methods"
            error={shown.allowed_response_modes}
          >
            {options.response_modes.map((m) => (
              <Check
                key={m}
                label={responseMode(m)}
                checked={v.allowed_response_modes.includes(m)}
                onChange={(on) =>
                  set(
                    "allowed_response_modes",
                    toggle(v.allowed_response_modes, m, on),
                  )
                }
              />
            ))}
          </Fieldset>

          <Fieldset
            legend="Difficulty range"
            error={shown.max_difficulty ?? shown.min_difficulty}
          >
            <div className="flex flex-wrap gap-6">
              {(["min_difficulty", "max_difficulty"] as const).map((k) => (
                <div key={k} className="flex flex-col gap-1">
                  <label htmlFor={k} className="text-sm">
                    {k === "min_difficulty" ? "Minimum" : "Maximum"}
                  </label>
                  <select
                    id={k}
                    value={v[k]}
                    onChange={(e) => set(k, Number(e.target.value))}
                    className="min-h-target rounded-control border-2 border-line-strong bg-surface px-3 text-lg"
                  >
                    {Array.from(
                      {
                        length:
                          options.difficulty[1] - options.difficulty[0] + 1,
                      },
                      (_, i) => i + options.difficulty[0],
                    ).map((d) => (
                      <option key={d} value={d}>
                        {d}
                      </option>
                    ))}
                  </select>
                </div>
              ))}
            </div>
          </Fieldset>
        </div>
      </div>

      <Fieldset legend="Picture categories" error={shown.allowed_categories}>
        <Check
          label="All categories"
          checked={v.allowed_categories === null}
          onChange={(on) =>
            set(
              "allowed_categories",
              on ? null : Object.keys(options.categories),
            )
          }
        />
        {v.allowed_categories !== null && (
          <div className="grid gap-x-6 sm:grid-cols-2 lg:grid-cols-4">
            {Object.entries(options.categories).map(([cat, levels]) => {
              const inRange = Object.entries(levels)
                .filter(
                  ([d]) =>
                    Number(d) >= v.min_difficulty &&
                    Number(d) <= v.max_difficulty,
                )
                .reduce((n, [, c]) => n + c, 0);
              return (
                <Check
                  key={cat}
                  label={
                    <>
                      <span className="capitalize">{cat}</span>
                      <span className="text-sm text-ink-muted">
                        {" "}
                        ({inRange} in range)
                      </span>
                    </>
                  }
                  checked={v.allowed_categories!.includes(cat)}
                  onChange={(on) =>
                    set(
                      "allowed_categories",
                      toggle(v.allowed_categories!, cat, on),
                    )
                  }
                />
              );
            })}
          </div>
        )}
      </Fieldset>

      <div className="grid gap-6 sm:grid-cols-3">
        <NumberField
          id="max_exercises_per_session"
          label="Exercises per session"
          hint={`${sessionRange[0]}–${sessionRange[1]}`}
          value={v.max_exercises_per_session}
          min={sessionRange[0]}
          max={sessionRange[1]}
          error={shown.max_exercises_per_session}
          onChange={(n) => set("max_exercises_per_session", n)}
        />
        <NumberField
          id="advance_after_correct"
          label="Increase difficulty after"
          hint="correct answers in a row"
          value={v.advance_after_correct}
          min={ruleRange[0]}
          max={ruleRange[1]}
          error={shown.advance_after_correct}
          onChange={(n) => set("advance_after_correct", n)}
        />
        <NumberField
          id="step_back_after_incorrect"
          label="Decrease difficulty after"
          hint="incorrect or skipped in a row"
          value={v.step_back_after_incorrect}
          min={ruleRange[0]}
          max={ruleRange[1]}
          error={shown.step_back_after_incorrect}
          onChange={(n) => set("step_back_after_incorrect", n)}
        />
      </div>

      <div className="flex flex-col gap-1">
        <label htmlFor="note" className="font-bold">
          Note (optional)
        </label>
        <textarea
          id="note"
          maxLength={500}
          rows={2}
          value={v.note ?? ""}
          onChange={(e) => set("note", e.target.value || null)}
          className="rounded-control border-2 border-line-strong bg-surface px-3 py-2"
        />
      </div>

      <p
        role="status"
        className={pictures === 0 ? "font-bold text-danger" : "text-ink-muted"}
      >
        {pictures === 0
          ? "No pictures in the library match these categories and difficulty range. The patient would not be able to practise."
          : `${pictures} pictures in the library match these limits.`}
      </p>

      <div className="flex flex-wrap gap-3">
        <Button type="submit">Review changes</Button>
        <Button variant="secondary" onClick={() => setStep("closed")}>
          Cancel
        </Button>
      </div>
    </form>
  );
}
