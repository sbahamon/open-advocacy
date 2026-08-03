# Scorecard Zoning Metrics — Methodology & Audit Guide

This document explains the per-alderperson **zoning metrics** added to the Chicago
City Council scorecard (`/scorecard/strong-towns-chicago-chicago-city-council` and
the AHIL Chicago group). It is written for someone with **no prior context** who needs
to verify the numbers are correct, reproduce them, or extend them.

The metric groups:

| Metric | Status | Source |
|---|---|---|
| **Zoning delay** (median days + stalled count) | **Shipped (Phase 1)** | Fully automated from the City Clerk eLMS API |
| **Bonus units** / **Lost units** | Scaffolded, not yet populated (Phase 2) | Hand/agent-curated registry with mandatory citations |
| **First mention → passage** days | Scaffolded, hidden (Phase 3) | Curated registry |
| **Affordability** (affordable-listings share + rank change) | **Shipped** | Community-collected Zillow survey (see §7) |

The **delay** and **affordability** metrics are visible in the table today.
Bonus/lost-unit columns are declared but `show_in_table=False` until the curated
registry is populated.

---

## 1. Definitions

**Term window.** All zoning-delay figures cover matters **introduced on or after
2023-05-15** (`TERM_START`), the start of the 2023–2027 City Council term. Older matters
are excluded.

**Zoning reclassification.** A Chicago City Council "map amendment" — the ordinance that
rezones a parcel. In eLMS these have `matterCategory == "ZONING RECLASSIFICATIONS"` and
titles like `Zoning Reclassification Map No. 11-J at 4634-4636 N Avers Ave - App No. 23124T1`.

**`zoning_median_days`** (per ward). Median of `finalActionDate − introductionDate` in
days, over the ward's **resolved, non-withdrawn** reclassifications (those with a real
`finalActionDate` whose `subStatus` does not contain "Withdrawn" — a withdrawal is not a
resolution and would enter the median as a misleading fast span). This is a **ward-scoped**
measure of how long rezonings take to clear the ward, not a personal attribute of the
sitting alder. It measures the **City Council phase only**: time an application spends
before introduction (ward office / planning-department review) is invisible to eLMS and
is not captured. Both caveats appear in the tooltip and in the always-visible metric
notes under the table.

**`zoning_matter_count`** (per ward). Number of reclassifications geocoded to the ward in
the term window. Displayed as a column: it is the denominator context for the other two —
wards with more rezoning activity naturally accumulate more stalled matters (stalled and
matter counts correlate at ≈0.79 in this data), so neither the median nor the stalled
count should be read without it.

**`zoning_stalled_count`** (per ward). Number of the ward's reclassifications with **no
final action more than 180 days after introduction**, as of the frozen `as-of` date (see
below), excluding withdrawn matters. The rule is deliberately **status-blind**: an earlier
version required the status string "In Committee", which silently excluded the dataset's
longest-pending matter (`O2023-0002795`, parked at "5-Council Consideration" for 1,100+
days). 180 days ≈ 3.6× the citywide median resolved span (50 days). The threshold is a
**proxy** for a stalled application, not an official designation, and the count is
monotonically nondecreasing as the as-of date advances — treat it as a floor.

**`as-of` date.** The stalled computation needs a "today". It is frozen into the generated
data file (`ZONING_DELAY_META.computed_at`), surfaced to the UI as
`ScorecardResponse.metrics_as_of`, and displayed under the table. `--as-of` is a required
flag so the vintage is always explicit. The current data was generated with
`--as-of 2026-08-02`.

**Bonus units** (Phase 2). Housing units enabled by **alder-initiated** proactive
upzonings since that alder's election. Sum of `units_delta` over registry items with
`kind == "upzone"`.

**Lost units** (Phase 2). Units removed by **alder-initiated** downzonings, plus units cut
from developments shrunk under alder pressure. Sum of `units_delta` over items with
`kind in {"downzone", "shrunk_development"}`. `units_delta` is always stored **positive**;
the `kind` decides the bucket.

