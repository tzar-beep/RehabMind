import { LoadingRegion, Skeleton } from "@/components/ui/Skeleton";

export default function PatientPageLoading() {
  return (
    <LoadingRegion label="Loading…" className="gap-8">
      <Skeleton className="h-7 w-72" />
      <Skeleton className="h-44 rounded-card" />
      <div className="grid grid-cols-1 gap-4 min-[420px]:grid-cols-2 md:grid-cols-4">
        {[0, 1, 2, 3].map((i) => (
          <Skeleton key={i} className="h-32 rounded-card" />
        ))}
      </div>
      <Skeleton className="h-72 rounded-card" />
    </LoadingRegion>
  );
}
