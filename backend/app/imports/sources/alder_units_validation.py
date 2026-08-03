"""Shared validation for the curated alder units registry.

Single source of truth for the curation rules documented in
``app/data/alder_units_registry.py``. Used by both the CI gatekeeper test
(``tests/test_alder_units_registry.py``) and the merge script
(``scripts/merge_units_registry.py``), so research output is held to exactly
the rules CI enforces — a registry that merges cleanly cannot then fail CI.

Validators return a list of human-readable error strings (empty == valid)
instead of raising, so callers can report every problem in one pass.
"""

from __future__ import annotations

import re
from datetime import date
from typing import Any

from app.imports.sources.chicago_city_clerk_elms import normalize_name

VALID_KINDS = {"upzone", "downzone", "shrunk_development"}
RECORD_NUMBER_RE = re.compile(r"^[A-Z]{1,2}\d{4}-\d+$")

# The registry is a curated, reviewed file — unknown keys are rejected so
# research-side annotations (verification verdicts, attribution rationale)
# can't leak into the committed module.
ENTRY_KEYS = {"ward", "alder", "elected", "items"}
ITEM_REQUIRED_KEYS = {"name", "kind", "units_delta", "date", "citations"}
ITEM_OPTIONAL_KEYS = {"elms_record_number", "first_public_date", "notes"}
ITEM_KEYS = ITEM_REQUIRED_KEYS | ITEM_OPTIONAL_KEYS


def _iso(value: Any) -> date | None:
    try:
        return date.fromisoformat(value)
    except (TypeError, ValueError):
        return None


def validate_entry(
    entry: dict[str, Any], known_alders: set[str] | None = None
) -> list[str]:
    """Validate one ward entry; returns error strings (empty == valid)."""
    errors: list[str] = []
    label = f"ward {entry.get('ward', '?')} ({entry.get('alder', '?')})"

    unknown = set(entry) - ENTRY_KEYS
    if unknown:
        errors.append(f"{label}: unknown entry keys {sorted(unknown)}")

    ward = entry.get("ward")
    if not isinstance(ward, int) or isinstance(ward, bool) or not 1 <= ward <= 50:
        errors.append(f"{label}: ward must be an int in 1..50, got {ward!r}")

    elected = _iso(entry.get("elected"))
    if elected is None:
        errors.append(
            f"{label}: elected must be an ISO date, got {entry.get('elected')!r}"
        )

    alder = entry.get("alder")
    if not isinstance(alder, str) or not alder.strip():
        errors.append(f"{label}: alder must be a non-empty string")
    elif known_alders and normalize_name(alder) not in known_alders:
        errors.append(f"{label}: alder {alder!r} does not resolve to a known alder")

    items = entry.get("items")
    if not items:
        errors.append(f"{label}: entry must have at least one item")
        return errors

    for i, item in enumerate(items):
        errors.extend(_validate_item(item, elected, f"{label} item {i}"))
    return errors


def _validate_item(item: dict[str, Any], elected: date | None, label: str) -> list[str]:
    errors: list[str] = []
    label = f"{label} ({item.get('name', '?')})"

    unknown = set(item) - ITEM_KEYS
    if unknown:
        errors.append(f"{label}: unknown item keys {sorted(unknown)}")
    missing = ITEM_REQUIRED_KEYS - set(item)
    if missing:
        errors.append(f"{label}: missing required keys {sorted(missing)}")

    if item.get("kind") not in VALID_KINDS:
        errors.append(f"{label}: invalid kind {item.get('kind')!r}")

    delta = item.get("units_delta")
    if not isinstance(delta, int) or isinstance(delta, bool) or delta <= 0:
        errors.append(f"{label}: units_delta must be a positive int, got {delta!r}")

    item_date = _iso(item.get("date"))
    if item_date is None:
        errors.append(f"{label}: date must be an ISO date, got {item.get('date')!r}")
    elif elected is not None and item_date < elected:
        errors.append(
            f"{label}: item date {item_date} precedes alder election {elected}"
        )

    first_public = item.get("first_public_date")
    if first_public is not None:
        first_public_date = _iso(first_public)
        if first_public_date is None:
            errors.append(
                f"{label}: first_public_date must be an ISO date, got {first_public!r}"
            )
        elif item_date is not None and first_public_date > item_date:
            errors.append(f"{label}: first_public_date must be on or before date")

    record_number = item.get("elms_record_number")
    if record_number is not None and (
        not isinstance(record_number, str) or not RECORD_NUMBER_RE.match(record_number)
    ):
        errors.append(f"{label}: bad record number {record_number!r}")

    citations = item.get("citations")
    if not citations or not isinstance(citations, list):
        errors.append(f"{label}: each item requires at least one citation")
    else:
        for url in citations:
            if not isinstance(url, str) or not url.startswith(("http://", "https://")):
                errors.append(f"{label}: citation must be an http(s) URL, got {url!r}")
    return errors


def validate_registry(
    registry: list[dict[str, Any]], known_alders: set[str] | None = None
) -> list[str]:
    """Validate the whole registry, including cross-entry rules."""
    errors: list[str] = []
    wards = [entry.get("ward") for entry in registry]
    duplicates = sorted({w for w in wards if wards.count(w) > 1}, key=repr)
    if duplicates:
        errors.append(f"duplicate ward entries in registry: {duplicates}")
    for entry in registry:
        errors.extend(validate_entry(entry, known_alders))
    return errors