**Attribution rule.** Units are credited/debited **only for alder-initiated actions**
(the alder is a sponsor / the action originates from the ward office) — *not* for
applicant-filed reclassifications that merely passed under aldermanic prerogative. This is
a deliberate, narrow definition.

---

## 2. Data lineage

| Metric field | Source API / input | Fetch script | Generated data file | Aggregation | Seeder | API field | Frontend |
|---|---|---|---|---|---|---|---|
| `zoning_median_days`, `zoning_matter_count`, `zoning_stalled_count` | eLMS `GET /matter` (list) + `/matter/{guid}` (detail) + geocoding | `backend/scripts/fetch_zoning_delay_data.py` | `backend/app/data/ward_zoning_delay_data.py` (`WARD_ZONING_DELAY`, `ZONING_DELAY_META`) | `backend/app/imports/sources/ward_metrics.py::build_ward_metric_values()` | `backend/scripts/import_scorecard_projects.py` → carrier project's `EntityStatusRecord.record_metadata` (+ `dashboard_config.metrics_as_of`) | `ScorecardEntityRow.metrics[key]` + `ScorecardResponse.metrics[]` + `ScorecardResponse.metrics_as_of` | `Scorecard/DesktopTable.tsx` + `MetricCell.tsx` + `MetricNotes.tsx` |
| `bonus_units`, `lost_units`, `mention_to_passage_days` | Curated news/ordinance research | (manual + Phase-2 agent workflow) | `backend/app/data/alder_units_registry.py` (`ALDER_UNITS_REGISTRY`) | `ward_metrics.py::aggregate_units_registry()` | same seeder path | same | same |
| `affordable_share_pct`, `affordability_rank_change` | Community Zillow survey CSVs archived in `docs/data/zillow-affordability/` | `backend/scripts/fetch_affordability_data.py` | `backend/app/data/ward_affordability_data.py` (`WARD_AFFORDABILITY`, `AFFORDABILITY_META`) | `ward_metrics.py::build_ward_metric_values()` | same seeder path (descriptors carry per-metric `as_of`/`source`) | same | same |

**Supporting artifacts:**
- `backend/app/data/chicago-wards.geojson` — the **post-2023 official ward map**
  (data-portal `p293-wvbd`, edit_date 2022-06-01, effective with the 2023 election),
  simplified with 1e-5° tolerance (~1 m; verified to change zero ward assignments over
  all cached points vs. full resolution). **History:** until 2026-08-02 this file was
  the superseded 2015–2023 map, which misattributed ~21.5% of matters; the replacement
  changed most wards' published numbers.
  `tests/test_zoning_delay.py::test_chicago_ward_polygons_match_post_2023_official_map`
  now pins six interior points that are assigned **different** wards by the two map
  vintages, so a wrong-vintage file cannot pass CI.
- `backend/app/data/zoning_geocode_cache.py` (`ZONING_GEOCODE_CACHE`) — committed address→lat/lon/ward cache (1,226 entries, 23 cached failures as `None`; some entries are stale keys from older parser versions and are harmless). Makes re-runs and CI need no geocoding key. The `ward` field in the cache is **output only** — ward assignment is recomputed from the cached coordinates on every run, so a ward-map update takes effect without re-geocoding.
- `backend/app/data/alder_zoning_candidates.py` (`ALDER_ZONING_CANDIDATES`) — **Phase-2 research seed only** (not used at runtime): alder-sponsored reclassifications keyed by normalized sponsor name (291 rows across 41 alders).
- `backend/app/imports/sources/zoning_delay.py` — network-free pure logic: `extract_address_from_title`, `assign_ward` (Shapely point-in-polygon over `chicago-wards.geojson`), `compute_ward_delay_stats`, `is_alder_sponsored`, `meters_to_ward_boundary`.
- `backend/app/imports/sources/ward_utils.py::parse_ward_number` — shared "Ward N" → int parser (also used by `import_adu_project_data.py`).

**Where values attach (design note).** Metric *descriptors* live on the group's
**position-0 ("carrier") project** `dashboard_config.metrics`; per-alder *values* live in
that same project's `EntityStatusRecord.record_metadata`. This mirrors the existing
`representative_title` convention and needs no schema change. `ScorecardService.get_scorecard`
reads the descriptors from the first project (in position order) that declares any, and
merges declared metric keys from record metadata (lowest-position project wins conflicts).
The existing 6/6 alignment score is **completely independent** — metrics are display-only.

