# Vendored Magic UI component

Source: [Magic UI](https://magicui.design) (`github.com/magicuidesign/magicui`), MIT licence,
copied from the registry (`glyph-matrix`). Used on the sign-in page only; decorative and
`aria-hidden`.

Local changes to `glyph-matrix.tsx`:

- with `prefers-reduced-motion` it draws one still frame and never animates;
- new `settleAfter` prop: stops changing after that many ms so the page comes to rest
  (no constant background motion).
