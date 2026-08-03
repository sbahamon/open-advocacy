# Alder units research protocol (bonus / lost units registry)

How `ALDER_UNITS_REGISTRY` (`backend/app/data/alder_units_registry.py`) gets
populated. The registry drives three hidden scorecard metrics — `bonus_units`,
`lost_units`, `mention_to_passage_days` — and is a **committed, reviewed data
file**: every number must be citation-backed, and CI
(`backend/tests/test_alder_units_registry.py`) is the gatekeeper. The curation
rules of record are in the registry module's docstring and methodology doc §6;
this document describes the *process* that produces entries.

## Pipeline overview

```
ALDER_ZONING_CANDIDATES (seed)          news/web sweep
        │                                     │
        ▼                                     ▼
 per-alder research agent  ──items──▶  adversarial verifier(s)
                                              │ confirmed / corrected only
                                              ▼
                              research JSON (reviewed by a human)
                                              │
                                              ▼
                    python -m scripts.merge_units_registry <json> [--replace]
                                              │ shared validators must pass
                                              ▼
                        app/data/alder_units_registry.py  (committed)
                                              │
                                              ▼
                              CI: tests/test_alder_units_registry.py
```

One agent workflow run produces a **research JSON** file (list of registry
entries, plus research-only annotations). A human reviews it, then merges it
with `scripts/merge_units_registry.py`, which:

- folds `attribution_rationale` into `notes` and drops transient keys
  (`_verify`, `elected_citation`);
- validates the merged registry with
  `app/imports/sources/alder_units_validation.py` — the *same* validators the
  CI test runs, so a clean merge cannot fail CI;
- rewrites the registry module in place (schema docstring preserved),
  erroring on ward collisions unless `--replace` is given;
- writes nothing if any entry fails validation.

## Research phase (one agent per alder)

Seeded by `backend/app/data/alder_zoning_candidates.py` — the alder's
*sponsored* zoning matters from the City Clerk eLMS (record numbers, intro /
final-action dates, geocoded ward). Agents sweep local coverage (Block Club
Chicago, Urbanize Chicago, Chicago YIMBY, Crain's, Tribune, Sun-Times, ward
newsletters, Plan Commission documents) since the alder took office.

Hard rules (mirrored in the agent prompts):

1. **No estimates.** Every `units_delta` must appear in a fetched citation
   (a stated before/after pair is acceptable for `shrunk_development`).
   A relevant change with no citable unit count is recorded in the run's
   `omitted` log, never as an item.
2. **≥ 1 http(s) citation per item**, actually fetched and read by the agent.
3. **Attribution to the initiating alder.** Ward rezonings are normally
   introduced by the local alder (aldermanic prerogative), but sponsorship of
   someone else's project or a mayoral/city-wide program does not qualify.
   The geocoded ward on a candidate matter is a hint, not the attribution.
4. `date` = passage/effect date; `first_public_date` = earliest public
   mention when found. Items must post-date the alder taking office.
5. **Quality over quantity**, and both directions: downzones and shrunk
   developments usually have no eLMS seed and only exist in news coverage.

## Verification phase (adversarial)

Every item is re-checked by a separate verifier agent instructed to *refute*
it: re-fetch each citation, confirm the unit count is stated, the kind
semantics fit, the attribution holds, and the dates are consistent
(cross-checking the eLMS record's final-action date when present). Verdicts
are `confirmed`, `corrected` (with a full replacement item), or `rejected`;
only the first two survive. Verifiers default to `rejected` when uncertain —
a wrong number is worse than a missing one.

## Coverage bar (why the metrics are still hidden)

`bonus_units` / `lost_units` stay `show_in_table=False` in
`CHICAGO_WARD_METRICS` until enough wards have researched entries that blanks
read as "not researched yet" rather than implying zero. Bar: **≥ 40 of 50
wards researched** (an alder researched and yielding zero cited items still
counts as researched — record that outcome in this document's pilot log).
Flipping the flag is a one-line seeder change; the drift-detection fix in
`import_scorecard_projects.py` propagates it to existing DBs on the next
seeder run.

## Pilot log

| Date | Wards | Outcome |
| ---- | ----- | ------- |
| 2026-08-03 | 21 (Mosley), 9 (Beale), 11 (Lee), 28 (Ervin), 7 (Mitchell) | 5-alder pilot (full run output: `docs/data/alder-units-research/2026-08-03-pilot.json`). Merged: Ward 21 — 2 upzone items, 33 bonus units (Morgan Park Missing Middle A-8970 sites). Researched with zero surviving items: 9, 11, 28, 7 — Beale/Lee/Mitchell produced no citable unit counts (9/16/10 omitted leads respectively); Ervin's 2 candidates (Garfield Green 81u, Hub32 51u) were rejected on the initiation test (developer/mayoral-program filings, not alder-initiated). Two further Mosley items (24u, 12u) were rejected on enablement checks — parts of those sites were already RT-4 before his ordinance and no citation states the reduced count. Coverage: 5/50 wards researched. |
