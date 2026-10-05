export default function Loading() {
  return (
    <div role="status" aria-label="Loading" className="flex flex-col gap-6">
      <div className="h-9 w-64 animate-pulse rounded-control bg-line motion-reduce:animate-none" />
      <div className="h-28 animate-pulse rounded-card bg-line motion-reduce:animate-none" />
      <div className="h-64 animate-pulse rounded-card bg-line motion-reduce:animate-none" />
      <span className="sr-only">Loading…</span>
    </div>
  );
}
