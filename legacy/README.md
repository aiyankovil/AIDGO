# Legacy (v1) material — superseded

Kept so that links and earlier publications remain traceable. Nothing here is used by the v2 pipeline.

| Path | What it was | Superseded by |
|---|---|---|
| `mapping.py`, `ontologyGenerator.py` | v1 CSV → RDF-star generators. They did not run: `Graph.rdf_star_triple` does not exist in rdflib, and the input CSVs were never committed. | `aidgo_tools/build.py` |
| `Readme.md` | v1 README for the generators | top-level `README.md` |
| `sparql-v1/` | v1 queries (`http://w3id.org/aidgo#`, `aidgo:Alignment`, `aidgo:regulatoryRequirement`) | `queries/*.rq` |
| `mapping-v1/` | early SKOS files (`example.org` / `example.com` namespaces, DefinitionDifference and NoMapping types) | `ontology/aidgo.ttl`, `output/aidgo_kg.ttl` |
| `mappingAIDGO_v1.xlsx` | 10-row v1 alignment sheet | `data/alignments.csv` |
| `index_old.html`, `indexV1.html`, `MyStyle.css` | earlier documentation pages (`indexV1.html` uses the deprecated `aidgo:NoMatching`) | `index.html` |

v1 → v2 term changes: `aidgo:NoMatching`/`aidgo:NoMapping` → `aidgo:NoAlignment`; `aidgo:DefinitionDifference` → `aidgo:PartiallySatisfies` with a basis; `aidgo:Alignment` → `aidgo:AlignmentAssertion`; `aidgo:regulatoryRequirement`/`aidgo:technicalClause` → `aidgo:legalRequirement`/`aidgo:technicalRequirement`. The deprecated names stay declared in the ontology with `owl:deprecated true` and `dct:isReplacedBy`.
