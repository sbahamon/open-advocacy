# Alder units research runs (audit artifacts)

Raw output of the multi-agent research workflow described in
`docs/alder-units-research-protocol.md`. Each file is one run's full result —
the entries that were merged into
`backend/app/data/alder_units_registry.py` **plus** everything that did not
survive: `rejected` (items killed by the adversarial verifiers, with the full
refutation) and `omitted` (leads the researchers found but could not back with
a citable unit count).

These files are the audit trail for the registry: every committed
`units_delta` can be traced here to its citations and its verification
verdict, and every non-obvious *absence* (an alder with no entry) to the
leads that were considered and why they were dropped.

| Run | Scope | Outcome |
| --- | ----- | ------- |
| `2026-08-03-pilot.json` | Wards 21 (Mosley), 9 (Beale), 11 (Lee), 28 (Ervin), 7 (Mitchell) | 1 entry merged (Ward 21, 2 items, 33 bonus units); 4 wards researched with zero items surviving verification |
