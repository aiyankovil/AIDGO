# AIDGO source data

These CSVs are the single source of truth for the knowledge graph. They were produced from the
v1 site's embedded dataset by `aidgo_tools/migrate.py` (see its docstring for the exact command)
and are edited directly from now on; `migrate.py` refuses to overwrite them unless given `--force`. After any change run `make && make test`.

All files are UTF-8, comma-separated, with a header row. Empty cell = no value.

## legal_requirements.csv — EU AI Act Article 10 atomic obligations
| column | meaning |
|---|---|
| id | local name in `https://w3id.org/euaiact/art10#` |
| label | short label |
| definition | the atomic obligation; bracketed text is the shared lead-in |
| article_ref | `Art. 10(p)` or `Art. 10(p)(x)` — validated by SHACL |

Art. 10(2)(g) (measures to detect, prevent and mitigate biases) and Art. 10(5)(c), (d), (f) have
no atomic obligation in the v2 dataset.

## iso_requirements.csv — ISO/IEC 5259-3 clause-level requirements (`tair:Requirement`)
`id`, `label`, `definition` (full compound SHALL text), `collection` (id in iso_collections.csv), `clause` (FDIS numbering).

## iso_conjunctive_requirements.csv — atomic requirements (`aidgo:ConjunctiveRequirement`)
`id`, `label`, `definition` (bracket-context form), `decomposes` (parent id in iso_requirements.csv),
`collection`, `clause` (must equal the parent's clause — SHACL-checked).

## iso_collections.csv — clause tree (`aidgo:RequirementCollection`)
`id`, `label`, `definition`, `broader` (parent collection), `clause`.

## iso_concepts.csv — ISO/IEC 5259-1…5 terms (`aidgo:Concept`)
`id`, `label`, `alt_label`, `definition`, `broader`, `source` (`ISO/IEC 5259-n`), `clause`.

## alignments.csv — expert alignment assertions (`aidgo:AlignmentAssertion`)
| column | meaning |
|---|---|
| mapping_id | assertion id (local name in `https://w3id.org/aidgo#`) |
| legal_id | obligation id |
| tech_id | requirement or atomic-requirement id; **empty for NoAlignment** (becomes `rdf:nil`) |
| alignment_type | CompletelySatisfies, PartiallySatisfies, RelatedTo, ConflictsWith, NoAlignment |
| alignment_basis | SemanticEquivalence, FunctionalEquivalence, ConceptualCoverage, ScopeOverlap, GapIdentified |
| legal_focus | when the assertion targets one element of the obligation, that element (else empty) |
| legal_focus_text | the wording of that element (else empty); becomes `aidgo:legalFocusText` |
| justification | why the type was assigned (required unless NoAlignment) |
| gap | what is left unaddressed (required for PartiallySatisfies and NoAlignment) |
| covered_cqs | competency questions the assertion helps answer |

## coding/ — independent coding of ISO/IEC 5259-3 by M. Arellano
`arellano_5259-3_requirements.csv`: `id`, `coded_clause` (as coded), `fdis_clause` (mapped to FDIS
numbering; empty = not a 5259-3 clause), `norm_level`, `related_category`, `related_concepts`.
`arellano_5259-3_concepts.csv`: the coder's concept register. ISO text was intentionally not copied.
Used only by `python -m aidgo_tools agreement`.
