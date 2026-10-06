"use client";

import { RefreshCw } from "lucide-react";
import Link from "next/link";

import { Button, buttonClasses } from "@/components/ui/Button";

/** Anything unexpected outside the clinician area (which has its own message). */
export default function AppError({
  reset,
}: {
  error: Error;
  reset: () => void;
}) {
  return (
    <main
      id="main"
      className="flex flex-1 flex-col items-center justify-center gap-6 px-6 py-16 text-center"
    >
      <h1 className="text-3xl font-bold">Something went wrong</h1>
      <p className="max-w-md text-lg text-ink-muted">
        This page could not be shown. Your practice so far is saved. Please try
        again.
      </p>
      <div className="flex flex-wrap justify-center gap-3">
        <Button size="lg" onClick={reset}>
          <RefreshCw aria-hidden="true" size={20} />
          Try again
        </Button>
        <Link href="/" className={buttonClasses("secondary", "lg")}>
          Go to my home page
        </Link>
      </div>
    </main>
  );
}
