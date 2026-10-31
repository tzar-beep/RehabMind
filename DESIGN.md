# Design

RehabMind's visual world is a **patient ID wristband**: the calm, printed object people already trust in a hospital. Signing in is identification, and the rest of the app is the label it carries. It should read as healthcare at a glance, without hospital coldness.

## Parts

- **Strap** (`.strap`, `.strap-stud`, `.strap-hole` in `globals.css`): moulded mint plastic. It is the header on every signed-in page (`AppShell`) and runs behind the card on the sign-in page. Holes and studs are decoration: always `aria-hidden`, hidden when space is short, and only on the sign-in page. In a working header they read as controls or progress steps, so the header keeps the moulded strap alone.
- **Label**: a white card, `rounded-card border border-line bg-surface shadow-card`. This is the default container. Never nest labels; use `rounded-control` with `bg-canvas` or `bg-accent-soft` for a panel inside one.
- **Label strip** (`LabelStrip`): the teal strip along the top of a label. Only for a screen's one main panel, never on every card.
- **Printed cells** (`Facts`, the sign-in details): figures and details in fixed cells split by 1px rules. Rank comes from weight and rules, not from extra type sizes or icons.
- **Barcode**: sign-in only. It is decoration, and repeating it would turn it into a costume.

## Colour

Tokens live in `@theme` in `globals.css`. Use them rather than raw values.

| Token | Value | Use |
|---|---|---|
| `canvas` | `#f2f5f5` | Page ground |
| `surface` | `#ffffff` | Labels, inputs |
| `ink` / `ink-muted` | `#1c2430` / `#4a5565` | Text |
| `line` / `line-strong` | `#dde3e3` / `#6f7a7b` | Rules / input borders |
| `accent` / `accent-hover` | `#0f6e6e` / `#0b5858` | Primary actions, label strip |
| `accent-soft` | `#e3f0ee` | Quiet emphasis, notes |
| `brand-deep` | `#0a3d3e` | Word chips on photos, AI pipeline map |
| Strap gradient | `#e3f3f0` to `#b3dbd4` | Strap only |

Teal is the only accent. The one exception is the logo's dot (`#f4b860` on dark and teal, `#c8652b` on light), which appears only in the logo, never in the interface. Success, warning and danger are for state, never decoration. All text pairs meet WCAG 2.1 AA.

## Type

Atkinson Hyperlegible Next throughout: it was designed for low-vision readers, and the audience has aphasia. No second display face. Headings are bold with slight negative tracking. Tabular figures for numbers.

## Depth and shape

- Resting labels use `shadow-card`; only what floats uses `shadow-float`.
- Radii: `rounded-card` (1.25rem) for labels, `rounded-control` (0.75rem) for controls and inner panels.
- No gradients other than the strap, no glass, no coloured side borders.

## Motion

One authored moment: on sign-in the strap slides in and the stud presses home. App pages keep their existing small feedback animations. The global reduced-motion rule covers everything.

## Rules that outrank the look

- Patient pages fit one screen at laptop sizes without scrolling.
- Targets stay at least 48px (`min-h-target`); patient actions are larger.
- Plain language, and no streak pressure.
- Never imply a real ID or medical record: the wristband's printed details are product truths, not patient data.
