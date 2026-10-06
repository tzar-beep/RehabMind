"use client";

import { useState } from "react";

import { constraintRows } from "@/components/clinician/ConstraintSummary";
import type { ConstraintVersion } from "@/lib/api/clinician";

/** Side-by-side, read-only comparison of any two versions. */
export function VersionCompare({
  versions,
}: {
  versions: ConstraintVersion[];
}) {
  const [a, setA] = useState(versions[1]?.version ?? versions[0].version);
  const [b, setB] = useState(versions[0].version);
  const va = versions.find((v) => v.version === a)!;
  const vb = versions.find((v) => v.version === b)!;
  const ra = constraintRows(va);
  const rb = constraintRows(vb);

  const picker = (
    id: string,
    label: string,
    value: number,
    onChange: (n: number) => void,
  ) => (
    <div className="flex flex-col gap-1">
      <label htmlFor={id} className="text-sm font-bold">
        {label}
      </label>
      <select
        id={id}
        value={value}
        onChange={(e) => onChange(Number(e.target.value))}
        className="min-h-target rounded-control border-2 border-line-strong bg-surface px-3"
      >
        {versions.map((v) => (
          <option key={v.version} value={v.version}>
            Version {v.version}
            {v.is_active ? " (active)" : ""}
          </option>
        ))}
      </select>
    </div>
  );

  return (
    <div className="flex flex-col gap-4 rounded-card border border-line bg-surface p-5 shadow-card">
      <div className="flex flex-wrap gap-4">
        {picker("cmp-a", "Compare", a, setA)}
        {picker("cmp-b", "With", b, setB)}
      </div>
      <table className="w-full text-left">
        <caption className="sr-only">
          Version {a} compared with version {b}
        </caption>
        <thead className="text-sm text-ink-muted">
          <tr>
            <th scope="col" className="py-2 pr-4">
              Setting
            </th>
            <th scope="col" className="py-2 pr-4">
              Version {a}
            </th>
            <th scope="col" className="py-2">
              Version {b}
            </th>
          </tr>
        </thead>
        <tbody className="divide-y divide-line">
          {ra.map((row, i) => {
            const diff = row.value !== rb[i].value;
            return (
              <tr
                key={row.label}
                className={diff ? "bg-accent-soft" : undefined}
              >
                <th scope="row" className="py-2 pr-4 font-normal">
                  {row.label}
                  {diff && (
                    <span className="ml-2 text-sm font-bold">(differs)</span>
                  )}
                </th>
                <td className="py-2 pr-4">{row.value}</td>
                <td className="py-2">{rb[i].value}</td>
              </tr>
            );
          })}
        </tbody>
      </table>
    </div>
  );
}
