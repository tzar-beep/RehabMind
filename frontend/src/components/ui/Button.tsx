import type { ComponentPropsWithRef } from "react";

type Variant = "primary" | "secondary" | "quiet";
type Size = "md" | "lg";

const base =
  "inline-flex min-h-target min-w-target items-center justify-center gap-2 rounded-control " +
  "font-bold transition-colors disabled:cursor-not-allowed disabled:opacity-60";

const variants: Record<Variant, string> = {
  primary: "bg-accent text-white hover:bg-accent-hover",
  secondary: "border-2 border-accent bg-surface text-accent hover:bg-accent-soft",
  quiet: "text-ink-muted underline-offset-4 hover:text-ink hover:underline",
};

const sizes: Record<Size, string> = {
  md: "px-5 text-base",
  lg: "min-h-16 px-8 text-xl",
};

/** Button styling for links that act as primary navigation (e.g. "Start practice"). */
export function buttonClasses(variant: Variant = "primary", size: Size = "md"): string {
  return `${base} ${variants[variant]} ${sizes[size]}`;
}

export interface ButtonProps extends ComponentPropsWithRef<"button"> {
  variant?: Variant;
  size?: Size;
  busy?: boolean;
}

export function Button({
  variant = "primary",
  size = "md",
  busy = false,
  className = "",
  disabled,
  children,
  type = "button",
  ...props
}: ButtonProps) {
  return (
    <button
      type={type}
      className={`${base} ${variants[variant]} ${sizes[size]} ${className}`}
      disabled={disabled || busy}
      aria-busy={busy || undefined}
      {...props}
    >
      {children}
    </button>
  );
}
