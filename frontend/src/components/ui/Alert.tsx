import type { ReactNode } from "react";

type Tone = "info" | "success" | "warning" | "error";

const tones: Record<Tone, string> = {
  info: "border-accent bg-accent-soft",
  success: "border-success bg-success-soft",
  warning: "border-warning bg-warning-soft",
  error: "border-danger bg-danger-soft",
};

/** Errors are announced immediately (role=alert); other tones politely (role=status). */
export function Alert({ tone = "info", children }: { tone?: Tone; children: ReactNode }) {
  return (
    <div
      role={tone === "error" ? "alert" : "status"}
      className={`rounded-control border-l-4 px-4 py-3 text-base ${tones[tone]}`}
    >
      {children}
    </div>
  );
}
