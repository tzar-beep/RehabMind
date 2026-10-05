export function SkipLink({ target = "main" }: { target?: string }) {
  return (
    <a
      href={`#${target}`}
      className="sr-only rounded-control bg-surface px-4 py-3 font-bold focus:not-sr-only focus:absolute focus:left-4 focus:top-4 focus:z-50"
    >
      Skip to main content
    </a>
  );
}
