"""Tests for the shared registry validators and the merge script."""

import importlib.util
import shutil
from pathlib import Path

import pytest

from app.imports.sources.alder_units_validation import (
    validate_entry,
    validate_registry,
)
from scripts.merge_units_registry import (
    REGISTRY_PATH,
    clean_entry,
    merge_registry,
    write_registry_module,
)


def make_item(**overrides):
    item = {
        "name": "2354 N Milwaukee Ave upzone (B3-2 -> B2-5)",
        "kind": "upzone",
        "units_delta": 120,
        "date": "2024-06-12",
        "elms_record_number": "O2024-0009123",
        "first_public_date": "2023-11-02",
        "citations": ["https://blockclubchicago.org/story"],
        "notes": "example",
    }
    item.update(overrides)
    return item


def make_entry(**overrides):
    entry = {
        "ward": 21,
        "alder": "Ronnie Mosley",
        "elected": "2023-05-15",
        "items": [make_item()],
    }
    entry.update(overrides)
    return entry


# validate_entry


def test_valid_entry_passes():
    assert validate_entry(make_entry()) == []


def test_valid_entry_passes_roster_check():
    assert validate_entry(make_entry(), known_alders={"ronnie mosley"}) == []


def test_unknown_alder_fails_roster_check():
    errors = validate_entry(make_entry(), known_alders={"someone else"})
    assert any("does not resolve" in e for e in errors)


@pytest.mark.parametrize(
    "overrides,fragment",
    [
        ({"ward": 0}, "ward must be an int in 1..50"),
        ({"ward": 51}, "ward must be an int in 1..50"),
        ({"ward": "21"}, "ward must be an int in 1..50"),
        ({"elected": "not-a-date"}, "elected must be an ISO date"),
        ({"items": []}, "at least one item"),
        ({"alder": ""}, "non-empty string"),
        ({"extra": 1}, "unknown entry keys"),
    ],
)
def test_entry_rule_violations(overrides, fragment):
    errors = validate_entry(make_entry(**overrides))
    assert any(fragment in e for e in errors), errors


@pytest.mark.parametrize(
    "overrides,fragment",
    [
        ({"kind": "rezone"}, "invalid kind"),
        ({"units_delta": 0}, "positive int"),
        ({"units_delta": -5}, "positive int"),
        ({"units_delta": True}, "positive int"),
        ({"units_delta": 12.5}, "positive int"),
        ({"date": "2022-01-01"}, "precedes alder election"),
        ({"date": "junk"}, "date must be an ISO date"),
        ({"first_public_date": "2025-01-01"}, "on or before date"),
        ({"first_public_date": "junk"}, "first_public_date must be an ISO date"),
        ({"elms_record_number": "bad-format"}, "bad record number"),
        ({"citations": []}, "at least one citation"),
        ({"citations": ["ftp://x"]}, "http(s) URL"),
        ({"_verify": {}}, "unknown item keys"),
    ],
)
def test_item_rule_violations(overrides, fragment):
    errors = validate_entry(make_entry(items=[make_item(**overrides)]))
    assert any(fragment in e for e in errors), errors


def test_missing_required_item_key():
    item = make_item()
    del item["citations"]
    errors = validate_entry(make_entry(items=[item]))
    assert any("missing required keys" in e for e in errors)


def test_optional_item_keys_may_be_absent():
    item = make_item()
    del item["elms_record_number"]
    del item["first_public_date"]
    del item["notes"]
    assert validate_entry(make_entry(items=[item])) == []


# validate_registry


def test_duplicate_wards_rejected():
    errors = validate_registry([make_entry(), make_entry()])
    assert any("duplicate ward" in e for e in errors)


def test_registry_of_distinct_wards_passes():
    entries = [make_entry(), make_entry(ward=9, alder="Anthony Beale")]
    assert validate_registry(entries) == []


# clean_entry


def test_clean_entry_folds_rationale_and_drops_research_keys():
    entry = make_entry(elected_citation="https://ballotpedia.org/x")
    entry["items"] = [
        make_item(
            notes="base note",
            attribution_rationale="introduced the ordinance",
            _verify={"verdict": "confirmed"},
        )
    ]
    cleaned = clean_entry(entry)
    assert "elected_citation" not in cleaned
    item = cleaned["items"][0]
    assert "_verify" not in item
    assert "attribution_rationale" not in item
    assert item["notes"] == "base note Attribution: introduced the ordinance"
    assert validate_entry(cleaned) == []


def test_clean_entry_uses_rationale_as_notes_when_no_notes():
    entry = make_entry()
    item = make_item(attribution_rationale="demanded the downzone")
    del item["notes"]
    entry["items"] = [item]
    cleaned = clean_entry(entry)
    assert cleaned["items"][0]["notes"] == "Attribution: demanded the downzone"


def test_clean_entry_drops_none_optional_keys():
    entry = make_entry(
        items=[make_item(elms_record_number=None, first_public_date=None, notes=None)]
    )
    item = clean_entry(entry)["items"][0]
    assert "elms_record_number" not in item
    assert "first_public_date" not in item
    assert "notes" not in item
    assert validate_entry(clean_entry(entry)) == []


# merge_registry


def test_merge_into_empty_registry_sorts_by_ward():
    merged = merge_registry(
        [], [make_entry(ward=21), make_entry(ward=9, alder="Anthony Beale")]
    )
    assert [e["ward"] for e in merged] == [9, 21]


def test_merge_collision_errors_without_replace():
    with pytest.raises(ValueError, match="--replace"):
        merge_registry([make_entry()], [make_entry()])


def test_merge_collision_replaces_with_flag():
    updated = make_entry(items=[make_item(), make_item(name="second item")])
    merged = merge_registry([make_entry()], [updated], replace=True)
    assert len(merged) == 1
    assert len(merged[0]["items"]) == 2


# write_registry_module


def _import_registry(path: Path):
    spec = importlib.util.spec_from_file_location("registry_under_test", path)
    assert spec is not None and spec.loader is not None
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def test_write_registry_module_round_trips(tmp_path):
    out = tmp_path / "alder_units_registry.py"
    shutil.copy(REGISTRY_PATH, out)
    entries = [
        clean_entry(make_entry()),
        clean_entry(make_entry(ward=9, alder="Anthony Beale")),
    ]
    write_registry_module(entries, path=out)

    module = _import_registry(out)
    assert module.ALDER_UNITS_REGISTRY == entries
    # The reviewed schema docstring survives the rewrite.
    assert "Hard curation rules" in module.__doc__

    # Idempotent: writing the same entries again leaves the file unchanged.
    first = out.read_text(encoding="utf-8")
    write_registry_module(entries, path=out)
    assert out.read_text(encoding="utf-8") == first


def test_write_registry_module_requires_marker(tmp_path):
    out = tmp_path / "not_a_registry.py"
    out.write_text("x = 1\n", encoding="utf-8")
    with pytest.raises(ValueError, match="marker"):
        write_registry_module([], path=out)
