import { describe, it, expect } from 'vitest';
import { wardNumberFromDistrictName } from './wardNumberFromDistrictName';

describe('wardNumberFromDistrictName', () => {
  it('parses "Ward N" district names case-insensitively', () => {
    expect(wardNumberFromDistrictName('Ward 35')).toBe(35);
    expect(wardNumberFromDistrictName('ward 1')).toBe(1);
    expect(wardNumberFromDistrictName('  Ward 50 ')).toBe(50);
  });

  it('never guesses on non-ward names', () => {
    expect(wardNumberFromDistrictName('District 12')).toBeNull();
    expect(wardNumberFromDistrictName('Ward')).toBeNull();
    expect(wardNumberFromDistrictName('Ward 12B')).toBeNull();
  });
});
