import { execSync } from "node:child_process";
import path from "node:path";

// Repeated local e2e runs exceed the per-IP login limit by design; reset it (dev only).
export default function globalSetup() {
  execSync("uv run python -m app.scripts.reset_rate_limits", {
    cwd: path.resolve(__dirname, "../../backend"),
    stdio: "inherit",
  });
}
