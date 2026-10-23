# Vendored chart components

Source: [Bklit UI](https://bklit.com) (`github.com/bklit/bklit-ui`), MIT licence, installed
with `npx shadcn@latest add @bklit/line-chart @bklit/bar-chart`.

Kept as shipped (excluded from ESLint). Local changes:
- fixed the `shimmering-text` import path in `chart-loading-label.tsx`;
- `bar-chart.tsx`: vertical y-scales now use per-row sums for stacked bars (upstream used the
  largest single segment, so stacked bars overflowed the axis). RehabMind wraps these in `components/clinician/TrendCharts.tsx`,
which adds titles, descriptions and a data table for accessibility.
