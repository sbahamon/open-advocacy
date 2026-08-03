# Zillow Ward Affordability Survey (community-collected)

Hand-collected Zillow listing data for all 50 Chicago wards, gathered by **Collin
Pearsall** (Ward 1 resident and volunteer). Collin hand-drew each ward as a custom
search area in the Zillow web interface (Zillow persists these shapes in the URL,
so the identical boundaries were reused across years) and recorded rental and
for-sale listing counts, medians, and affordability breakdowns by bedroom count.

## Files

| File | Contents |
|---|---|
| `zillow-affordability-2025.csv` | Full per-ward survey, collected 2025-07-25 → 2025-07-27 |
| `zillow-affordability-2026.csv` | Full per-ward survey, collected 2026-07-25 → 2026-07-28 |
| `zillow-affordability-2025-vs-2026.csv` | Year-over-year comparison: listing counts, medians, affordable totals, rank changes |
| `provenance-slack-note.png` | Collin's original note explaining the collection method |

## Method (summary — see the provenance note and methodology doc for detail)

- Affordability is measured against the **ARO 60% AMI rent limits per bedroom
  count** (0–5 br), from the City's published Income and Rent Limits tables
  ([2025](https://www.chicago.gov/content/dam/city/sites/affordable-requirements-ordinance/2025%20Income%20and%20Rent%20Limits.pdf),
  [2026](https://www.chicago.gov/content/dam/city/sites/affordable-requirements-ordinance/2026%20Income%20and%20Rent%20Limits%20-%20final.pdf)).
- For-sale affordability uses Zillow's **estimated monthly payment with no money
  down and any credit score**, which folds in HOA/taxes and avoids
  price-only inconsistencies.
- Medians were determined manually using Zillow's price filters.
- Land/empty lots and room-only rentals were excluded; multifamily buildings were
  not excluded.

## Known caveats

- **Hand-drawn boundaries** approximate — but are not identical to — the official
  [2023 ward map](https://data.cityofchicago.org/Facilities-Geographic-Boundaries/Boundaries-Wards-2023-Map/cdf7-bgn3).
- The rent limits used assume **landlords pay utilities**, which makes areas where
  they don't (i.e. most non-downtown areas) look somewhat more affordable than
  they are.
- **Small samples**: ward listing counts range from tens to ~1,500; small wards'
  percentages are noisy.
- Each survey is a **one-week July snapshot**, not an annual average.

## How this feeds the app

`python -m scripts.fetch_affordability_data` (from `backend/`) parses these CSVs
and regenerates the committed module
`backend/app/data/ward_affordability_data.py`, which
`app/imports/sources/ward_metrics.py` merges into the scorecard ward metrics.
See `docs/scorecard-metrics-methodology.md` §7 for definitions and audit steps.
