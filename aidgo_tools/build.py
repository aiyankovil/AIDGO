"""Build the AIDGO knowledge graph from data/*.csv.

Outputs
  output/aidgo_kg.ttl       ontology + instance data, plain RDF 1.1 (rdflib, pySHACL, Protege, GraphDB ...)
  output/aidgo_kg_star.ttl  the same graph plus an RDF 1.2 (RDF-star) annotation layer in which every
                            alignment is the annotated triple  L aidgo:alignedWith T ~ aidgo:Map_X {| ... |}
                            so that the AlignmentAssertion node is the reifier of the triple it describes.
  output/aidgo_kg.nt        N-Triples of the plain graph (sorted, for stable diffs)

The build is deterministic: same inputs -> byte-identical outputs.
"""

from __future__ import annotations

import csv
import re
from collections import defaultdict
from dataclasses import dataclass, field

import pyoxigraph as ox
from rdflib import Graph, Literal, Namespace, URIRef
from rdflib.namespace import DCTERMS, OWL, PROV, RDF, RDFS, SKOS, XSD

from . import paths
from .paths import stage_for_clause

AIDGO = Namespace(paths.AIDGO)
ISO = Namespace(paths.ISO5259)
AIAPR = Namespace(paths.AIAPR)
TAIR = Namespace(paths.TAIR)

ELI_AI_ACT = URIRef("https://eur-lex.europa.eu/eli/reg/2024/1689/oj")
MAPPING_PROCESS = AIDGO["MappingProcess_v2"]
LINKING_PROCESS = AIDGO["LexicalConceptLinking_v1"]
AUTHOR = AIDGO["KuruvillaGeorgeAiyankovil"]
MAPPING_DATE = "2026-04-14"

# Concept labels too generic to signal that a requirement *uses* the concept.
CONCEPT_STOPLIST = {"data", "organization"}


def read(name: str) -> list[dict]:
    with (paths.DATA / name).open(encoding="utf-8") as fh:
        return [{k: (v or "").strip() for k, v in r.items()} for r in csv.DictReader(fh)]


@dataclass
class Dataset:
    concepts: list[dict] = field(default_factory=lambda: read("iso_concepts.csv"))
    collections: list[dict] = field(default_factory=lambda: read("iso_collections.csv"))
    requirements: list[dict] = field(default_factory=lambda: read("iso_requirements.csv"))
    conj: list[dict] = field(default_factory=lambda: read("iso_conjunctive_requirements.csv"))
    legal: list[dict] = field(default_factory=lambda: read("legal_requirements.csv"))
    alignments: list[dict] = field(default_factory=lambda: read("alignments.csv"))


def coverage_status(types: list[str]) -> str:
    """Obligation-level aggregation rule (see aidgo:CoverageStatusScheme)."""
    if types and all(t == "CompletelySatisfies" for t in types):
        return "FullyCovered"
    if types and all(t == "NoAlignment" for t in types):
        return "NotCovered"
    return "PartiallyCovered"


def concept_links(ds: Dataset) -> list[tuple[str, str]]:
    """Deterministic longest-match lexical linking of requirement text to concept labels."""
    labels: list[tuple[str, str]] = []
    for c in ds.concepts:
        for lab in {c["label"], c["alt_label"]}:
            lab = re.sub(r"\s*\(.*?\)", "", lab).strip().lower()
            if lab and lab not in CONCEPT_STOPLIST:
                labels.append((lab, c["id"]))
    labels.sort(key=lambda x: (-len(x[0]), x[0]))
    links = set()
    for r in ds.requirements + ds.conj:
        text = (r["label"] + " " + r["definition"]).lower()
        taken = [False] * len(text)
        for lab, cid in labels:
            for m in re.finditer(r"(?<![a-z])" + re.escape(lab) + r"s?(?![a-z])", text):
                if not any(taken[m.start():m.end()]):
                    links.add((r["id"], cid))
                    for i in range(m.start(), m.end()):
                        taken[i] = True
    return sorted(links)


