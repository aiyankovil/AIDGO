# AIDGO: AI Data Governance Ontology

AIDGO aligns the data-governance obligations of **Article 10 of the EU AI Act** (Regulation (EU) 2024/1689)
with the requirements of **ISO/IEC 5259-3** (data quality management for machine learning), as a knowledge graph.
Each alignment is typed (completely satisfies, partially satisfies, related to, conflicts with, no alignment),
with its basis, a justification, the documented gap and PROV-O provenance.

## AIDGO Compliance Explorer

Open `index.html` (also served at <https://w3id.org/aidgo>). It runs entirely in the browser: the graph is
loaded into an in-browser SPARQL engine (Oxigraph, WebAssembly) and every view is a SPARQL query.

- **Coverage**: Article 10 obligations against the life-cycle stages of ISO/IEC 5259-3, with gaps
- **Obligation**: legal text, its elements, and every alignment with what it does not guarantee and its provenance
- **Standard clause**: which obligations a clause supports
- **SPARQL**: query editor with six competency questions; download the graph

## Contents

| File | What it is |
|---|---|
| `index.html` | AIDGO Compliance Explorer (single file, no server) |
| `aidgo_public.ttl` | Public knowledge graph (Turtle) |
| `queries.json` | The six competency questions in SPARQL |
| `scripts/build_public_graph.py` | Builds the public graph from the full graph, removing ISO/IEC text, with a leak check |
| `scripts/obligation_elements.json` | Decomposition of each Article 10 obligation into elements |

## What is not included

ISO/IEC standards are copyrighted. This release contains **no ISO/IEC requirement text or term definitions**:
only identifiers, clause numbers, short labels, structure, life-cycle stages and the alignment assertions
(whose justifications are the annotators' own words). Article 10 is public law and is included.
Alignments are expert judgments, not legal advice or evidence of conformity.

## Licence

CC BY 4.0 (see `LICENSE`).

## Cite

Kuruvilla George Aiyankovil and Dave Lewis. 2026. AIDGO: A FAIR Ontology for Aligning the EU AI Act
Data Governance Obligations with ISO/IEC Technical Standards. In *Proceedings of SEMANTiCS 2026
(Posters and Demos)*, Ghent, Belgium.

ADAPT Centre, School of Computer Science and Statistics, Trinity College Dublin.
