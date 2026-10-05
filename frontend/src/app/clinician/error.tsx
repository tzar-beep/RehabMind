"use client";

import { Alert } from "@/components/ui/Alert";
import { Button } from "@/components/ui/Button";

export default function ClinicianError({
  reset,
}: {
  error: Error;
  reset: () => void;
}) {
  return (
    <div className="flex flex-col gap-4">
      <Alert tone="error">
        This information could not be loaded. Please try again. If it keeps
        happening, the service may be unavailable.
      </Alert>
      <div>
        <Button onClick={reset}>Try again</Button>
      </div>
    </div>
  );
}
