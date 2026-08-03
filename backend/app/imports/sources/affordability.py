"""Parse the community-collected Zillow ward affordability CSVs.

The CSVs (archived under ``docs/data/zillow-affordability/``) were hand-collected
by Collin Pearsall using hand-drawn ward boundaries in the Zillow web UI — one
full survey in late July 2025, one in late July 2026, plus a comparison sheet.
Affordability is measured against the ARO 60% AMI rent limits per bedroom count;
for-sale listings use Zillow's estimated monthly payment (no money down, any
credit score).

Headers are matched by normalized prefix, not exact string — the sheets carry
year-specific limits (and the odd typo) inside the header text. Every matched
column must be unique, every ward 1–50 must be present exactly once, and the
combined affordability share is recomputed from the raw counts and cross-checked
against the sheet's own percentage, so silent column drift fails loudly instead
of importing wrong numbers.
"""

from __future__ import annotations

import csv
import io

WARD_COUNT = 50

# Recomputed share must agree with the sheet's percentage to this many
# percentage points; anything bigger means we grabbed the wrong column.
SHARE_TOLERANCE_PP = 0.1

_MISSING_CELL_VALUES = {"", "-", "n/a", "#div/0!"}


class AffordabilityParseError(ValueError):
    """The CSVs do not match the expected shape — refuse to import."""


def _normalize(text: str) -> str:
    return " ".join(text.lower().split())


def _parse_number(text: str, *, context: str) -> float | int | None:
    cell = text.strip()
    if _normalize(cell) in _MISSING_CELL_VALUES:
        return None
    cleaned = cell.rstrip("%").replace(",", "").replace("$", "")
    try:
        value = float(cleaned)
    except ValueError as exc:
        raise AffordabilityParseError(
            f"Expected a number in {context}, got {cell!r}"
        ) from exc
    return int(value) if value.is_integer() else value


def _find_column(header: list[str], prefix: str, *, exact: bool = False) -> int:
    normalized_prefix = _normalize(prefix)
    matches = [
        i
        for i, name in enumerate(header)
        if (
            _normalize(name) == normalized_prefix
            if exact
            else _normalize(name).startswith(normalized_prefix)
        )
    ]
    if len(matches) != 1:
        raise AffordabilityParseError(
            f"Expected exactly one column matching {prefix!r}, found {len(matches)}"
        )
    return matches[0]


# Logical field -> (header prefix, exact?) for the two per-year survey sheets.
# The combined rental+for-sale columns are the ones the scorecard uses; the
# per-bedroom breakdown columns are intentionally not imported.
_YEAR_FIELDS: dict[str, tuple[str, bool]] = {
    "neighborhoods": ("Neighborhood names", True),
    "median_rent": ("Median monthly rent", True),
    "median_sale_price": ("Median for sale price", True),
    "affordable_listings": (
        "Total rental and for sale listings affordable at 60% AMI",
        False,
    ),
    "total_listings": ("Total rental and for sale listings with 0-5 bedrooms", False),
    "affordable_share_pct": (
        "% of rental and for sale listings affordable at 60% AMI",
        False,
    ),
    "affordability_rank": (
        "Affordability rank - % of rental and for sale listings affordable at 60% of AMI",
        False,
    ),
}

_RANK_CHANGE_PREFIX = "Change in affordability rank"


def _read_rows(text: str) -> tuple[list[str], list[list[str]]]:
    rows = list(csv.reader(io.StringIO(text)))
    if len(rows) < 2:
        raise AffordabilityParseError("CSV has no data rows")
    return rows[0], rows[1:]


def _split_ward_rows(
    rows: list[list[str]], ward_column: int
) -> tuple[dict[int, list[str]], list[str] | None]:
    """Split data rows into per-ward rows and the citywide ('-') summary row."""
    ward_rows: dict[int, list[str]] = {}
    citywide: list[str] | None = None
    for row in rows:
        cell = row[ward_column].strip()
        if cell.isdigit():
            ward = int(cell)
            if ward in ward_rows:
                raise AffordabilityParseError(f"Duplicate ward {ward}")
            ward_rows[ward] = row
        elif cell == "-":
            citywide = row
        elif cell:
            raise AffordabilityParseError(f"Unexpected ward cell {cell!r}")
    if set(ward_rows) != set(range(1, WARD_COUNT + 1)):
        missing = sorted(set(range(1, WARD_COUNT + 1)) - set(ward_rows))
        raise AffordabilityParseError(f"Missing wards: {missing}")
    return ward_rows, citywide


def _extract_fields(
    row: list[str], columns: dict[str, int], *, context: str
) -> dict[str, float | int | str | None]:
    values: dict[str, float | int | str | None] = {}
    for field, index in columns.items():
        if field == "neighborhoods":
            values[field] = row[index].strip()
        else:
            values[field] = _parse_number(row[index], context=f"{context} {field}")
    return values