---

## 3. Reproduction

All commands run from `backend/`. The canonical environment is the poetry env
(`poetry install`); a fresh checkout that only needs the tools can use any Python 3.12 with
the pinned `ruff`/`mypy`/`pytest`.

**Regenerate the delay data from scratch** (cold run ≈ 2,570 HTTP requests: ~57 list pages
+ 1,278 matter details + ~1,230 Nominatim geocodes; ~25–30 min, dominated by geocoding at
1 req/s):

```bash
# Optional: set GEOCODING_API_KEY in backend/.env to use Google instead of Nominatim.
python -m scripts.fetch_zoning_delay_data --as-of 2026-08-02
```

The script caches every eLMS page and matter detail under `backend/.elms_cache/`
(gitignored) and every geocode in the committed `zoning_geocode_cache.py`, so **re-runs
are near-instant and make no geocoding or matter-detail calls** (each run still issues
one eLMS meta request and one alder-roster request):

```bash
python -m scripts.fetch_zoning_delay_data --as-of 2026-08-02   # seconds, fully cached
git diff backend/app/data/ward_zoning_delay_data.py            # only the Generated timestamp should move on a clean re-run
```

Flags: `--as-of` is **required** (the vintage must be explicit). `--refresh-geocode`
retries cached geocode **failures only** — successes always come from the cache. A
transient geocoder outage (rate limit, 5xx) is never written to the cache as a permanent
failure; only a definitive "no result" or an out-of-Chicago hit is. `--force` writes even
if ward-assignment coverage falls below the 80% floor (it is currently 96.5%). If the
alder-roster fetch fails, the Phase-2 candidates file is left untouched rather than
truncated.

**Re-seed the scorecard** (idempotent by slug; safe to re-run):

```bash
python -m scripts.import_scorecard_projects
```

**Verify the numbers surface through the API** (needs the app running with the Chicago group
seeded):

```bash
curl -s localhost:8000/api/scorecard/strong-towns-chicago-chicago-city-council \
  | jq '.metrics, .entities[0].metrics'
```

### Expected figures for the committed data (as-of 2026-08-02)

- Target matters (ZONING RECLASSIFICATIONS since 2023-05-15): **1,278** (deduplicated by `matterId`)
- Ward-assignment coverage: **96.5%** (1,233 assigned / 45 unassigned; the 45 record numbers are listed in `ZONING_DELAY_META.unassigned_record_numbers`)
- Per-ward matter count: min **3**, median **18.5**, max **103**; **all 50 wards populated**, all 50 have a median
- Per-ward `n_resolved`: min **2**; 8 wards below 10 (small-N medians — see §5)
- Total stalled >180 days: **100**
- Withdrawn matters excluded from medians: **1** (`O2026-0022148`)
- Near-boundary points (<30 m from a ward line, reassignment-risk under the simplified polygon): **184 / 1,233 = 14.9%** (`ZONING_DELAY_META.near_boundary_count`)

> **Numbers changed on 2026-08-02** relative to the first published snapshot (as-of
> 2026-07-23): the ward map was corrected from the 2015–2023 vintage to the post-2023
> map (≈21.5% of points moved wards), the stalled rule became status-blind, withdrawn
> matters left the median, ~11 previously unparseable/ungeocodable addresses were
> recovered, and `--as-of` advanced. The underlying eLMS corpus was verified unchanged
> between the two dates via a live API sweep.

---

## 4. Auditor checklist

> **First stop: the in-app audit page.** `/scorecard/{group-slug}/audit` renders a
> ward choropleth plus every ward's underlying matter list (record numbers linked to
> eLMS, introduction/final-action dates, derived span, stalled/withdrawn/near-boundary
> flags) from the committed `backend/app/data/ward_zoning_matters.py`, served by
> `GET /api/scorecard/{group-slug}/zoning-audit`. Steps 1 and 6 below can be done
> entirely from that page; the CI test
> `tests/test_zoning_audit_service.py::TestCommittedDataReconciliation` additionally
> proves the per-matter records reproduce `WARD_ZONING_DELAY` bit-for-bit on every run.

