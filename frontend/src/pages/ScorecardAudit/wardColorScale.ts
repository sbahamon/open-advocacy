/** Pure color-scale helpers for the ward choropleth. */

export type AuditColorMetric =
  | 'zoning_median_days'
  | 'zoning_stalled_count'
  | 'zoning_matter_count'
  | 'affordable_share_pct'
  | 'affordability_rank_change';

export const COLOR_METRIC_LABELS: Record<AuditColorMetric, string> = {
  zoning_median_days: 'Median delay (days)',
  zoning_stalled_count: 'Stalled >180d',
  zoning_matter_count: 'Rezonings (count)',
  affordable_share_pct: 'Affordable listings (%)',
  affordability_rank_change: 'Affordability rank change',
};

/** Metrics whose value is signed (better/worse around zero) → diverging ramp. */
export const DIVERGING_METRICS: ReadonlySet<AuditColorMetric> = new Set([
  'affordability_rank_change',
]);

// Sequential: one hue, light → dark (validated blue ramp, steps 100→700).
export const SCALE_COLORS = ['#cde2fb', '#86b6ef', '#3987e5', '#1c5cab', '#0d366b'];
// Diverging: warm pole (declined) ↔ neutral gray ↔ cool pole (improved).
// Red↔green was rejected as CVD-hostile; blue↔red poles read as opposites.
export const DIVERGING_COLORS = ['#e34948', '#eda3a2', '#f0efec', '#86b6ef', '#256abf'];
export const MISSING_COLOR = '#e0e0e0';

/**
 * Quantile bin edges for a set of values: SCALE_COLORS.length - 1 cut points
 * at evenly spaced quantiles. Duplicate-heavy distributions simply reuse edges
 * (values then land in the lowest matching bin).
 */
export function quantileBins(values: number[]): number[] {
  const sorted = [...values].sort((a, b) => a - b);
  if (sorted.length === 0) return [];
  const edges: number[] = [];
  for (let i = 1; i < SCALE_COLORS.length; i++) {
    const idx = Math.min(
      sorted.length - 1,
      Math.floor((i / SCALE_COLORS.length) * sorted.length)
    );
    edges.push(sorted[idx]);
  }
  return edges;
}

/** Color for one value against the given bin edges; null → MISSING_COLOR. */
export function colorForValue(value: number | null | undefined, edges: number[]): string {
  if (value == null || Number.isNaN(value) || edges.length === 0) return MISSING_COLOR;
  for (let i = 0; i < edges.length; i++) {
    if (value < edges[i]) return SCALE_COLORS[i];
  }
  return SCALE_COLORS[SCALE_COLORS.length - 1];
}

/**
 * Diverging color for a signed value, symmetric about zero.
 *
 * `maxAbs` is the largest |value| in the dataset; each arm splits it evenly
 * into two bands, and zero (or a missing maxAbs) lands on the neutral
 * midpoint. Quantile-binning signed values through the sequential ramp would
 * color "no change" a misleading mid-blue.
 */
export function divergingColorForValue(
  value: number | null | undefined,
  maxAbs: number
): string {
  if (value == null || Number.isNaN(value)) return MISSING_COLOR;
  if (value === 0 || maxAbs <= 0) return DIVERGING_COLORS[2];
  const strong = Math.abs(value) > maxAbs / 2;
  if (value < 0) return strong ? DIVERGING_COLORS[0] : DIVERGING_COLORS[1];
  return strong ? DIVERGING_COLORS[4] : DIVERGING_COLORS[3];
}
