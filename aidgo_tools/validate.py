"""Validate output/aidgo_kg.ttl against shapes/aidgo-shapes.ttl and referential-integrity checks.

Exit status 0 when there are no SHACL Violations (Warnings are reported but tolerated).
"""

from __future__ import annotations

import sys

from pyshacl import validate
from rdflib import Graph, URIRef
from rdflib.namespace import SH

from . import paths


def shacl_report(data: Graph | None = None) -> tuple[bool, list[tuple[str, str, str, str]]]:
    data = data if data is not None else Graph().parse(paths.KG_TTL)
    shapes = Graph().parse(paths.SHAPES)
    _, report, _ = validate(data, shacl_graph=shapes, ont_graph=None, inference="none",
                            advanced=True, allow_warnings=True)
    results = []
    for r in report.subjects(SH.resultSeverity, None):
        sev = str(report.value(r, SH.resultSeverity)).split("#")[-1]
        focus = str(report.value(r, SH.focusNode)).split("#")[-1]
        path = report.value(r, SH.resultPath)
        msg = str(report.value(r, SH.resultMessage))
        results.append((sev, focus, str(path).split("#")[-1] if path else "", msg))
    results.sort()
    return not any(s == "Violation" for s, *_ in results), results


def dangling_iris(g: Graph) -> list[str]:
    """IRIs in the AIDGO data namespaces used as objects but never described as subjects."""
    ns = (paths.ISO5259, paths.AIAPR, paths.AIDGO)
    subjects = {str(s) for s in g.subjects()}
    out = set()
    for o in g.objects():
        if not isinstance(o, URIRef):
            continue
        o = str(o)
        if o.startswith(ns) and o not in subjects:
            out.add(o)
    return sorted(out)


def main() -> int:
    g = Graph().parse(paths.KG_TTL)
    ok, results = shacl_report(g)
    violations = [r for r in results if r[0] == "Violation"]
    warnings = [r for r in results if r[0] == "Warning"]
    for sev, focus, path, msg in results:
        print(f"  [{sev}] {focus} {path}: {msg}")
    dangling = dangling_iris(g)
    for d in dangling:
        print(f"  [Violation] dangling IRI (used but never defined): {d}")
    print(f"SHACL: {len(violations)} violation(s), {len(warnings)} warning(s); "
          f"dangling IRIs: {len(dangling)}")
    return 0 if ok and not dangling else 1


if __name__ == "__main__":
    sys.exit(main())
