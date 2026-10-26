"""Extraction agreement between the AIDGO coding of ISO/IEC 5259-3 and M. Arellano's independent coding.

This measures agreement on *unitisation* (which clauses carry SHALL requirements, and into how
many atomic units each is split). It is not an inter-rater reliability statistic for alignment
types; that requires a second rater classifying the 24 alignment pairs.

    python -m aidgo_tools agreement
Writes output/coding_agreement/{clauses.csv,README.md}.
"""

from __future__ import annotations

import csv
from collections import Counter

from . import paths
from .build import read


def unit_counts() -> tuple[Counter, Counter, list[str]]:
    reqs = read("iso_requirements.csv")
    conj = read("iso_conjunctive_requirements.csv")
    has_conj = {c["decomposes"] for c in conj}
    aidgo: Counter = Counter()
    for c in conj:
        aidgo[c["clause"]] += 1
    for r in reqs:  # clause-level requirements without atomic children are atomic themselves
        if r["id"] not in has_conj:
            aidgo[r["clause"]] += 1
    rows = read("coding/arellano_5259-3_requirements.csv")
    arellano: Counter = Counter()
    out_of_scope = []
    for r in rows:
        if r["fdis_clause"]:
            arellano[r["fdis_clause"]] += 1
        else:
            out_of_scope.append(r["id"])
    return aidgo, arellano, out_of_scope


def clause_key(c: str) -> tuple:
    return tuple(int(x) for x in c.split("."))


def main() -> int:
    aidgo, arellano, oos = unit_counts()
    A, B = set(aidgo), set(arellano)
    both, only_a, only_b = A & B, A - B, B - A
    out = paths.OUTPUT / "coding_agreement"
    out.mkdir(parents=True, exist_ok=True)
    with (out / "clauses.csv").open("w", newline="", encoding="utf-8") as fh:
        w = csv.writer(fh, lineterminator="\n")
        w.writerow(["fdis_clause", "aidgo_units", "arellano_units", "in_both", "difference"])
        for c in sorted(A | B, key=clause_key):
            w.writerow([c, aidgo.get(c, 0), arellano.get(c, 0), int(c in both),
                        arellano.get(c, 0) - aidgo.get(c, 0)])
    exact = sum(aidgo[c] == arellano[c] for c in both)
    mad = sum(abs(aidgo[c] - arellano[c]) for c in both) / len(both) if both else 0.0
    jacc = len(both) / len(A | B) if A | B else 0.0
    summary = f"""# ISO/IEC 5259-3 extraction agreement (AIDGO vs. Arellano)

Unitisation agreement between two independent atomic extractions of ISO/IEC FDIS 5259-3.
Arellano clause numbers were mapped to FDIS numbering with the crosswalk in
`aidgo_tools/migrate.py` (ARELLANO_CROSSWALK).

| | AIDGO | Arellano |
|---|---|---|
| Atomic units | {sum(aidgo.values())} | {sum(arellano.values())} (+{len(oos)} coded from ISO/IEC 5259-2, excluded) |
| Clauses with SHALL units | {len(A)} | {len(B)} |

* Clauses coded by both: **{len(both)}**; Jaccard overlap of clause sets: **{jacc:.3f}**
* Exact agreement on unit count within shared clauses: **{exact}/{len(both)}**; mean absolute difference **{mad:.2f}** units
* Only AIDGO: {", ".join(sorted(only_a, key=clause_key)) or "none"}
* Only Arellano: {", ".join(sorted(only_b, key=clause_key)) or "none"}

Per-clause counts: [clauses.csv](clauses.csv).

Scope note: this is agreement on *what the requirements are*, a precondition for, not a substitute
for, inter-rater reliability on alignment types.
"""
    (out / "README.md").write_text(summary, encoding="utf-8")
    print(summary)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