1. **Re-derive one ward's median by hand.** Pick a ward, pull its resolved matters from the
   audit page (or `backend/.elms_cache/matters/*.json`), compute `finalActionDate − introductionDate`
   for each, take the median, and compare to `WARD_ZONING_DELAY[ward]["zoning_median_days"]`.
   Confirm withdrawn matters and negative spans are excluded. (Sentinel dates like
   `1900-01-01` are guarded against in code but have zero occurrences in the current
   corpus, so that guard cannot be exercised against real data.)
1a. **Verify the ward-map vintage.** The committed
   `backend/app/data/chicago-wards.geojson` must be the post-2023 map. Check a point the
   two vintages disagree on — e.g. 10805 S Halsted (41.6976, −87.6428) must assign to
   ward **21** (the 2015–2023 map says 34), and 333 S Desplaines (41.8776, −87.6444)
   must assign to ward **34** (the old map says 42). The unit test
   `test_chicago_ward_polygons_match_post_2023_official_map` pins six such points.
2. **Check coverage honesty.** Confirm `len(ZONING_DELAY_META["unassigned_record_numbers"])`
   equals `total_matters − assigned`, and that **no ward was assigned by guessing** — every
   unparseable/failed address is in the unassigned list, never dropped into a ward.
3. **Metadata preservation (load-bearing).** The whole feature depends on curated metadata
   surviving the admin refresh. Verify: call the refresh endpoint (or `import_scorecard_projects`)
   twice and diff the carrier project's `record_metadata` — it must be unchanged. This is
   enforced in `StatusService.create_status_record` (`None` = preserve, explicit `{}` = clear)
   and covered by `tests/test_status_service.py::TestCreateStatusRecordPreservesCuratedFields`.
   (Independently reproduced against real SQLite during implementation: three consecutive
   refreshes preserved both `record_metadata` and `notes`.)
4. **Score integrity.** Confirm the alignment score is untouched: the row's `aligned_count` /
   `total_scoreable` must match a pre-change production payload. `tests/test_scorecard_service.py::
   TestGetScorecardMetrics::test_scores_identical_with_and_without_metrics_config` asserts this.
5. **Registry citations (Phase 2).** For a sample of `ALDER_UNITS_REGISTRY` items, open each
   `citations` URL and confirm it supports the `units_delta` and the alder attribution.
   `tests/test_alder_units_registry.py` enforces the structural rules (see §6).
6. **Boundary exposure.** Spot-check a few of the 184 near-boundary record numbers against
   Chicago's official ward map; confirm any misassignment doesn't move a ward's *median*
   materially. Note this robustness argument only holds for wards with a healthy sample —
   8 wards have fewer than 10 resolved matters (minimum: 2), and their medians are
   individually fragile. The published `zoning_matter_count` column and the `n_resolved`
   field in the data file give the denominator.

---

## 5. Known limitations & judgment calls

- **Geocoding failures are never guessed.** 45 matters (3.5%) could not be confidently
  placed in a ward — hard geocode failures, out-of-Chicago rejects (e.g.
  "400 N Elizabeth Ave" resolving to Waukegan), and titles with no parseable address. They
  are excluded and listed, not distributed into wards.
- **First-address-only rule.** Titles listing multiple addresses are geocoded on the first
  address; address ranges (`4634-4636`) collapse to the first house number. Bare
  application-number suffixes (`- A-8863`, `- App 22194`) are stripped, and
  "Dr. Martin Luther King (Jr.) Dr" spellings are normalized to "King Dr" before
  geocoding — both classes previously caused ward-correlated coverage loss on the South
  Side.
- **Simplified ward polygons.** `backend/app/data/chicago-wards.geojson` is the post-2023
  official map (`p293-wvbd`), simplified at ~1 m tolerance (verified to flip zero
  assignments vs. full resolution over all cached points). **14.9% of points fall within
  30 m of a ward boundary** and could in principle reassign under the exact boundary.
  Acceptable for ward-level medians; fully auditable via `near_boundary_record_numbers`.