def build_graph(ds: Dataset | None = None) -> tuple[Graph, list[tuple[str, str]]]:
    ds = ds or Dataset()
    g = Graph()
    g.parse(paths.ONTOLOGY)
    for p, ns in paths.PREFIXES.items():
        g.bind(p, ns, override=True)
    en = lambda s: Literal(s, lang="en")  # noqa: E731

    # --- provenance agents and activities
    g.add((AUTHOR, RDF.type, PROV.Person))
    g.add((AUTHOR, RDFS.label, Literal("Kuruvilla George Aiyankovil")))
    src_law, src_iso = AIDGO["Source_EUAIAct_Art10"], AIDGO["Source_ISO5259_3"]
    g.add((src_law, RDF.type, PROV.Entity))
    g.add((src_law, RDFS.label, en("Regulation (EU) 2024/1689 (AI Act), Article 10")))
    g.add((src_law, RDFS.seeAlso, ELI_AI_ACT))
    g.add((src_iso, RDF.type, PROV.Entity))
    g.add((src_iso, RDFS.label, en("ISO/IEC FDIS 5259-3 Data quality management requirements and guidelines")))
    g.add((MAPPING_PROCESS, RDF.type, PROV.Activity))
    g.add((MAPPING_PROCESS, RDFS.label, en("AIDGO expert alignment of Article 10 to ISO/IEC 5259-3, v2")))
    g.add((MAPPING_PROCESS, PROV.startedAtTime, Literal(MAPPING_DATE + "T00:00:00Z", datatype=XSD.dateTime)))
    g.add((MAPPING_PROCESS, PROV.used, src_law))
    g.add((MAPPING_PROCESS, PROV.used, src_iso))
    g.add((MAPPING_PROCESS, PROV.wasAssociatedWith, AUTHOR))
    g.add((LINKING_PROCESS, RDF.type, PROV.Activity))
    g.add((LINKING_PROCESS, RDFS.label, en("Deterministic longest-match lexical linking of requirement text to ISO/IEC 5259 concept labels")))
    g.add((LINKING_PROCESS, PROV.used, src_iso))

    # --- concepts
    for c in ds.concepts:
        s = ISO[c["id"]]
        g.add((s, RDF.type, AIDGO.Concept))
        g.add((s, DCTERMS.identifier, Literal(c["id"])))
        g.add((s, SKOS.prefLabel, en(c["label"])))
        if c["alt_label"]:
            g.add((s, SKOS.altLabel, en(c["alt_label"])))
        if c["definition"]:
            g.add((s, SKOS.definition, en(c["definition"])))
        if c["broader"]:
            g.add((s, SKOS.broader, ISO[c["broader"]]))
        g.add((s, DCTERMS.source, Literal(c["source"])))
        if c["clause"]:
            g.add((s, AIDGO.clauseNumber, Literal(c["clause"])))

    # --- collections
    for c in ds.collections:
        s = ISO[c["id"]]
        g.add((s, RDF.type, AIDGO.RequirementCollection))
        g.add((s, DCTERMS.identifier, Literal(c["id"])))
        g.add((s, SKOS.prefLabel, en(c["label"])))
        if c["definition"]:
            g.add((s, SKOS.definition, en(c["definition"])))
        if c["broader"]:
            g.add((s, SKOS.broader, ISO[c["broader"]]))
        g.add((s, AIDGO.clauseNumber, Literal(c["clause"])))
        g.add((s, DCTERMS.source, Literal("ISO/IEC 5259-3")))

    # --- technical requirements (clause level and atomic)
    def tech(r: dict, atomic: bool) -> None:
        s = ISO[r["id"]]
        g.add((s, RDF.type, TAIR.Requirement))
        g.add((s, RDF.type, AIDGO.TechnicalRequirement))
        if atomic:
            g.add((s, RDF.type, AIDGO.ConjunctiveRequirement))
            g.add((s, RDF.type, TAIR.ConjuntiveRequirement))
            g.add((s, TAIR.decomposes, ISO[r["decomposes"]]))
        g.add((s, DCTERMS.identifier, Literal(r["id"])))
        g.add((s, SKOS.prefLabel, en(r["label"])))
        if r["definition"]:
            g.add((s, SKOS.definition, en(r["definition"])))
        if r["collection"]:
            g.add((s, SKOS.broader, ISO[r["collection"]]))
        g.add((s, DCTERMS.source, Literal("ISO/IEC 5259-3")))
        g.add((s, AIDGO.clauseNumber, Literal(r["clause"])))
        stage = stage_for_clause(r["clause"])
        if stage:
            g.add((s, AIDGO.dqmlcStage, AIDGO[stage]))

    for r in ds.requirements:
        tech(r, atomic=False)
    for r in ds.conj:
        tech(r, atomic=True)

    # --- legal requirements
    for l in ds.legal:
        s = AIAPR[l["id"]]
        g.add((s, RDF.type, TAIR.Requirement))
        g.add((s, RDF.type, AIDGO.LegalRequirement))
        g.add((s, DCTERMS.identifier, Literal(l["id"])))
        g.add((s, SKOS.prefLabel, en(l["label"])))
        g.add((s, SKOS.definition, en(l["definition"])))
        g.add((s, AIDGO.articleReference, Literal(l["article_ref"])))
        g.add((s, DCTERMS.source, ELI_AI_ACT))

    # --- alignment assertions
    per_obligation: dict[str, list[str]] = defaultdict(list)
    for a in ds.alignments:
        m = AIDGO[a["mapping_id"]]
        lr = AIAPR[a["legal_id"]]
        tr = ISO[a["tech_id"]] if a["tech_id"] else RDF.nil
        per_obligation[a["legal_id"]].append(a["alignment_type"])
        g.add((m, RDF.type, AIDGO.AlignmentAssertion))
        g.add((m, DCTERMS.identifier, Literal(a["mapping_id"])))
        g.add((m, AIDGO.legalRequirement, lr))
        g.add((m, AIDGO.technicalRequirement, tr))
        g.add((m, AIDGO.alignmentType, AIDGO[a["alignment_type"]]))
        g.add((m, AIDGO.alignmentBasis, AIDGO[a["alignment_basis"]]))
        if a["justification"]:
            g.add((m, AIDGO.alignmentJustification, en(a["justification"])))
        if a["gap"]:
            g.add((m, AIDGO.alignmentGap, en(a["gap"])))
        if a["legal_focus"]:
            g.add((m, AIDGO.legalFocus, en(a["legal_focus"])))
        if a["covered_cqs"]:
            g.add((m, AIDGO.coveredCQs, Literal(a["covered_cqs"])))
        g.add((m, AIDGO.validationStatus, AIDGO.ExpertValidated))
        g.add((m, PROV.wasGeneratedBy, MAPPING_PROCESS))
        g.add((m, PROV.generatedAtTime, Literal(MAPPING_DATE, datatype=XSD.date)))
        g.add((m, PROV.wasAttributedTo, AUTHOR))
        if a["tech_id"]:
            g.add((lr, AIDGO.alignedWith, tr))

    for lid, types in per_obligation.items():
        g.add((AIAPR[lid], AIDGO.coverageStatus, AIDGO[coverage_status(types)]))

    links = concept_links(ds)
    for rid, cid in links:
        g.add((ISO[rid], AIDGO.uses, ISO[cid]))
    return g, links


