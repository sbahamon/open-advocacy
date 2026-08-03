/** Pure color-scale helpers for the ward choropleth. */

export type AuditColorMetric = 'zoning_median_days' | 'zoning_stalled_count' | 'zoning_matter_count';

export const COLOR_METRIC_LABELS: Record<AuditColorMetric, string> = {
  zoning_median_days: 'Median delay (days)',
  zoning_stalled_count: 'Stalled >180d',
  zoning_matter_count: 'Rezonings (count)',
};

// Light → dark sequential ramp (5 bins). Same hue family as the app's primary.
export const SCALE_COLORS = ['#e3f2fd', '#90caf9', '#42a5f5', '#1976d2', '#0d47a1'];
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
