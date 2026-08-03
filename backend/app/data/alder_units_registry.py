"""Curated registry of alder-initiated housing-production changes (Phase 2).

Hand/agent-curated and reviewed like a data file — every item must carry at
least one citation and survive the validation test in
``tests/test_alder_units_registry.py`` (the CI gatekeeper). Ships **empty** in
Phase 1; the news-research workflow appends entries later.

Aggregation semantics (see ``app.imports.sources.ward_metrics``):
  - ``bonus_units``  = Σ ``units_delta`` over items with ``kind == "upzone"``
  - ``lost_units``   = Σ ``units_delta`` over items with
                       ``kind in {"downzone", "shrunk_development"}``
  - ``mention_to_passage_days`` = median over items that have BOTH
                                  ``first_public_date`` and ``date``

Item schema (all dates are ISO ``YYYY-MM-DD`` strings)::

    ALDER_UNITS_REGISTRY: list[dict] = [
      {
        "ward": 1,                       # int, 1..50, unique per registry entry
        "alder": "Daniel La Spata",      # resolves via normalize_name to a known alder
        "elected": "2019-05-20",         # date the alder took office (window start)
        "items": [
          {
            "name": "2354 N Milwaukee Ave upzone (B3-2 -> B2-5)",
            "kind": "upzone",            # "upzone" | "downzone" | "shrunk_development"
            "units_delta": 120,          # int, ALWAYS POSITIVE; kind decides the bucket
            "date": "2024-06-12",        # date the change took effect (passage)
            "elms_record_number": "O2024-0009123",  # optional; ^[A-Z]{1,2}\\d{4}-\\d+$
            "first_public_date": "2023-11-02",       # optional; <= date
            "citations": ["https://blockclubchicago.org/..."],  # REQUIRED, >= 1, http(s)
            "notes": "...",              # optional free text
          },
        ],
      },
    ]

Hard curation rules (enforced by the validation test):
  - ``units_delta`` is always a positive integer; the sign/bucket is decided by
    ``kind``, never by a negative number.
  - Every item needs >= 1 citation, each an ``http://`` or ``https://`` URL.
  - ``first_public_date <= date`` when both are present.
  - Each item's ``date`` is on or after the alder's ``elected`` date
    (alder-initiated attribution only covers the current term).
  - No duplicate ward across top-level entries; ``ward`` in 1..50.
  - ``elms_record_number`` (when present) matches ``^[A-Z]{1,2}\\d{4}-\\d+$``.
  - ``alder`` resolves via ``normalize_name`` against the known alder roster.
"""

# Curated via scripts/merge_units_registry.py from reviewed research
# output; every item is citation-backed (see
# docs/alder-units-research-protocol.md and methodology doc §6).
ALDER_UNITS_REGISTRY: list[dict] = [
    {
        "ward": 21,
        "alder": "Ronnie Mosley",
        "elected": "2023-05-15",
        "items": [
            {
                "name": "Morgan Park Missing Middle mass rezoning (RS-3 -> RT-4, A-8970) — Superior Source site, 1320-38 W 109th Pl & 1425-29 W 109th (18 units)",
                "kind": "upzone",
                "units_delta": 18,
                "date": "2025-05-21",
                "elms_record_number": "O2025-0016179",
                "first_public_date": "2025-04-16",
                "citations": [
                    "https://www.chicago.gov/city/en/depts/mayor/press_room/press_releases/2026/january/missing-middle-round-two.html",
                    "https://blockclubchicago.org/2026/01/22/developers-to-construct-missing-middle-housing-in-morgan-park/",
                    "https://www.chicago.gov/city/en/depts/dcd/provdrs/ec_dev/news/2025/november/land-sale--incentives-proposed-for-morgan-park--missing-middle--.html",
                    "https://chicago.councilmatic.org/legislation/o2025-0016179/",
                ],
                "notes": "1320-38 W 109th Pl is explicitly within A-8970's listed range (1233-1435 W 109th Pl). The second address is given as '1425-29 W. 109th St.' in the mayoral release (A-8970 lists 1201-1421 W 109th St, so 1425-29 would be just past the listed range) but as '1425-29 W. 109th Place' in Block Club, which is within the listed range. Attribution: Same enabling change as the Famor item: Mosley's aldermanic application A-8970 (O2025-0016179, sole primary sponsor, passed 2025-05-21) rezoned these Morgan Park blocks RS-3 -> RT-4 to facilitate Missing Middle construction. Superior Source Capital LLC's six three-flats ('six three-flat buildings housing 18 new units in Morgan Park' per mayor's Jan 21, 2026 release; 'six three-flats housing 18 new units' per Block Club) are on 1320-38 W 109th Pl and 1425-29 W 109th, inside the rezoned area; the three-flats require the RT-4 zoning Mosley introduced. The land-sale ordinance itself (O2025-0021689) was mayoral, so units are attributed to the alder-initiated rezoning.",
            },
            {
                "name": "Morgan Park Missing Middle mass rezoning (RS-3 -> RT-4, A-8970) — Vazquez site, 1111-1240 W 110th Pl (15 units)",
                "kind": "upzone",
                "units_delta": 15,
                "date": "2025-05-21",
                "elms_record_number": "O2025-0016179",
                "first_public_date": "2025-04-16",
                "citations": [
                    "https://www.chicago.gov/city/en/depts/mayor/press_room/press_releases/2026/january/missing-middle-round-two.html",
                    "https://blockclubchicago.org/2026/01/22/developers-to-construct-missing-middle-housing-in-morgan-park/",
                    "https://www.chicago.gov/city/en/depts/dcd/provdrs/ec_dev/news/2025/may/new-zoning-will-facilitate--missing-middle--residential-projects.html",
                    "https://chicago.councilmatic.org/legislation/o2025-0016179/",
                ],
                "notes": "Address correction vs. the press-release wording: the mayor's release and Block Club describe the site as '1158-1240 W. 110th Place and 1235 W. 110th St.', but land-sale ordinance O2025-0021688's title lists the actual lots as 1235, 1240, 1222, 1200, and 1111 W 110th Pl (no 1158 lot; 1235 is on 110th Pl, not 110th St). All five fall within A-8970's listed common-address ranges (1101-1437 and 1200-1436 W 110th Pl) and were spot-verified as rezoned by A8970 on 2025-05-21 in the City zoning dataset. Developer history: site originally assigned to Toro Construction Corp. in the Aug 2025 selection; approved developer in Jan 2026 is Vazquez Housing Development; both iterations stated 15 units. Attribution: Mosley is the sole sponsor of aldermanic zoning application A-8970 (O2025-0016179; filing office Ward 21; ordinance text signed 'Ronnie L. Mosley, Alderman, 21st Ward'; introduced 2025-04-16, passed 2025-05-21 per the City Clerk eLMS API), which rezoned these Morgan Park blocks RS-3 -> RT-4 to facilitate Missing Middle construction — RS-3 permits only detached houses, so the RT-4 he introduced is what makes Vazquez Housing Development's five three-flats ('15 units are set for development' per the mayor's Jan 21, 2026 release; 'five three-flats with 15 units in all' per Block Club) legal. All five lots per land-sale ordinance O2025-0021688 (1235, 1240, 1222, 1200, 1111 W 110th Pl) are confirmed inside the A-8970 rezoning: the City of Chicago zoning dataset (dj47-wfun) shows each lot in an RT-4 polygon with ordinance A8970 dated 2025-05-21. The land-sale ordinance itself was a mayoral introduction, so units are attributed to the alder-initiated enabling rezoning.",
            },
        ],
    }
]
