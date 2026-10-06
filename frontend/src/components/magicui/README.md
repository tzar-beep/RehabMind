# Vendored Magic UI components

Source: [Magic UI](https://magicui.design) (`github.com/magicuidesign/magicui`), MIT licence,
copied from the registry (`glyph-matrix`, `border-beam`). Used on the sign-in page only.

Local changes (both are decorative and `aria-hidden`):
- `glyph-matrix.tsx`: with `prefers-reduced-motion` draws one still frame and never animates.
- `border-beam.tsx`: not rendered with `prefers-reduced-motion` (hydration-safe media query
  instead of `useReducedMotion`); dropped the unused `style`, `transition` and
  `initialOffset` props.
