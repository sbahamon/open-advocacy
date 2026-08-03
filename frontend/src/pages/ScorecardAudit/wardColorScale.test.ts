import { describe, it, expect } from 'vitest';
import {
  colorForValue,
  MISSING_COLOR,
  quantileBins,
  SCALE_COLORS,
} from './wardColorScale';

describe('quantileBins', () => {
  it('returns one fewer edge than there are colors', () => {
    const edges = quantileBins([1, 2, 3, 4, 5, 6, 7, 8, 9, 10]);
    expect(edges).toHaveLength(SCALE_COLORS.length - 1);
  });

  it('returns no edges for an empty input', () => {
    expect(quantileBins([])).toEqual([]);
  });
});

describe('colorForValue', () => {
  const edges = quantileBins([10, 20, 30, 40, 50, 60, 70, 80, 90, 100]);

  it('maps low values to the light end and high values to the dark end', () => {
    expect(colorForValue(1, edges)).toBe(SCALE_COLORS[0]);
    expect(colorForValue(1000, edges)).toBe(SCALE_COLORS[SCALE_COLORS.length - 1]);
  });

  it('renders missing values with the neutral color', () => {
    expect(colorForValue(null, edges)).toBe(MISSING_COLOR);
    expect(colorForValue(undefined, edges)).toBe(MISSING_COLOR);
    expect(colorForValue(50, [])).toBe(MISSING_COLOR);
  });
});
