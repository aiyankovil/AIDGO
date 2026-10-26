"""AIDGO semantic distance score.

similarity(A, B) = 1 / (1 + d(A, B)),  d = weighted shortest-path length over the AIDGO graph.

  * Rada et al. (1989)   edge counting: fewer edges -> more similar
  * Wu & Palmer (1994)   hierarchy steps carry a depth penalty (broader = 1.5)
  * Li et al. (2003)     non-linear transform 1/(1+d)
  * Dijkstra (1959)      optimal weighted shortest path

The graph is read from output/aidgo_kg.ttl, so every score is reproducible from the published KG.
Edges are treated as undirected. NoAlignment assertions contribute no edge (there is no technical
node). Lexically derived aidgo:uses links are excluded unless --with-concept-links is given,
because they are not expert-validated.

    python -m aidgo_tools distance                         # all legal x technical pairs -> CSV
    python -m aidgo_tools distance AiaPrReq_10.2_4 AidgoReq_7_3_5_2   # one pair, with full path
"""

from __future__ import annotations

import csv
import heapq
import sys
from collections import defaultdict

from rdflib import Graph, Namespace
from rdflib.namespace import RDF, SKOS

from . import paths

AIDGO = Namespace(paths.AIDGO)
TAIR = Namespace(paths.TAIR)

EDGE_WEIGHTS = {
    "CompletelySatisfies": 1.0,  # direct normative equivalence
    "decomposes": 1.0,           # same normative family (atomic -> clause-level requirement)
    "PartiallySatisfies": 2.0,   # partial coverage with documented gap
    "broader": 1.5,              # hierarchy / membership step (flat penalty, after Wu & Palmer)
    "broaderConcept": 1.5,       # concept hierarchy step
    "uses": 2.0,                 # requirement -> concept (optional, derived)
    "RelatedTo": 3.0,            # associative only
    "ConflictsWith": 5.0,        # incompatible assumptions
}


def local(u) -> str:
    s = str(u)
    return s.split("#")[-1]


def build_adjacency(g: Graph, with_concept_links: bool = False) -> dict[str, list[tuple[str, float, str]]]:
    adj: dict[str, list[tuple[str, float, str]]] = defaultdict(list)

    def edge(a, b, kind: str) -> None:
        w = EDGE_WEIGHTS[kind]
        adj[local(a)].append((local(b), w, kind))
        adj[local(b)].append((local(a), w, kind))

    for m in g.subjects(RDF.type, AIDGO.AlignmentAssertion):
        t = local(g.value(m, AIDGO.alignmentType))
        tr = g.value(m, AIDGO.technicalRequirement)
        if t in EDGE_WEIGHTS and tr != RDF.nil:
            edge(g.value(m, AIDGO.legalRequirement), tr, t)
    for s, o in g.subject_objects(TAIR.decomposes):
        edge(s, o, "decomposes")
    for s, o in g.subject_objects(AIDGO.inCollection):
        edge(s, o, "broader")
    for s, o in g.subject_objects(SKOS.broader):
        kind = "broaderConcept" if (s, RDF.type, AIDGO.Concept) in g else "broader"
        edge(s, o, kind)
    if with_concept_links:
        for s, o in g.subject_objects(AIDGO.uses):
            edge(s, o, "uses")
    return adj


def shortest_paths(adj, source: str) -> tuple[dict[str, float], dict[str, tuple[str, str]]]:
    dist, prev = {source: 0.0}, {}
    pq = [(0.0, source)]
    while pq:
        d, u = heapq.heappop(pq)
        if d > dist.get(u, float("inf")):
            continue
        for v, w, kind in sorted(adj.get(u, [])):  # sorted -> deterministic tie-breaking
            nd = d + w
            if nd < dist.get(v, float("inf")):
                dist[v], prev[v] = nd, (u, kind)
                heapq.heappush(pq, (nd, v))
    return dist, prev


def path_to(prev, source: str, target: str) -> list[tuple[str, str, str]]:
    steps, node = [], target
    while node != source:
        u, kind = prev[node]
        steps.append((u, kind, node))
        node = u
    return list(reversed(steps))


def score(d: float) -> float:
    return 1.0 / (1.0 + d)


def main(argv: list[str]) -> int:
    with_links = "--with-concept-links" in argv
    argv = [a for a in argv if not a.startswith("--")]
    g = Graph().parse(paths.KG_TTL)
    adj = build_adjacency(g, with_links)
    if len(argv) == 2:
        a, b = argv
        dist, prev = shortest_paths(adj, a)
        if b not in dist:
            print(f"{a} and {b} are not connected: similarity 0")
            return 0
        print(f"distance({a}, {b}) = {dist[b]:.2f}   similarity = {score(dist[b]):.4f}")
        for u, kind, v in path_to(prev, a, b):
            print(f"  {u} --{kind} ({EDGE_WEIGHTS[kind]})--> {v}")
        return 0
    legal = sorted(local(s) for s in g.subjects(RDF.type, AIDGO.LegalRequirement))
    tech = sorted(local(s) for s in g.subjects(RDF.type, AIDGO.TechnicalRequirement))
    out = paths.OUTPUT / "distance"
    out.mkdir(parents=True, exist_ok=True)
    fn = out / ("legal_tech_scores_with_concepts.csv" if with_links else "legal_tech_scores.csv")
    reachable = 0
    with fn.open("w", newline="", encoding="utf-8") as fh:
        w = csv.writer(fh, lineterminator="\n")
        w.writerow(["legal_id", "tech_id", "distance", "similarity", "hops", "path"])
        for a in legal:
            dist, prev = shortest_paths(adj, a)
            for b in tech:
                if b in dist:
                    reachable += 1
                    p = path_to(prev, a, b)
                    w.writerow([a, b, f"{dist[b]:.2f}", f"{score(dist[b]):.4f}", len(p),
                                " > ".join([a] + [f"[{k}] {v}" for _, k, v in p])])
                else:
                    w.writerow([a, b, "", "0.0000", "", ""])
    print(f"  {fn.relative_to(paths.ROOT)}: {len(legal)} x {len(tech)} pairs, {reachable} connected")
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