def parse_year_csv(
    text: str, year: int
) -> tuple[
    dict[int, dict[str, float | int | str | None]], dict[str, float | int | str | None]
]:
    """Parse one per-year survey sheet.

    Returns (per-ward values, citywide summary values). Raises
    AffordabilityParseError on any shape or cross-check violation.
    """
    header, rows = _read_rows(text)
    ward_column = _find_column(header, "Ward", exact=True)
    columns = {
        field: _find_column(header, prefix, exact=exact)
        for field, (prefix, exact) in _YEAR_FIELDS.items()
    }

    ward_rows, citywide_row = _split_ward_rows(rows, ward_column)
    wards: dict[int, dict[str, float | int | str | None]] = {}
    for ward in sorted(ward_rows):
        values = _extract_fields(
            ward_rows[ward], columns, context=f"{year} ward {ward}"
        )
        _check_share(values, context=f"{year} ward {ward}")
        rank = values["affordability_rank"]
        if not isinstance(rank, int) or not 1 <= rank <= WARD_COUNT:
            raise AffordabilityParseError(
                f"{year} ward {ward}: affordability_rank {rank!r} not in 1..{WARD_COUNT}"
            )
        wards[ward] = values

    if citywide_row is None:
        raise AffordabilityParseError(f"{year}: citywide summary row missing")
    citywide_columns = {
        field: index
        for field, index in columns.items()
        if field != "affordability_rank"
    }
    citywide = _extract_fields(
        citywide_row, citywide_columns, context=f"{year} citywide"
    )
    _check_share(citywide, context=f"{year} citywide")
    return wards, citywide


def _check_share(values: dict[str, float | int | str | None], *, context: str) -> None:
    affordable = values["affordable_listings"]
    total = values["total_listings"]
    share = values["affordable_share_pct"]
    if not isinstance(affordable, int) or not isinstance(total, int) or total <= 0:
        raise AffordabilityParseError(
            f"{context}: bad listing counts {affordable!r}/{total!r}"
        )
    if not isinstance(share, (int, float)):
        raise AffordabilityParseError(f"{context}: missing affordability share")
    recomputed = affordable / total * 100
    if abs(recomputed - float(share)) > SHARE_TOLERANCE_PP:
        raise AffordabilityParseError(
            f"{context}: share {share} disagrees with {affordable}/{total} "
            f"(recomputed {recomputed:.2f})"
        )


def parse_comparison_csv(text: str) -> dict[int, int]:
    """Parse the 2025-vs-2026 sheet: ward -> affordability rank change."""
    header, rows = _read_rows(text)
    ward_column = _find_column(header, "Ward", exact=True)
    change_column = _find_column(header, _RANK_CHANGE_PREFIX)
    ward_rows, _ = _split_ward_rows(rows, ward_column)
    changes: dict[int, int] = {}
    for ward in sorted(ward_rows):
        value = _parse_number(
            ward_rows[ward][change_column],
            context=f"comparison ward {ward} rank change",
        )
        if not isinstance(value, int):
            raise AffordabilityParseError(
                f"comparison ward {ward}: rank change {value!r} is not an integer"
            )
        changes[ward] = value
    return changes


def build_ward_affordability(
    csv_2025: str, csv_2026: str, csv_comparison: str
) -> tuple[
    dict[int, dict[str, float | int | str | None]], dict[str, float | int | str | None]
]:
    """Merge the three sheets into the committed per-ward payload + citywide meta.

    The display keys are ``affordable_share_pct`` (2026 combined share, 0-100)
    and ``affordability_rank_change`` (positive = ward became relatively more
    affordable). The rank change is cross-checked against the two years' rank
    columns, so the comparison sheet cannot silently diverge from the surveys.
    """
    wards_2025, citywide_2025 = parse_year_csv(csv_2025, 2025)
    wards_2026, citywide_2026 = parse_year_csv(csv_2026, 2026)
    rank_changes = parse_comparison_csv(csv_comparison)

    merged: dict[int, dict[str, float | int | str | None]] = {}
    for ward in sorted(wards_2026):
        year_2025 = wards_2025[ward]
        year_2026 = wards_2026[ward]
        rank_2025 = year_2025["affordability_rank"]
        rank_2026 = year_2026["affordability_rank"]
        assert isinstance(rank_2025, int) and isinstance(rank_2026, int)
        expected_change = rank_2025 - rank_2026
        if rank_changes[ward] != expected_change:
            raise AffordabilityParseError(
                f"ward {ward}: comparison rank change {rank_changes[ward]} != "
                f"{rank_2025} - {rank_2026}"
            )
        merged[ward] = {
            "neighborhoods": year_2026["neighborhoods"],
            "affordable_share_pct": year_2026["affordable_share_pct"],
            "affordability_rank_change": rank_changes[ward],
            "affordable_share_pct_2025": year_2025["affordable_share_pct"],
            "affordable_listings_2025": year_2025["affordable_listings"],
            "affordable_listings_2026": year_2026["affordable_listings"],
            "total_listings_2025": year_2025["total_listings"],
            "total_listings_2026": year_2026["total_listings"],
            "affordability_rank_2025": rank_2025,
            "affordability_rank_2026": rank_2026,
            "median_rent_2025": year_2025["median_rent"],
            "median_rent_2026": year_2026["median_rent"],
            "median_sale_price_2025": year_2025["median_sale_price"],
            "median_sale_price_2026": year_2026["median_sale_price"],
        }

    citywide: dict[str, float | int | str | None] = {
        "citywide_affordable_share_pct_2025": citywide_2025["affordable_share_pct"],
        "citywide_affordable_share_pct_2026": citywide_2026["affordable_share_pct"],
        "citywide_total_listings_2025": citywide_2025["total_listings"],
        "citywide_total_listings_2026": citywide_2026["total_listings"],
    }
    return merged, citywide
