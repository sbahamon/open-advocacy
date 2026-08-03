"""Validation test for the curated alder units registry (the CI gatekeeper).

Passes trivially while ``ALDER_UNITS_REGISTRY`` is empty. Once the research
workflow appends entries, these checks enforce the curation rules documented
in ``app/data/alder_units_registry.py``. The rules themselves live in
``app.imports.sources.alder_units_validation`` — shared with
``scripts/merge_units_registry.py`` so a registry that merges cleanly cannot
then fail CI.
"""

import pytest

from app.data.alder_units_registry import ALDER_UNITS_REGISTRY
from app.imports.sources.alder_units_validation import (
    validate_entry,
    validate_registry,
)

# Known alders come from the same committed source the scorecard fetch uses.
# Empty registry never exercises this, but keep resolution honest when populated.
try:
    from app.data.elms_scorecard_data import ELMS_SCORECARD_DATA

    KNOWN_ALDER_NAMES = {
        name for lookup in ELMS_SCORECARD_DATA.values() for name in lookup
    }
except ImportError:  # pragma: no cover
    KNOWN_ALDER_NAMES = set()


def test_registry_is_valid_as_a_whole():
    errors = validate_registry(ALDER_UNITS_REGISTRY, known_alders=KNOWN_ALDER_NAMES)
    assert not errors, "\n".join(errors)


@pytest.mark.parametrize(
    "entry",
    ALDER_UNITS_REGISTRY,
    ids=[f"ward-{entry.get('ward')}" for entry in ALDER_UNITS_REGISTRY],
)
def test_registry_entry_is_valid(entry):
    errors = validate_entry(entry, known_alders=KNOWN_ALDER_NAMES)
    assert not errors, "\n".join(errors)
