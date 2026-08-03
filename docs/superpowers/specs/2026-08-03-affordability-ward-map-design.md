# Affordability on the Ward Map — Design

**Date:** 2026-08-03
**Status:** Approved (user-reviewed in session)

## Goal

Show the community-collected Zillow affordability data on a map. The existing
audit page at `/scorecard/:groupSlug/audit` already renders a ward choropleth;
extend it into a general **"Ward Map & Audit"** rather than building a second
map page.

## Decisions (user-confirmed)

1. **Placement:** extend the existing audit page; no new route, no second map.
2. **Ward detail panel:** on ward click, always show **both** the affordability
   context card **and** the zoning matters docket, regardless of which metric
   is coloring the map. The active toggle affects only the choropleth colors
   and tooltip emphasis. Card renders above the docket (it is compact).

## Backend (additive; endpoint URL unchanged)

- New pydantic model `WardAffordability` in
  `backend/app/models/pydantic/models.py`: `neighborhoods`,
  `affordable_share_pct` (2026), `affordable_share_pct_2025`,
  `affordable_listings_2025/2026`, `total_listings_2025/2026`,
  `affordability_rank_2025/2026`, `affordability_rank_change`,
  `median_rent_2025/2026`, `median_sale_price_2025/2026`.
- `ZoningAuditWard` gains `affordability: WardAffordability | None = None`.
- `ZoningAuditResponse` gains `affordability_meta: dict[str, Any] = {}`
  (= `AFFORDABILITY_META`: as-of, source attribution, collection windows,
  citywide shares).
- `backend/app/services/zoning_audit_service.py` populates both from the
  committed `WARD_AFFORDABILITY` / `AFFORDABILITY_META`
  (`app/data/ward_affordability_data.py`), with the same defensive-import
  pattern as the other generated modules; wards missing from the data get
  `affordability=None`.
- `GET /api/scorecard/{group_slug}/zoning-audit` is unchanged otherwise —
  strictly additive, backward compatible.

## Frontend

Page title becomes **"Ward Map & Audit"**; intro sentence updated to mention
both metric families.

- `frontend/src/types/index.ts`: `WardAffordability` interface;
  `ZoningAuditWard.affordability?`; `ZoningAuditResponse.affordability_meta`.
- `wardColorScale.ts`:
  - `AuditColorMetric` gains `'affordable_share_pct'` and
    `'affordability_rank_change'` (labels in `COLOR_METRIC_LABELS`).
  - Affordable share reuses the sequential blue ramp (darker = more
    affordable).
  - Rank change is **diverging** (negative = dropped, positive = improved):
    new pure `divergingColorForValue(value, maxAbs)` mapping through a
    red ↔ neutral ↔ green ramp centered at 0. A signed quantile through the
    sequential ramp would color "no change" a misleading mid-blue.
  - Load the `dataviz` skill before finalizing exact ramp hex values at
    implementation time.
- `MetricToggle.tsx`: five buttons (wraps on small screens).
- `WardChoroplethMap.tsx`: per-metric value selector (zoning values from the
  ward stats, affordability values from `ward.affordability`); picks
  sequential vs diverging coloring by metric; tooltip appends the two
  affordability lines when an affordability metric is active.
- New `AffordabilityCard.tsx` (one component per file, co-located test):
  neighborhoods, 2025→2026 share with raw affordable/total listing counts
  (small-N made visible), rank movement (e.g. "48 → 46 (+2)"), median rent and
  sale price both years. Renders "No affordability survey data" fallback when
  `affordability` is null.
- `index.tsx` detail panel: `AffordabilityCard` above `WardMattersTable` on
  every ward selection.
- `AuditMeta.tsx`: one added caption line with the survey source + as-of from
  `affordability_meta`, mirroring the scorecard footnote.

## Testing

- Backend (`tests/test_zoning_audit_service.py`): wards carry affordability
  values matching `WARD_AFFORDABILITY`; `affordability_meta` passthrough;
  service still works with the module absent (patched to empty → `None`s).
- Frontend (vitest): `divergingColorForValue` units (negative/zero/positive,
  missing → neutral); `AffordabilityCard` renders values and the null
  fallback; index test asserts card + docket both render on ward selection.
- Gates: backend ruff/mypy/pytest; frontend lint/type-check/vitest (node:20
  Docker). Cold-start `docker-compose.verify.yaml` check: toggle to
  "Affordable listings" colors the map, ward click shows card + docket.

## Out of scope

- No second map page, no scorecard-page map embed.
- No new chart library; ramps are pure functions.
- No change to which affordability metrics appear on the scorecard table.
