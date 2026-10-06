import { useId, type ComponentPropsWithRef, type ReactNode } from "react";

export interface TextFieldProps extends ComponentPropsWithRef<"input"> {
  label: string;
  hint?: string;
  error?: string;
  /** Control shown inside the right edge of the input (e.g. show password). */
  trailing?: ReactNode;
}

/** Labelled input with hint and error text wired up for assistive technology. */
export function TextField({
  label,
  hint,
  error,
  trailing,
  id,
  className = "",
  ...props
}: TextFieldProps) {
  const autoId = useId();
  const inputId = id ?? autoId;
  const hintId = hint ? `${inputId}-hint` : undefined;
  const errorId = error ? `${inputId}-error` : undefined;

  return (
    <div className="flex flex-col gap-1.5">
      <label htmlFor={inputId} className="text-base font-bold">
        {label}
      </label>
      {hint && (
        <p id={hintId} className="text-sm text-ink-muted">
          {hint}
        </p>
      )}
      <div className="relative">
        <input
          id={inputId}
          aria-invalid={error ? true : undefined}
          aria-describedby={
            [hintId, errorId].filter(Boolean).join(" ") || undefined
          }
          className={
            "min-h-target w-full rounded-control border-2 bg-surface px-4 text-lg " +
            (trailing ? "pr-16 " : "") +
            (error ? "border-danger " : "border-line-strong ") +
            className
          }
          {...props}
        />
        {trailing && (
          <div className="absolute inset-y-0 right-1 flex items-center">
            {trailing}
          </div>
        )}
      </div>
      {error && (
        <p id={errorId} className="text-sm font-bold text-danger">
          {error}
        </p>
      )}
    </div>
  );
}
