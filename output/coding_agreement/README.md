# ISO/IEC 5259-3 extraction agreement (AIDGO vs. Arellano)

Unitisation agreement between two independent atomic extractions of ISO/IEC FDIS 5259-3.
Arellano clause numbers were mapped to FDIS numbering with the crosswalk in
`aidgo_tools/migrate.py` (ARELLANO_CROSSWALK).

| | AIDGO | Arellano |
|---|---|---|
| Atomic units | 167 | 145 (+2 coded from ISO/IEC 5259-2, excluded) |
| Clauses with SHALL units | 44 | 53 |

* Clauses coded by both: **44**; Jaccard overlap of clause sets: **0.830**
* Exact agreement on unit count within shared clauses: **19/44**; mean absolute difference **1.73** units
* Only AIDGO: none
* Only Arellano: 6.4, 7.2.4, 8.3.1.3, 12.2.3, 12.3.2, 12.6.1, 12.6.2, 12.6.3, 12.9

Per-clause counts: [clauses.csv](clauses.csv).

Scope note: this is agreement on *what the requirements are*, a precondition for, not a substitute
for, inter-rater reliability on alignment types.
