import { LoadingRegion, Skeleton } from "@/components/ui/Skeleton";

/** Same shape as the patient pages: one screen, nothing to scroll while it loads. */
export default function PatientLoading() {
  return (
    <LoadingRegion label="Loading…" className="min-h-0 flex-1 gap-4">
      <Skeleton className="min-h-0 flex-1 rounded-card" />
      <Skeleton className="h-48 shrink-0 rounded-card" />
    </LoadingRegion>
  );
}
