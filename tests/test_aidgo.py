"""Regression tests: every figure reported in the thesis and papers is recomputed from the KG.

Run:  python -m pytest -q
"""

from __future__ import annotations

import csv
from collections import Counter

import pytest
from rdflib import Graph, Namespace
from rdflib.namespace import RDF

from aidgo_tools import paths
from aidgo_tools.build import Dataset, build_graph, coverage_status, load_store, main as build_main
from aidgo_tools.query import query_files, resolve, run
from aidgo_tools.validate import dangling_iris, shacl_report

AIDGO = Namespace(paths.AIDGO)


@pytest.fixture(scope="session", autouse=True)
def built():
    build_main()


@pytest.fixture(scope="session")
def graph() -> Graph:
    return Graph().parse(paths.KG_TTL)


@pytest.fixture(scope="session")
def store():
    return load_store(star=True)


def rows(name: str, store):
    return run(resolve(name).read_text(encoding="utf-8"), store)[1]


# --------------------------------------------------------------- dataset size
def test_node_counts(graph):
    count = lambda c: len(set(graph.subjects(RDF.type, c)))  # noqa: E731
    assert count(AIDGO.Concept) == 74
    assert count(AIDGO.RequirementCollection) == 51
    assert count(AIDGO.LegalRequirement) == 17
    assert count(AIDGO.ConjunctiveRequirement) == 119
    # 190 technical requirement nodes = 71 clause-level + 119 atomic (not 190 requirements)
    assert count(AIDGO.TechnicalRequirement) == 190
    assert count(AIDGO.AlignmentAssertion) == 24


# --------------------------------------------------------------- headline statistics
def test_assertion_level_distribution(store):
    got = {r[0].split(":")[1]: int(r[1]) for r in rows("CQ-M5", store)}
    assert got == {"CompletelySatisfies": 6, "PartiallySatisfies": 15, "NoAlignment": 3,
                   "RelatedTo": 0, "ConflictsWith": 0}


def test_obligation_level_coverage(store):
    got = {r[0]: int(r[1]) for r in rows("CQ-COV", store)}
    assert got == {"FullyCovered": 2, "PartiallyCovered": 12, "NotCovered": 3}


def test_materialised_coverage_matches_rule(store):
    for legal_id, _ref, status, _n, types in rows("CQ-COV-detail", store):
        assert status == "aidgo:" + coverage_status(types.split(", ")), legal_id


def test_coverage_rule():
    assert coverage_status(["CompletelySatisfies", "CompletelySatisfies"]) == "FullyCovered"
    assert coverage_status(["CompletelySatisfies", "PartiallySatisfies"]) == "PartiallyCovered"
    assert coverage_status(["NoAlignment"]) == "NotCovered"
    assert coverage_status(["NoAlignment", "PartiallySatisfies"]) == "PartiallyCovered"


# --------------------------------------------------------------- integrity
def test_shacl_conforms(graph):
    ok, results = shacl_report(graph)
    assert ok, [r for r in results if r[0] == "Violation"]


def test_no_dangling_iris(graph):
    assert dangling_iris(graph) == []


def test_no_deprecated_terms_in_data():
    for a in Dataset().alignments:
        assert a["alignment_type"] in paths.ALIGNMENT_TYPES
        assert a["alignment_basis"] in paths.ALIGNMENT_BASES


def test_every_requirement_has_stage(graph):
    for s in graph.subjects(RDF.type, AIDGO.TechnicalRequirement):
        assert graph.value(s, AIDGO.dqmlcStage) is not None, s


def test_build_is_deterministic():
    a = paths.KG_TTL.read_bytes()
    build_main()
    assert paths.KG_TTL.read_bytes() == a


# --------------------------------------------------------------- queries
@pytest.mark.parametrize("q", [p.stem for p in query_files()])
def test_every_query_runs(q, store):
    cols, result = run(resolve(q).read_text(encoding="utf-8"), store)
    assert cols
    if q != "CQ-M4":  # no ConflictsWith assertion exists: empty is the correct answer
        assert result, f"{q} returned no rows"


def test_star_layer_matches_assertions(store):
    star = rows("CQ-STAR", store)
    positive = [a for a in Dataset().alignments if a["tech_id"]]
    assert len(star) == len(positive) == 21
    got = {(r[0], r[1], r[2].split(":")[1]) for r in star}
    assert got == {(a["legal_id"], a["tech_id"], a["alignment_type"]) for a in positive}


def test_gap_obligations(store):
    assert [r[2] for r in rows("CQ-M3", store)] == ["AiaPrReq_10.5", "AiaPrReq_10.5_a", "AiaPrReq_10.5_b"]


# --------------------------------------------------------------- site
def test_site_in_sync():
    from aidgo_tools import site
    assert site.main(["--check"]) == 0


def test_second_coding_has_no_iso_text():
    with (paths.CODING / "arellano_5259-3_requirements.csv").open(encoding="utf-8") as fh:
        header = next(csv.reader(fh))
    assert not {"definition", "text", "iso_text"} & set(header)
