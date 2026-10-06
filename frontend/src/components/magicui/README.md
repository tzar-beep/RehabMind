# Vendored Magic UI component

Source: [Magic UI](https://magicui.design) (`github.com/magicuidesign/magicui`), MIT licence,
copied from the registry (`glyph-matrix`, `flickering-grid`). Decorative and
`aria-hidden`.

Local changes to `glyph-matrix.tsx`:

- with `prefers-reduced-motion` it draws one still frame and never animates;
- new `settleAfter` prop: stops changing after that many ms so the page comes to rest
  (no constant background motion).

`flickering-grid.tsx` (from `flickering-grid`, used behind the AI pipeline map): rewritten
without React state in effects; pauses off-screen; one still frame with reduced motion.
