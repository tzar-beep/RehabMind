import Link from "next/link";

import { buttonClasses } from "@/components/ui/Button";

export default function SessionNotFound() {
  return (
    <div className="flex flex-col items-start gap-4">
      <h1 className="text-2xl font-bold">Session not found</h1>
      <p className="text-ink-muted">
        This practice session does not exist for this patient. It may be from an
        old link.
      </p>
      <Link href="../sessions" className={buttonClasses("secondary")}>
        Back to session history
      </Link>
    </div>
  );
}
