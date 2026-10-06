import type { Metadata } from "next";
import { z } from "zod";

import { StatusBadge } from "@/components/clinician/StatusBadge";
import { Alert } from "@/components/ui/Alert";
import { Avatar } from "@/components/ui/Avatar";
import { UserSummarySchema } from "@/lib/api/schemas";
import { backendGet, getCurrentUser } from "@/lib/api/server";

import { AccountActions } from "./AccountActions";
import { AddUserForm } from "./AddUserForm";

export const metadata: Metadata = { title: "Accounts" };

export default async function AdminHome() {
  const [users, me] = await Promise.all([
    backendGet("/admin/users", z.array(UserSummarySchema)).then((u) => u ?? []),
    getCurrentUser(),
  ]);
  const clinicians = users
    .filter((u) => u.role === "clinician" && u.is_active)
    .map((u) => ({ id: u.id, name: u.display_name }));
  const unassigned = users.filter(
    (u) => u.role === "patient" && u.is_active && u.care_team.length === 0,
  ).length;

  return (
    <div className="flex flex-col gap-6">
      <h1 className="text-3xl font-bold">Accounts</h1>
      <AddUserForm clinicians={clinicians} />
      <h2 className="mt-4 text-2xl font-bold">User list</h2>
      {unassigned > 0 && (
        <Alert tone="warning">
          {unassigned === 1 ? "1 patient has" : `${unassigned} patients have`}{" "}
          no clinician yet. They cannot practise until a clinician is assigned
          and sets practice limits.
        </Alert>
      )}
      <div
        tabIndex={0}
        aria-label="Scrollable table"
        className="overflow-x-auto rounded-card border border-line bg-surface shadow-card"
      >
        <table className="w-full text-left">
          <caption className="sr-only">All user accounts</caption>
          <thead className="border-b border-line text-sm text-ink-muted">
            <tr>
              <th scope="col" className="px-6 py-3">
                Name
              </th>
              <th scope="col" className="px-6 py-3">
                Email
              </th>
              <th scope="col" className="px-6 py-3">
                Role
              </th>
              <th scope="col" className="px-6 py-3">
                Status
              </th>
              <th scope="col" className="px-6 py-3">
                Care team
              </th>
              <th scope="col" className="px-6 py-3">
                Actions
              </th>
            </tr>
          </thead>
          <tbody className="divide-y divide-line">
            {users.map((u) => (
              <tr key={u.id} className="transition-colors hover:bg-canvas/60">
                <td className="px-6 py-3 font-bold whitespace-nowrap">
                  <span className="flex items-center gap-3">
                    <Avatar name={u.display_name} size="sm" />
                    {u.display_name}
                  </span>
                </td>
                <td className="px-6 py-3">{u.email}</td>
                <td className="px-6 py-3">
                  <span className="rounded-full bg-canvas px-3 py-1 text-sm font-bold capitalize ring-1 ring-line">
                    {u.role}
                  </span>
                </td>
                <td className="px-6 py-3">
                  {u.is_active ? (
                    <StatusBadge tone="success">Active</StatusBadge>
                  ) : (
                    <StatusBadge tone="neutral">Disabled</StatusBadge>
                  )}
                </td>
                <td className="px-6 py-3">
                  {u.role !== "patient" ? (
                    <span className="text-ink-muted">—</span>
                  ) : u.care_team.length ? (
                    <span className="whitespace-nowrap">
                      {u.care_team.join(", ")}
                    </span>
                  ) : (
                    <StatusBadge tone="warning">Not assigned</StatusBadge>
                  )}
                </td>
                <td className="px-6 py-3 align-top">
                  <AccountActions
                    user={u}
                    clinicians={clinicians}
                    isSelf={u.id === me?.id}
                  />
                </td>
              </tr>
            ))}
          </tbody>
        </table>
      </div>
    </div>
  );
}
