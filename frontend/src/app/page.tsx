import { redirect } from "next/navigation";

import { ROLE_HOME } from "@/lib/api/schemas";
import { getCurrentUser } from "@/lib/api/server";

export default async function Home() {
  const me = await getCurrentUser();
  redirect(me ? ROLE_HOME[me.role] : "/login");
}
