# Accessibility

Target: WCAG 2.1 AA. Self-assessed for this academic prototype — not a formal audit; manual
screen-reader testing with real users with aphasia has not been done.

## Automated checks (run on every E2E run)

| Check | Where |
|---|---|
| axe-core, WCAG 2.0/2.1 A + AA rules | login, patient home, practice (question, feedback, hints), all clinician screens, constraint editor and review |
| No horizontal scrolling at 375px (phone) and 768px (tablet) | `e2e/responsive.spec.ts` |
| Every visible control ≥ 44×44px (patient controls are 48–112px) | same |
| `prefers-reduced-motion` disables animation | same |
| Keyboard: skip link, focus moves to the answer field / Next button / review heading | `auth`, `practice`, `clinician` specs |
| No browser console errors on clinician screens | `clinician.spec.ts` |

## Design decisions

- Atkinson Hyperlegible Next; 18px base; patient prompts 36px; one task per screen.
- Single, high-contrast focus ring everywhere; text/background pairs meet AA (most AAA).
- Status is always icon + text, never colour alone; errors use `role="alert"`, other
  updates `role="status"`.
- Charts: single series, titled and described, native per-point tooltips, and a data
  table for every chart.
- Picture alt text says "Picture to name" — naming the object would give the answer
  away. Picture naming is inherently visual; typing/speaking alternatives are provided
  for the answer, not the stimulus.
- Clinician tables use `scope`, captions, and scroll inside their container on narrow screens.

## Known gaps

- No manual NVDA/VoiceOver pass recorded; no user testing with people with aphasia.
- No dark mode or user-adjustable text size beyond browser zoom.
- Speech recording relies on browser `MediaRecorder`; unsupported browsers fall back to typing.
