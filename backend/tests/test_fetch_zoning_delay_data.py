"""Tests for scripts/fetch_zoning_delay_data.py helpers.

These cover the pure/near-pure pieces: the target-matter filter, the generated
data-module writer, and the Geocoder's cache semantics. The network sweep and
orchestration are exercised by regeneration runs, not unit tests.
"""

import runpy
from typing import Any, cast

import aiohttp
import pytest

from scripts.fetch_zoning_delay_data import (
    Geocoder,
    filter_target_matters,
    write_delay_module,
)


def _row(matter_id, category="ZONING RECLASSIFICATIONS", intro="2024-01-10T00:00:00"):
    return {
        "matterId": matter_id,
        "matterCategory": category,
        "introductionDate": intro,
    }


class TestFilterTargetMatters:
    def test_keeps_in_window_zoning_matters(self):
        pages = [[_row("a"), _row("b", category="APPOINTMENTS")]]
        assert [m["matterId"] for m in filter_target_matters(pages)] == ["a"]

    def test_excludes_matters_before_term_start(self):
        pages = [[_row("a", intro="2023-04-19T00:00:00"), _row("b")]]
        assert [m["matterId"] for m in filter_target_matters(pages)] == ["b"]

    def test_term_start_day_is_included(self):
        pages = [[_row("a", intro="2023-05-15T00:00:00")]]
        assert [m["matterId"] for m in filter_target_matters(pages)] == ["a"]

    def test_deduplicates_by_matter_id_across_pages(self):
        # Pagination shift can repeat a row on a later page; the raw sweep for
        # the committed data contained 88 such duplicates outside the zoning
        # category. A duplicate would double-count in every ward statistic.
        pages = [[_row("a"), _row("b")], [_row("a")]]
        assert [m["matterId"] for m in filter_target_matters(pages)] == ["a", "b"]


class TestWriteDelayModule:
    def _load(self, path):
        return runpy.run_path(str(path))

    def test_none_median_round_trips_importably(self, tmp_path):
        out = tmp_path / "delay.py"
        stats: dict[int, dict[str, float | int | None]] = {
            5: {
                "zoning_median_days": None,
                "zoning_matter_count": 2,
                "zoning_stalled_count": 1,
                "n_resolved": 0,
                "n_pending": 2,
            }
        }
        meta = {"term_start": "2023-05-15", "computed_at": "2026-07-23"}
        write_delay_module(stats, meta, path=out)
        module = self._load(out)
        assert module["WARD_ZONING_DELAY"][5]["zoning_median_days"] is None
        assert module["WARD_ZONING_DELAY"][5]["zoning_matter_count"] == 2

    def test_meta_with_bool_and_none_round_trips_importably(self, tmp_path):
        # json.dumps would emit true/null here — a NameError at import time.
        out = tmp_path / "delay.py"
        stats: dict[int, dict[str, float | int | None]] = {
            1: {
                "zoning_median_days": 42.0,
                "zoning_matter_count": 3,
                "zoning_stalled_count": 0,
                "n_resolved": 3,
                "n_pending": 0,
            }
        }
        meta = {"forced": True, "note": None, "unassigned_record_numbers": ["O1-1"]}
        write_delay_module(stats, meta, path=out)
        module = self._load(out)
        assert module["ZONING_DELAY_META"]["forced"] is True
        assert module["ZONING_DELAY_META"]["note"] is None


class TestWriteMattersModule:
    def test_matters_round_trip_importably(self, tmp_path):
        from scripts.fetch_zoning_delay_data import write_matters_module

        out = tmp_path / "matters.py"
        ward_matters = {
            35: [
                {
                    "record_number": "O2026-0012345",
                    "matter_guid": "abc-123",
                    "title": "Zoning Reclassification at 1 N Test St",
                    "address": "1 N Test St",
                    "introduction_date": "2026-01-21T00:00:00",
                    "final_action_date": None,
                    "status": "4-In Committee",
                    "sub_status": None,
                    "lat": 41.9,
                    "lon": -87.7,
                    "near_boundary": True,
                }
            ]
        }
        unassigned = [
            {
                "record_number": "O2026-0099999",
                "matter_guid": "def-456",
                "title": "Unparseable title",
                "address": None,
                "introduction_date": "2026-02-01T00:00:00",
                "final_action_date": None,
                "status": "1-Introduced",
                "sub_status": None,
                "lat": None,
                "lon": None,
                "near_boundary": False,
            }
        ]
        write_matters_module(ward_matters, unassigned, path=out)
        module = runpy.run_path(str(out))
        assert module["WARD_ZONING_MATTERS"] == ward_matters
        assert module["UNASSIGNED_ZONING_MATTERS"] == unassigned
        # None and bools must be Python literals, not JSON null/true.
        assert module["WARD_ZONING_MATTERS"][35][0]["near_boundary"] is True
        assert module["UNASSIGNED_ZONING_MATTERS"][0]["address"] is None


