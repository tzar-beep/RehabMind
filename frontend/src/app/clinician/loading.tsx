import { LoadingRegion, Skeleton } from "@/components/ui/Skeleton";

export default function ClinicianLoading() {
  return (
    <LoadingRegion label="Loading your patients…" className="gap-10">
      <Skeleton className="h-56 rounded-card" />
      <div className="grid grid-cols-1 gap-4 min-[420px]:grid-cols-2 md:grid-cols-4">
        {[0, 1, 2, 3].map((i) => (
          <Skeleton key={i} className="h-36 rounded-card" />
        ))}
      </div>
      <Skeleton className="h-40 rounded-card" />
    </LoadingRegion>
  );
}
