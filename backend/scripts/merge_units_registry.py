"""Merge reviewed research output into the curated alder units registry.

Takes a JSON file of researched ward entries (the output of the multi-agent
research workflow described in ``docs/alder-units-research-protocol.md``),
strips research-side annotations, validates against the exact rules CI
enforces (``app.imports.sources.alder_units_validation``), and rewrites
``app/data/alder_units_registry.py`` in place — preserving its schema
docstring. Nothing is written if any entry fails validation.

Research-only keys are handled explicitly: ``attribution_rationale`` is folded
into ``notes`` (it is part of the curation record), while transient keys such
as ``_verify`` and ``elected_citation`` are dropped with a log line.

Input JSON shape: a list of registry entries, e.g.::

    [{"ward": 21, "alder": "Ronnie Mosley", "elected": "2023-05-15",
      "items": [{"name": "...", "kind": "upzone", "units_delta": 120,
                 "date": "2024-06-12", "citations": ["https://..."]}]}]

Usage:
    python -m scripts.merge_units_registry research.json             # merge; error on ward collision
    python -m scripts.merge_units_registry research.json --replace   # replace colliding wards
    python -m scripts.merge_units_registry research.json --dry-run   # validate + report, no write
"""

from __future__ import annotations

import argparse
import json
import logging
import re
import subprocess
import sys
from pathlib import Path
from typing import Any

from app.data.alder_units_registry import ALDER_UNITS_REGISTRY
from app.imports.sources.alder_units_validation import validate_registry
from app.imports.sources.ward_metrics import aggregate_units_registry

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger("merge-units-registry")

REGISTRY_PATH = (
    Path(__file__).resolve().parent.parent / "app" / "data" / "alder_units_registry.py"
)
REGISTRY_MARKER = "ALDER_UNITS_REGISTRY: list[dict] ="

# Canonical key orders for the committed module (stable diffs).
_ENTRY_KEY_ORDER = ("ward", "alder", "elected", "items")
_ITEM_KEY_ORDER = (
    "name",
    "kind",
    "units_delta",
    "date",
    "elms_record_number",
    "first_public_date",
    "citations",
    "notes",
)


def _clean_item(item: dict[str, Any]) -> dict[str, Any]:
    """Keep schema keys in canonical order; fold rationale into notes."""
    cleaned = dict(item)
    rationale = cleaned.pop("attribution_rationale", None)
    if rationale:
        notes = cleaned.get("notes") or ""
        suffix = f"Attribution: {rationale}"
        cleaned["notes"] = f"{notes} {suffix}".strip() if notes else suffix

    dropped = [k for k in cleaned if k not in _ITEM_KEY_ORDER]
    for key in dropped:
        logger.info("Dropping research-only item key %r (%s)", key, item.get("name"))

    return {
        key: cleaned[key]
        for key in _ITEM_KEY_ORDER
        if key in cleaned and cleaned[key] is not None
    }


def clean_entry(entry: dict[str, Any]) -> dict[str, Any]:
    """Reduce a researched entry to the committed registry schema."""
    cleaned = {
        key: entry[key] for key in _ENTRY_KEY_ORDER if key in entry and key != "items"
    }
    dropped = [k for k in entry if k not in _ENTRY_KEY_ORDER]
    for key in dropped:
        logger.info(
            "Dropping research-only entry key %r (ward %s)", key, entry.get("ward")
        )
    cleaned["items"] = [_clean_item(item) for item in entry.get("items", [])]
    return cleaned


def merge_registry(
    existing: list[dict[str, Any]],
    new_entries: list[dict[str, Any]],
    replace: bool = False,
) -> list[dict[str, Any]]:
    """Merge new ward entries into the existing registry, sorted by ward.

    A ward present in both is an error unless ``replace`` is set (each ward
    has exactly one curated entry; partial item-level merges are done by
    editing the research JSON, not here).
    """
    merged = {entry["ward"]: entry for entry in existing}
    for entry in new_entries:
        ward = entry["ward"]
        if ward in merged and not replace:
            raise ValueError(
                f"ward {ward} already has a registry entry; rerun with --replace "
                "to overwrite it"
            )
        merged[ward] = entry
    return [merged[ward] for ward in sorted(merged)]


