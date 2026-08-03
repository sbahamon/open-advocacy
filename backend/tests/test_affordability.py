"""Tests for the Zillow affordability CSV parser and module writer."""

import pytest

from app.imports.sources.affordability import (
    AffordabilityParseError,
    build_ward_affordability,
    parse_comparison_csv,
    parse_year_csv,
)
from scripts.fetch_affordability_data import write_affordability_module

# ---------------------------------------------------------------------------
# Fixture builders — compact synthetic sheets with the real headers' shapes,
# including decoy columns whose prefixes are close to the ones we match.
# ---------------------------------------------------------------------------

YEAR_HEADER = [
    "Neighborhood names",
    "Ward",
    "Median monthly rent",
    "Median for sale price",
    # Decoys: rental-only / 100%-AMI variants that must NOT match.
    "Total rental listings affordable at 60% AMI based on 2026 ARO rent limit",
    "% of listings for rent and for sale that are affordable at 100% of 2024 AMI",
    "Total rental and for sale listings affordable at 60% AMI based on 2026 ARO rent limit ($1276 for studio)",
    "Total rental and for sale listings with 0-5 bedrooms",
    "% of rental and for sale listings affordable at 60% AMI based on 2026 ARO rent limit ($1276 for studio)",
    "Affordability rank - % of rental and for sale listings affordable at 60% of AMI based on 2026 ARO rent limit",
]


def year_row(
    ward: int,
    affordable: int = 5,
    total: int = 100,
    share: str = "5.00%",
    rank: int | None = None,
    rent: str = "1,500",
) -> list[str]:
    return [
        f"Area {ward}",
        str(ward),
        rent,
        "300,000",
        "9",
        "1.00%",
        str(affordable),
        str(total),
        share,
        str(rank if rank is not None else ward),
    ]


def year_csv(rows: list[list[str]] | None = None) -> str:
    if rows is None:
        rows = [year_row(w) for w in range(1, 51)]
    citywide = [
        "Chicago",
        "-",
        "2,200",
        "375,000",
        "99",
        "9.99%",
        "500",
        "10000",
        "5.00%",
        "",
    ]
    lines = [",".join(f'"{c}"' for c in row) for row in [YEAR_HEADER, *rows, citywide]]
    return "\n".join(lines)


def comparison_csv(changes: dict[int, int] | None = None) -> str:
    header = [
        "Neighborhood names",
        "Ward",
        "Change in affordability rank for % of rental and for sale listings affordable at 60% AMI (July 2025 to July 2026)",
    ]
    rows = [[f"Area {w}", str(w), str((changes or {}).get(w, 0))] for w in range(1, 51)]
    citywide = ["Chicago", "-", ""]
    return "\n".join(",".join(row) for row in [header, *rows, citywide])


# ---------------------------------------------------------------------------
# parse_year_csv
# ---------------------------------------------------------------------------


class TestParseYearCsv:
    def test_parses_values_and_citywide(self):
        wards, citywide = parse_year_csv(year_csv(), 2026)
        assert set(wards) == set(range(1, 51))
        assert wards[1]["neighborhoods"] == "Area 1"
        assert wards[1]["median_rent"] == 1500  # comma-thousands stripped
        assert wards[1]["affordable_share_pct"] == 5.0  # % suffix stripped
        assert wards[1]["affordability_rank"] == 1
        assert citywide["total_listings"] == 10000

    def test_decoy_columns_do_not_shadow_the_combined_columns(self):
        wards, _ = parse_year_csv(year_csv(), 2026)
        # The combined column (value 5) is used, not the rental-only decoy (value 9).
        assert wards[2]["affordable_listings"] == 5

    def test_missing_ward_rejected(self):
        rows = [year_row(w) for w in range(1, 50)]  # ward 50 missing
        with pytest.raises(AffordabilityParseError, match=r"Missing wards: \[50\]"):
            parse_year_csv(year_csv(rows), 2026)

    def test_duplicate_ward_rejected(self):
        rows = [year_row(w) for w in range(1, 51)] + [year_row(7)]
        with pytest.raises(AffordabilityParseError, match="Duplicate ward 7"):
            parse_year_csv(year_csv(rows), 2026)

    def test_share_count_disagreement_rejected(self):
        rows = [year_row(w) for w in range(1, 51)]
        rows[0] = year_row(1, affordable=5, total=100, share="7.00%")
        with pytest.raises(AffordabilityParseError, match="disagrees"):
            parse_year_csv(year_csv(rows), 2026)

    def test_non_numeric_cell_rejected(self):
        rows = [year_row(w) for w in range(1, 51)]
        rows[3] = year_row(4, rent="soon™")
        with pytest.raises(AffordabilityParseError, match="Expected a number"):
            parse_year_csv(year_csv(rows), 2026)

    def test_div_zero_cell_parses_as_missing(self):
        rows = [year_row(w) for w in range(1, 51)]
        rows[3] = year_row(4, rent="#DIV/0!")
        wards, _ = parse_year_csv(year_csv(rows), 2026)
        assert wards[4]["median_rent"] is None

    def test_ambiguous_header_rejected(self):
        text = year_csv().replace(
            "Median for sale price", "Median monthly rent", 1
        )  # now two "Median monthly rent" columns
        with pytest.raises(AffordabilityParseError, match="exactly one column"):
            parse_year_csv(text, 2026)


# ---------------------------------------------------------------------------
# build_ward_affordability
# ---------------------------------------------------------------------------


class TestBuildWardAffordability:
    def test_merges_years_and_rank_change(self):
        csv_2025 = year_csv([year_row(w, rank=51 - w) for w in range(1, 51)])
        csv_2026 = year_csv()  # rank == ward
        changes = {w: (51 - w) - w for w in range(1, 51)}
        merged, citywide = build_ward_affordability(
            csv_2025, csv_2026, comparison_csv(changes)
        )
        assert merged[1]["affordability_rank_change"] == 49
        assert merged[1]["affordability_rank_2025"] == 50
        assert merged[1]["affordability_rank_2026"] == 1
        assert citywide["citywide_affordable_share_pct_2026"] == 5.0

    def test_comparison_sheet_disagreement_rejected(self):
        csv_both = year_csv()
        with pytest.raises(AffordabilityParseError, match="rank change"):
            build_ward_affordability(csv_both, csv_both, comparison_csv({1: 3}))


# ---------------------------------------------------------------------------
# parse_comparison_csv
# ---------------------------------------------------------------------------


def test_comparison_requires_integer_changes():
    text = comparison_csv().replace("Area 2,2,0", "Area 2,2,1.5")
    with pytest.raises(AffordabilityParseError, match="not an integer"):
        parse_comparison_csv(text)


# ---------------------------------------------------------------------------
# write_affordability_module round-trip
# ---------------------------------------------------------------------------


def test_write_affordability_module_round_trips(tmp_path):
    wards: dict[int, dict[str, float | int | str | None]] = {
        1: {
            "neighborhoods": "Wicker Park, Logan Square",
            "affordable_share_pct": 1.16,
            "affordability_rank_change": 2,
            "median_rent_2026": None,
        }
    }
    meta = {"as_of": "2026-07-28", "source": "test"}
    out = tmp_path / "ward_affordability_data.py"
    write_affordability_module(wards, meta, path=out)

    namespace: dict = {}
    exec(out.read_text(), namespace)  # noqa: S102 - importing our own generated file
    assert namespace["WARD_AFFORDABILITY"] == wards
    assert namespace["AFFORDABILITY_META"] == meta
    assert "# as-of: 2026-07-28" in out.read_text()
