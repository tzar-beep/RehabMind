import { render, screen } from "@testing-library/react";
import { describe, expect, it } from "vitest";
import { axe } from "vitest-axe";

import { Alert } from "./Alert";
import { Button } from "./Button";
import { TextField } from "./TextField";

describe("TextField", () => {
  it("associates label, hint and error with the input", () => {
    render(
      <TextField
        label="Email"
        hint="Your work email"
        error="Email is required"
      />,
    );
    const input = screen.getByLabelText("Email");
    expect(input).toHaveAttribute("aria-invalid", "true");
    expect(input).toHaveAccessibleDescription(
      "Your work email Email is required",
    );
  });

  it("has no axe violations", async () => {
    const { container } = render(
      <TextField label="Password" type="password" error="Too short" />,
    );
    expect((await axe(container)).violations).toEqual([]);
  });
});

describe("Button", () => {
  it("defaults to type=button and disables while busy", () => {
    render(<Button busy>Save</Button>);
    const button = screen.getByRole("button", { name: "Save" });
    expect(button).toHaveAttribute("type", "button");
    expect(button).toBeDisabled();
    expect(button).toHaveAttribute("aria-busy", "true");
  });

  it("meets the minimum target size class", () => {
    render(<Button>Go</Button>);
    expect(screen.getByRole("button").className).toContain("min-h-target");
  });
});

describe("Alert", () => {
  it("announces errors assertively and other messages politely", () => {
    render(
      <>
        <Alert tone="error">Failed</Alert>
        <Alert tone="success">Saved</Alert>
      </>,
    );
    expect(screen.getByRole("alert")).toHaveTextContent("Failed");
    expect(screen.getByRole("status")).toHaveTextContent("Saved");
  });
});
