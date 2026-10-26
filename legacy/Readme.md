AIDGO (AI Data Governance Ontology) is a semantic alignment framework linking legal requirements from the EU AI Act (Article 10) with technical clauses from ISO/IEC 5259 (Data Quality for Analytics & AI). This repository provides CSV templates, an RDF-Star generator, an alignment suggestion script, and SPARQL queries for evaluating compliance.

Repository Structure

data/
article10_requirements.csv
iso5259_clauses.csv
aidgo_alignment.csv

scripts/
merge_to_aidgo_rdfstar.py
suggest_alignments.py

output/
aidgo_output.ttl

examples/
example_alignment.ttl
example_queries.rq

README.txt or README.md

Installation

Prerequisites:
Python 3.9 or higher
rdflib 6.2 or higher (must support RDF-Star)
pandas 1.3 or higher
scikit-learn 1.0 or higher

Install requirements:
pip install rdflib pandas scikit-learn

Input Data Files

All inputs are stored in the data directory.

2.1 Article 10 Requirements (article10_requirements.csv)

This file contains atomic regulatory requirements extracted from AI Act Article 10.

Required columns:
RequirementID — unique ID such as A10-2-Req1
skos:prefLabel — short human-readable label
skos:definition — requirement definition

Example rows:
RequirementID, skos:prefLabel, skos:definition
A10-2-Req1, Data quality requirements, Datasets must be relevant, representative, free of errors and complete.
A10-3-Req1, Bias mitigation, Bias must be detected, assessed, and mitigated.

2.2 ISO 5259 Clauses (iso5259_clauses.csv)

This file contains atomic clauses extracted from ISO/IEC 5259.

Required columns:
ClauseID — unique ID such as ISO5259-1-6.2
skos:prefLabel — clause title
skos:definition — description of clause

2.3 Alignment Mapping (aidgo_alignment.csv)

This file expresses the mapping between Article 10 requirements and ISO clauses.

Required columns:
Requirement — requirement ID from article10_requirements.csv
Clause — clause ID from iso5259_clauses.csv
AlignmentType — one of the following:
CompletelySatisfies
PartiallySatisfies
ConflictsWith
DefinitionDifference
Rationale — explanation for why the alignment applies

Optional columns:
skos:prefLabel — requirement label (overrides requirement CSV)
skos:definition — requirement definition (overrides requirement CSV)

Generating the AIDGO RDF-Star Ontology

Run the main script:
python scripts/merge_to_aidgo_rdfstar.py

This script:
Loads all three CSV files
Creates requirement and clause nodes
Creates alignment instances
Applies alignment types
Adds rationale using RDF-Star embedded triples
Outputs ontology to output/aidgo_output.ttl

RDF-Star Output Example

Example structure of generated triples:

Alignment instance:
aidgo:Align_A10-2-Req1_ISO5259-1-6.2
type Alignment
regulatoryRequirement A10-2-Req1
technicalClause ISO5259-1-6.2
alignmentType PartiallySatisfies

RDF-Star rationale triple:
<< Align_A10-2-Req1_ISO5259-1-6.2 alignmentType PartiallySatisfies >>
rationale "Explanation goes here"
