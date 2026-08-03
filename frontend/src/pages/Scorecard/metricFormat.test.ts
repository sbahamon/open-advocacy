import { describe, it, expect } from 'vitest';
import { EMPTY_METRIC_LABEL, formatMetricValue } from './metricFormat';

describe('formatMetricValue', () => {
  it('renders an em dash for null and undefined', () => {
    expect(formatMetricValue(null)).toBe(EMPTY_METRIC_LABEL);
    expect(formatMetricValue(undefined)).toBe(EMPTY_METRIC_LABEL);
  });

  it('renders an em dash for blank strings', () => {
    expect(formatMetricValue('')).toBe(EMPTY_METRIC_LABEL);
    expect(formatMetricValue('   ')).toBe(EMPTY_METRIC_LABEL);
  });

  it('formats numbers with locale grouping', () => {
    expect(formatMetricValue(1234)).toBe((1234).toLocaleString());
    expect(formatMetricValue(0)).toBe('0');
  });

  it('formats numeric strings as numbers', () => {
    expect(formatMetricValue('1234')).toBe((1234).toLocaleString());
    expect(formatMetricValue('128.5')).toBe((128.5).toLocaleString());
  });

  it('passes non-numeric strings through unchanged', () => {
    expect(formatMetricValue('n/a')).toBe('n/a');
  });

  it('falls back to default formatting for unknown format values', () => {
    expect(formatMetricValue(1234, 'not-a-real-format')).toBe((1234).toLocaleString());
    expect(formatMetricValue(1234, 'number')).toBe((1234).toLocaleString());
  });

  it('formats percentages from a 0-100 value with one decimal', () => {
    expect(formatMetricValue(19.68, 'percentage')).toBe('19.7%');
    expect(formatMetricValue(0, 'percentage')).toBe('0.0%');
    expect(formatMetricValue('1.16', 'percentage')).toBe('1.2%');
  });
});
