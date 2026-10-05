// Copies curated stimulus images listed in the backend catalog into public/stimuli.
// The catalog (backend/app/exercises/stimuli_catalog.json) is the single source of truth.
import { copyFileSync, mkdirSync, readFileSync } from "node:fs";
import { dirname, join } from "node:path";
import { fileURLToPath } from "node:url";

const root = join(dirname(fileURLToPath(import.meta.url)), "..");
const catalog = JSON.parse(
  readFileSync(join(root, "../backend/app/exercises/stimuli_catalog.json"), "utf8"),
);
const out = join(root, "public/stimuli");
mkdirSync(out, { recursive: true });
for (const s of catalog.stimuli) {
  copyFileSync(
    join(root, "node_modules/lucide-static/icons", `${s.source_icon}.svg`),
    join(out, `${s.slug}.svg`),
  );
}
copyFileSync(join(root, "node_modules/lucide-static/LICENSE"), join(out, "LICENSE-lucide.txt"));
console.log(`copied ${catalog.stimuli.length} stimuli`);
