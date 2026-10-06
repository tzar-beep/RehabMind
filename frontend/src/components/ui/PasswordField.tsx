"use client";

import { Eye, EyeOff } from "lucide-react";
import { useState } from "react";

import { TextField, type TextFieldProps } from "./TextField";

/** Password input with a show/hide button, so people can check what they typed. */
export function PasswordField(
  props: Omit<TextFieldProps, "type" | "trailing">,
) {
  const [visible, setVisible] = useState(false);
  const Icon = visible ? EyeOff : Eye;
  return (
    <TextField
      {...props}
      type={visible ? "text" : "password"}
      trailing={
        <button
          type="button"
          onClick={() => setVisible((v) => !v)}
          aria-pressed={visible}
          aria-label="Show password"
          className="grid size-11 place-items-center rounded-control text-ink-muted transition-colors hover:bg-accent-soft hover:text-ink"
        >
          <Icon aria-hidden="true" size={22} />
        </button>
      }
    />
  );
}