def _ruff_format(path: Path) -> None:
    """Best-effort `ruff format` on the written file so re-runs stay compliant."""
    try:
        subprocess.run(
            [sys.executable, "-m", "ruff", "format", str(path)],
            check=True,
            capture_output=True,
        )
    except (subprocess.CalledProcessError, FileNotFoundError) as exc:
        logger.warning("Could not ruff-format %s (%s); format it manually.", path, exc)


def write_registry_module(
    registry: list[dict[str, Any]], path: Path | None = None
) -> None:
    """Rewrite the registry module, preserving everything above the assignment.

    The schema docstring is the reviewed documentation of record — only the
    literal (and the comment line directly above it) is regenerated.
    """
    out_path = path if path is not None else REGISTRY_PATH
    source = out_path.read_text(encoding="utf-8")
    # Anchor to column 0: the schema example inside the module docstring
    # contains the same text, indented.
    match = re.search(f"^{re.escape(REGISTRY_MARKER)}", source, flags=re.MULTILINE)
    if match is None:
        raise ValueError(f"marker {REGISTRY_MARKER!r} not found in {out_path}")
    head = source[: match.start()]

    # Drop the stale comment block sitting directly above the assignment.
    head_lines = head.rstrip().splitlines()
    while head_lines and head_lines[-1].lstrip().startswith("#"):
        head_lines.pop()

    lines = [
        *head_lines,
        "",
        "# Curated via scripts/merge_units_registry.py from reviewed research",
        "# output; every item is citation-backed (see",
        "# docs/alder-units-research-protocol.md and methodology doc §6).",
        f"{REGISTRY_MARKER} {registry!r}",
        "",
    ]
    out_path.write_text("\n".join(lines), encoding="utf-8")
    _ruff_format(out_path)
    logger.info("Wrote %s", out_path)


def _known_alders() -> set[str]:
    try:
        from app.data.elms_scorecard_data import ELMS_SCORECARD_DATA
    except ImportError:  # pragma: no cover
        return set()
    return {name for lookup in ELMS_SCORECARD_DATA.values() for name in lookup}


def _report(registry: list[dict[str, Any]]) -> None:
    aggregates = aggregate_units_registry(registry)
    for entry in registry:
        ward = entry["ward"]
        values = aggregates.get(ward, {})
        logger.info(
            "ward %s (%s): %d items -> bonus_units=%s lost_units=%s "
            "mention_to_passage_days=%s",
            ward,
            entry["alder"],
            len(entry["items"]),
            values.get("bonus_units", 0),
            values.get("lost_units", 0),
            values.get("mention_to_passage_days", "n/a"),
        )


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("research_json", type=Path, help="researched entries (JSON)")
    parser.add_argument(
        "--replace", action="store_true", help="replace existing ward entries"
    )
    parser.add_argument(
        "--dry-run", action="store_true", help="validate and report without writing"
    )
    args = parser.parse_args()

    new_entries = [
        clean_entry(entry)
        for entry in json.loads(args.research_json.read_text(encoding="utf-8"))
    ]
    registry = merge_registry(ALDER_UNITS_REGISTRY, new_entries, replace=args.replace)

    errors = validate_registry(registry, known_alders=_known_alders())
    if errors:
        for error in errors:
            logger.error("%s", error)
        raise SystemExit(f"{len(errors)} validation error(s); nothing written")

    _report(registry)
    if args.dry_run:
        logger.info("Dry run: %d entries validated, nothing written", len(registry))
        return
    write_registry_module(registry)
    logger.info("Done. %d ward entries in registry.", len(registry))


if __name__ == "__main__":
    main()