- **Stalled count is volume-confounded.** `zoning_stalled_count` is a raw count, and it
  correlates with the ward's rezoning volume (corr ≈ 0.79) — busy wards accumulate more
  stalled matters, and a ward that deters applications entirely shows zero. That is why
  `zoning_matter_count` is displayed alongside it and the tooltip says to read the two
  together. It is also monotonically nondecreasing as the as-of date ages: the published
  figure is a floor. (An earlier caveat here blamed re-referred/substituted ordinances
  for inflating the count; that mechanism is **not observable** in the eLMS list payload
  — substitute ordinances' originals do not appear in the sweep at all — so the caveat
  was retired as unsupported.)
- **Ward-scoped, not person-scoped.** Delay metrics describe the **ward** across the whole
  term. Where an alder changed mid-term, some of the ward's delay history predates the sitting
  alder. This is stated in each tooltip and in the always-visible metric notes rendered
  under the table (including the mobile layout). Unit metrics (Phase 2), by contrast, are
  per-alder and gated on each alder's `elected` date in the registry.
- **Refresh scope.** The admin scorecard refresh endpoint updates vote/sponsorship data
  only; the zoning columns are frozen at `metrics_as_of` until the fetch script is re-run
  and the seeder re-executed. The vintage is displayed so readers can see the difference.
- **Candidate-seed name-normalization gap (Phase 2 action item).** `ALDER_ZONING_CANDIDATES`
  keys sponsors by `normalize_name`. Four sponsor names matched no roster entry: two are
  non-persons ("Misc. Transmittal", "Dept./Agency", expected), but **two are real alders whose
  sponsored matters are currently dropped from the seed** — Carlos Ramirez-Rosa (Ward 35) and
  Walter Burnett Jr. (Ward 27). Reconcile these before the Phase-2 research relies on the seed,
  or their proactive rezonings will be missed. This affects only the research *seed*, not any
  shipped delay number.
- **"Shrunk development" scope.** Counts units removed from a specific project during
  negotiation/downsizing that is attributable to the alder; it does not attempt to model
  hypothetical "could-have-been" capacity.

---

## 6. Registry curation rules (Phase 2)

`ALDER_UNITS_REGISTRY` (in `backend/app/data/alder_units_registry.py`) is a **committed,
reviewed** list — the deliberate opposite of a scraped number. Each item:

```python
{ "ward": 1, "alder": "Daniel La Spata", "elected": "2019-05-20",
  "items": [
    { "name": "2354 N Milwaukee Ave upzone (B3-2 -> B2-5)",
      "kind": "upzone",              # upzone | downzone | shrunk_development
      "units_delta": 120,            # ALWAYS positive; kind decides the bucket
      "date": "2024-06-12",
      "elms_record_number": "O2024-0009123",   # optional cross-reference
      "first_public_date": "2023-11-02",       # optional (newsletter / community meeting)
      "citations": ["https://blockclubchicago.org/..."],  # REQUIRED, >= 1 http(s) URL
      "notes": "..." } ] }
```

Enforced by `backend/tests/test_alder_units_registry.py` (CI is the gatekeeper): ward ∈ 1–50,
no duplicate wards, valid `kind`, `units_delta > 0`, ISO dates, `first_public_date <= date`,
item `date >= elected`, `citations` non-empty and all `http(s)://`, `elms_record_number`
matches `^[A-Z]{1,2}\d{4}-\d+$` when present, and the alder resolves via `normalize_name`.

