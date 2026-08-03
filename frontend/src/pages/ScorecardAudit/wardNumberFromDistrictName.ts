/**
 * Parse a ward number from a district name like "Ward 35".
 *
 * Mirrors the backend's `parse_ward_number` district-name branch: never
 * guesses — anything unparseable returns null.
 */
export function wardNumberFromDistrictName(districtName: string): number | null {
  const match = /^ward\s+(\d+)$/i.exec(districtName.trim());
  if (!match) return null;
  const ward = parseInt(match[1], 10);
  return Number.isNaN(ward) ? null : ward;
}
