import type { Metadata } from "next";
import { z } from "zod";

import { UserSummarySchema } from "@/lib/api/schemas";
import { backendGet } from "@/lib/api/server";

export const metadata: Metadata = { title: "Accounts" };

export default async function AdminHome() {
  const users =
    (await backendGet("/admin/users", z.array(UserSummarySchema))) ?? [];

  return (
    <div className="flex flex-col gap-6">
      <h1 className="text-3xl font-bold">Accounts</h1>
      <div className="overflow-x-auto rounded-card border border-line bg-surface">
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
            </tr>
          </thead>
          <tbody className="divide-y divide-line">
            {users.map((u) => (
              <tr key={u.id}>
                <td className="px-6 py-3 font-bold">{u.display_name}</td>
                <td className="px-6 py-3">{u.email}</td>
                <td className="px-6 py-3 capitalize">{u.role}</td>
                <td className="px-6 py-3">
                  {u.is_active ? "Active" : "Disabled"}
                </td>
              </tr>
            ))}
          </tbody>
        </table>
      </div>
    </div>
  );
}
