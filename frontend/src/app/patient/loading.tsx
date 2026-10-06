import { LoadingRegion, Skeleton } from "@/components/ui/Skeleton";

export default function PatientLoading() {
  return (
    <LoadingRegion label="Loading your home page…" className="gap-10">
      <Skeleton className="h-64 rounded-card" />
      <Skeleton className="h-52 rounded-card" />
      <div className="grid gap-4 sm:grid-cols-3">
        <Skeleton className="h-44 rounded-card" />
        <Skeleton className="h-44 rounded-card" />
        <Skeleton className="h-44 rounded-card" />
      </div>
    </LoadingRegion>
  );
}
