# Vendored Magic UI components

Source: [Magic UI](https://magicui.design) (MIT), installed with
`npx shadcn@latest add https://magicui.design/r/<name>.json --path src/components/magicui`.

Local changes:
- `magic-card.tsx`: no `next-themes` (the app is light-only); uses the app's `surface` and
  `line` colours instead of `background` and `border`.
- `number-ticker.tsx`: shows the final number at once under `prefers-reduced-motion`; text
  colour is inherited.

Chosen for a calm product used by adults after a stroke: no continuous motion, nothing
childish. See the review in the commit that added them.