def _iri(u: str) -> str:
    return f"<{u}>"


def star_layer(ds: Dataset, links: list[tuple[str, str]]) -> str:
    """RDF 1.2 Turtle annotation layer: one annotated triple per alignment and concept link."""
    lines = ["", "#" * 78,
             "#  RDF 1.2 (RDF-star) annotation layer",
             "#  Each alignment assertion node is the reifier of its legal->technical triple:",
             "#    ?m rdf:reifies <<( ?legal aidgo:alignedWith ?tech )>>",
             "#  NoAlignment assertions have no technical requirement and therefore no triple.",
             "#" * 78, ""]
    for a in ds.alignments:
        if not a["tech_id"]:
            continue
        lines.append(
            f"{_iri(paths.AIAPR + a['legal_id'])} {_iri(paths.AIDGO + 'alignedWith')} "
            f"{_iri(paths.ISO5259 + a['tech_id'])} ~ {_iri(paths.AIDGO + a['mapping_id'])} {{| "
            f"{_iri(paths.AIDGO + 'alignmentType')} {_iri(paths.AIDGO + a['alignment_type'])} ; "
            f"{_iri(paths.AIDGO + 'alignmentBasis')} {_iri(paths.AIDGO + a['alignment_basis'])} ; "
            f"{_iri(paths.PROV + 'wasGeneratedBy')} {_iri(str(MAPPING_PROCESS))} |}} .")
    lines.append("")
    for rid, cid in links:
        lines.append(
            f"{_iri(paths.ISO5259 + rid)} {_iri(paths.AIDGO + 'uses')} {_iri(paths.ISO5259 + cid)} "
            f"{{| {_iri(paths.PROV + 'wasGeneratedBy')} {_iri(str(LINKING_PROCESS))} |}} .")
    return "\n".join(lines) + "\n"


def load_store(star: bool = True) -> ox.Store:
    """Load the built KG into an in-memory Oxigraph store (SPARQL 1.2 / SPARQL-star)."""
    store = ox.Store()
    path = paths.KG_STAR_TTL if star else paths.KG_TTL
    with path.open("rb") as fh:
        store.load(fh, format=ox.RdfFormat.TURTLE)
    return store


def main() -> None:
    ds = Dataset()
    g, links = build_graph(ds)
    paths.OUTPUT.mkdir(exist_ok=True)
    header = ("# AIDGO knowledge graph - GENERATED by `python -m aidgo_tools build` from data/*.csv.\n"
              "# Do not edit by hand. Ontology: ontology/aidgo.ttl  Docs: https://w3id.org/aidgo\n\n")
    plain = g.serialize(format="turtle")
    paths.KG_TTL.write_text(header + plain, encoding="utf-8")
    nt = sorted(l for l in g.serialize(format="nt").splitlines() if l.strip())
    (paths.OUTPUT / "aidgo_kg.nt").write_text("\n".join(nt) + "\n", encoding="utf-8")
    star = header.replace("knowledge graph", "knowledge graph + RDF 1.2 annotation layer") + plain + star_layer(ds, links)
    paths.KG_STAR_TTL.write_text(star, encoding="utf-8")
    n_star = len(load_store(star=True))  # parse check with a conformant RDF 1.2 parser
    print(f"  {paths.KG_TTL.relative_to(paths.ROOT)}: {len(g)} triples")
    print(f"  {paths.KG_STAR_TTL.relative_to(paths.ROOT)}: {n_star} triples (incl. reification layer)")
    print(f"  concept links (aidgo:uses): {len(links)}")


if __name__ == "__main__":
    main()