**Research workflow that populates it** (run separately; produces data, reviewed before commit):
per-alder agents sweep local coverage (Block Club, Crain's, Tribune/Sun-Times, ward newsletters)
since the alder's election for alder-initiated upzones/downzones/shrunk developments, extract
unit counts + dates + earliest public mention, and record **≥1 citation per item** — no
estimates; a number that can't be traced to a citation or ordinance text is omitted and noted.
A second **adversarial verification** agent re-fetches each citation and confirms the number
and attribution before the entry is merged. `ALDER_ZONING_CANDIDATES` seeds the search (subject
to the name-gap caveat in §5). After merge, flip `bonus_units`/`lost_units` to
`show_in_table=True` in `CHICAGO_WARD_METRICS` and re-run the seeder.

The operational protocol (agent workflow shape, merge tooling, coverage bar for the
`show_in_table` flip, pilot log) lives in `docs/alder-units-research-protocol.md`. Reviewed
research JSON is merged with `python -m scripts.merge_units_registry <research.json>`, which
validates against the same rules CI enforces (shared validators in
`app/imports/sources/alder_units_validation.py`) and refuses to write on any violation.

---

## 7. Community-collected Zillow affordability metrics

Two visible columns come from a **community-collected survey**, not an API:
**Affordable Listings (% at 60% AMI)** (`affordable_share_pct`) and
**Affordability Rank Change (2025→2026)** (`affordability_rank_change`).

**Provenance.** Collin Pearsall (Ward 1) hand-drew each of the 50 wards as a custom
search region in the Zillow web UI and recorded rental and for-sale listing data for
every ward — once in late July 2025 (7/25–27) and again in late July 2026 (7/25–28),
reusing the identical saved boundaries. The raw sheets, his original methodology
note, and an archive README live in `docs/data/zillow-affordability/`.

**Definitions.**

- **`affordable_share_pct`** (0–100). Of the ward's rental *and* for-sale listings
  with 0–5 bedrooms in the July 2026 survey, the share priced within the **ARO 60%
  AMI limit for their bedroom count** ([2026 limits](https://www.chicago.gov/content/dam/city/sites/affordable-requirements-ordinance/2026%20Income%20and%20Rent%20Limits%20-%20final.pdf);
  the 2025 survey used the [2025 limits](https://www.chicago.gov/content/dam/city/sites/affordable-requirements-ordinance/2025%20Income%20and%20Rent%20Limits.pdf)).
  Rentals compare monthly rent; for-sale listings compare **Zillow's estimated
  monthly payment with no money down and any credit score**, which folds in
  HOA/taxes and avoids price-only inconsistencies.
- **`affordability_rank_change`** (integer). How many places the ward moved in the
  50-ward ranking by affordable-listings share between the two surveys. **Positive =
  relatively more affordable.** Because it is a rank, citywide price shifts cancel
  out; only movement *relative to other wards* registers.

**Pipeline.** `python -m scripts.fetch_affordability_data` parses the archived CSVs
into `backend/app/data/ward_affordability_data.py`. The parser matches columns by
normalized header prefix, recomputes each share from the raw affordable/total counts
and fails if it disagrees with the sheet by more than 0.1 pp, requires all 50 wards
exactly once, and cross-checks the comparison sheet's rank change against the two
years' rank columns — column drift aborts the import rather than shipping a wrong
number. The metric descriptors carry their own `as_of` (2026-07-28) and `source`
attribution, rendered as a separate footnote line; the zoning metrics keep the
group-level `metrics_as_of`.

**Known limitations & judgment calls.**

- **Hand-drawn boundaries** closely approximate, but are not identical to, the
  official post-2023 ward map used by the zoning metrics.
- The ARO limits used assume **landlords pay utilities**; wards where tenants pay
  utilities (most areas outside downtown) look somewhat more affordable than they are.
- **Small samples.** Ward listing totals ranged from ~74 to ~1,512 in 2026; low-count
  wards' shares (and hence rank changes) are noisy. Citywide context:
  16.2% affordable (2025, n=19,462) → 16.8% (2026, n=21,312), in
  `AFFORDABILITY_META`.
- **One-week July snapshots**, not annual averages; medians were read manually from
  Zillow's price filters.
- Land/empty lots and room-only rentals were excluded; multifamily buildings were not.

**Auditor steps.** (1) Open the archived CSVs and spot-check a ward's combined
affordable/total counts against the generated module. (2) Re-run the fetch script —
only the `# Generated:` timestamp should change. (3) Confirm the scorecard column
for a ward equals the module's `affordable_share_pct`, e.g. Ward 4 = 19.68 → "19.7%".
