"""Tests for the zoning-audit service and its per-matter flag derivation."""

import statistics
from datetime import date
from unittest.mock import AsyncMock, MagicMock
from uuid import uuid4

import pytest

from app.data.ward_zoning_delay_data import WARD_ZONING_DELAY
from app.data.ward_zoning_matters import (
    UNASSIGNED_ZONING_MATTERS,
    WARD_ZONING_MATTERS,
)
from app.services.zoning_audit_service import ZoningAuditService, derive_matter_flags
from tests.factories import make_entity, make_project

AS_OF = date(2026, 8, 2)


def _matter(**overrides):
    base = {
        "record_number": "O2026-0000001",
        "matter_guid": "guid-1",
        "title": "Zoning Reclassification at 1 N Test St",
        "address": "1 N Test St",
        "introduction_date": "2026-01-21T00:00:00",
        "final_action_date": None,
        "status": "1-Introduced",
        "sub_status": None,
        "lat": 41.9,
        "lon": -87.7,
        "near_boundary": False,
    }
    base.update(overrides)
    return base


class TestDeriveMatterFlags:
    def test_resolved_matter_gets_span_and_no_pending_flags(self):
        row = derive_matter_flags(
            _matter(final_action_date="2026-03-21T00:00:00"), AS_OF
        )
        assert row.span_days == 59
        assert row.pending is False
        assert row.stalled is False
        assert row.withdrawn is False

    def test_pending_matter_older_than_threshold_is_stalled(self):
        row = derive_matter_flags(
            _matter(introduction_date="2025-06-01T00:00:00"), AS_OF
        )
        assert row.pending is True
        assert row.stalled is True

    def test_recent_pending_matter_is_not_stalled(self):
        row = derive_matter_flags(
            _matter(introduction_date="2026-06-01T00:00:00"), AS_OF
        )
        assert row.pending is True
        assert row.stalled is False

    def test_withdrawn_pending_matter_is_neither_pending_nor_stalled(self):
        row = derive_matter_flags(
            _matter(introduction_date="2024-01-01T00:00:00", sub_status="Withdrawn"),
            AS_OF,
        )
        assert row.withdrawn is True
        assert row.pending is False
        assert row.stalled is False

    def test_withdrawn_resolved_matter_keeps_span_but_is_flagged(self):
        # The span is shown for audit transparency; the withdrawn flag tells
        # the reader it was excluded from the median.
        row = derive_matter_flags(
            _matter(final_action_date="2026-01-21T00:00:00", sub_status="Withdrawn"),
            AS_OF,
        )
        assert row.span_days == 0
        assert row.withdrawn is True

    def test_sentinel_introduction_date_yields_no_span_or_stall(self):
        row = derive_matter_flags(
            _matter(
                introduction_date="1899-12-30T00:00:00",
                final_action_date="2026-03-21T00:00:00",
            ),
            AS_OF,
        )
        assert row.span_days is None
        assert row.stalled is False

    def test_negative_span_is_dropped(self):
        row = derive_matter_flags(
            _matter(final_action_date="2025-12-01T00:00:00"), AS_OF
        )
        assert row.span_days is None


@pytest.mark.skipif(not WARD_ZONING_MATTERS, reason="matters module not generated")
class TestCommittedDataReconciliation:
    """The committed per-matter records must reproduce WARD_ZONING_DELAY exactly.

    This is the audit page's core guarantee: aggregating the drill-down rows
    with the derived flags yields the very numbers the scorecard displays.
    """

    def test_every_ward_reconciles_bit_for_bit(self):
        for ward, stats in WARD_ZONING_DELAY.items():
            rows = [
                derive_matter_flags(m, AS_OF) for m in WARD_ZONING_MATTERS.get(ward, [])
            ]
            spans = [
                r.span_days for r in rows if r.span_days is not None and not r.withdrawn
            ]
            median = round(float(statistics.median(spans)), 1) if spans else None
            assert median == stats["zoning_median_days"], f"ward {ward} median"
            assert len(rows) == stats["zoning_matter_count"], f"ward {ward} count"
            assert sum(r.stalled for r in rows) == stats["zoning_stalled_count"], (
                f"ward {ward} stalled"
            )
            assert len(spans) == stats["n_resolved"], f"ward {ward} n_resolved"
            assert sum(r.pending for r in rows) == stats["n_pending"], (
                f"ward {ward} n_pending"
            )

    def test_totals_match_meta(self):
        from app.data.ward_zoning_delay_data import ZONING_DELAY_META

        assigned = sum(len(v) for v in WARD_ZONING_MATTERS.values())
        assert (
            assigned + len(UNASSIGNED_ZONING_MATTERS)
            == (ZONING_DELAY_META["total_matters"])
        )
        near = sum(
            1 for v in WARD_ZONING_MATTERS.values() for m in v if m["near_boundary"]
        )
        assert near == ZONING_DELAY_META["near_boundary_count"]


def _service(projects, entities, districts=None):
    projects_provider = MagicMock()
    projects_provider.filter_multiple = AsyncMock(return_value=projects)
    entities_provider = MagicMock()
    entities_provider.filter = AsyncMock(return_value=entities)
    districts_provider = MagicMock()
    districts_provider.filter_in = AsyncMock(return_value=districts or [])
    return ZoningAuditService(
        projects_provider=projects_provider,
        entities_provider=entities_provider,
        districts_provider=districts_provider,
    )


class TestGetZoningAudit:
    @pytest.mark.asyncio
    async def test_group_without_projects_returns_none(self):
        service = _service(projects=[], entities=[])
        assert await service.get_zoning_audit(uuid4(), "Empty Group") is None

    @pytest.mark.asyncio
    async def test_group_without_ward_entities_returns_none(self):
        # An IL-House-style group: entities exist but no "Ward N" districts.
        project = make_project(slug="test", jurisdiction_id=uuid4())
        entity = make_entity(name="Rep. Example")
        entity.district_name = "District 12"
        service = _service(projects=[project], entities=[entity])
        assert await service.get_zoning_audit(uuid4(), "IL House") is None

    @pytest.mark.asyncio
    async def test_builds_all_fifty_wards_with_alder_names(self):
        jurisdiction_id = uuid4()
        project = make_project(slug="test", jurisdiction_id=jurisdiction_id)
        entity = make_entity(
            name="Quezada, Anthony J.", jurisdiction_id=jurisdiction_id
        )
        entity.district_name = "Ward 35"
        service = _service(projects=[project], entities=[entity])

        audit = await service.get_zoning_audit(uuid4(), "AHIL")

        assert audit is not None
        assert audit.jurisdiction_id == jurisdiction_id
        assert len(audit.wards) == 50
        ward35 = next(w for w in audit.wards if w.ward == 35)
        assert ward35.alder_name == "Quezada, Anthony J."
        # Aggregates come straight from the committed WARD_ZONING_DELAY.
        if WARD_ZONING_DELAY:
            assert (
                ward35.zoning_median_days
                == (WARD_ZONING_DELAY[35]["zoning_median_days"])
            )
            assert len(ward35.matters) == ward35.zoning_matter_count
