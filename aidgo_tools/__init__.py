"""AIDGO tooling: build, validate and query the AI Data Governance Ontology knowledge graph.

Pipeline (see README):  data/*.csv  ->  output/aidgo_kg.ttl (+ RDF-star layer)
                        -> SHACL validation -> competency questions -> site pages
"""

__version__ = "2.0.0"