def _no_network_session() -> aiohttp.ClientSession:
    """A session stand-in; tests monkeypatch the provider methods instead."""
    return cast(aiohttp.ClientSession, object())


class TestGeocoderCacheSemantics:
    @pytest.mark.asyncio
    async def test_cached_success_is_returned_without_provider_call(self, monkeypatch):
        cache: dict[str, dict[str, Any] | None] = {
            "1 N Fake St": {"lat": 41.9, "lon": -87.7, "ward": 1}
        }
        geocoder = Geocoder(cache, refresh=False)

        async def boom(session, query):  # pragma: no cover - must not run
            raise AssertionError("provider should not be called")

        monkeypatch.setattr(geocoder, "_nominatim", boom)
        assert await geocoder.geocode(_no_network_session(), "1 N Fake St") == (
            41.9,
            -87.7,
        )

    @pytest.mark.asyncio
    async def test_refresh_retries_only_cached_failures(self, monkeypatch):
        cache: dict[str, dict[str, Any] | None] = {
            "1 N Good St": {"lat": 41.9, "lon": -87.7, "ward": 1},
            "2 N Bad St": None,
        }
        geocoder = Geocoder(cache, refresh=True)
        calls = []

        async def fake_nominatim(session, query):
            calls.append(query)
            return 41.85, -87.65

        monkeypatch.setattr(geocoder, "_nominatim", fake_nominatim)

        # Cached success: no provider call even with refresh on.
        assert await geocoder.geocode(_no_network_session(), "1 N Good St") == (
            41.9,
            -87.7,
        )
        assert calls == []
        # Cached failure: retried.
        assert await geocoder.geocode(_no_network_session(), "2 N Bad St") == (
            41.85,
            -87.65,
        )
        assert calls == ["2 N Bad St, Chicago, IL"]

    @pytest.mark.asyncio
    async def test_transient_provider_error_is_not_cached_as_failure(self, monkeypatch):
        from scripts.fetch_zoning_delay_data import GeocodeUnavailable

        cache: dict[str, dict[str, Any] | None] = {}
        geocoder = Geocoder(cache, refresh=False)

        async def unavailable(session, query):
            raise GeocodeUnavailable("HTTP 503")

        monkeypatch.setattr(geocoder, "_nominatim", unavailable)
        assert await geocoder.geocode(_no_network_session(), "3 N Flaky St") is None
        # A transient failure must not poison the committed cache.
        assert "3 N Flaky St" not in cache

    @pytest.mark.asyncio
    async def test_definitive_no_result_is_cached_as_failure(self, monkeypatch):
        cache: dict[str, dict[str, Any] | None] = {}
        geocoder = Geocoder(cache, refresh=False)

        async def no_result(session, query):
            return None

        monkeypatch.setattr(geocoder, "_nominatim", no_result)
        assert await geocoder.geocode(_no_network_session(), "4 N Nowhere St") is None
        assert cache["4 N Nowhere St"] is None

    @pytest.mark.asyncio
    async def test_out_of_chicago_hit_is_cached_as_failure(self, monkeypatch):
        cache: dict[str, dict[str, Any] | None] = {}
        geocoder = Geocoder(cache, refresh=False)

        async def waukegan(session, query):
            return 42.36, -87.84

        monkeypatch.setattr(geocoder, "_nominatim", waukegan)
        assert (
            await geocoder.geocode(_no_network_session(), "400 N Elizabeth Ave") is None
        )
        assert cache["400 N Elizabeth Ave"] is None
