import csv
from rdflib import Graph, Literal, Namespace, URIRef
from rdflib.namespace import RDF, RDFS, SKOS, DCTERMS, XSD

# Namespaces
AIDGO = Namespace("http://example.org/aidgo#")
TAIR  = Namespace("http://tair.adaptcentre.ie/ontologies/tair/")

# Create graph
g = Graph()
g.bind("aidgo", AIDGO)
g.bind("skos", SKOS)
g.bind("dct", DCTERMS)

# Input CSV
input_csv = "aidgo_alignment.csv"
rows = csv.DictReader(open(input_csv))

# Helper: create URI for requirements & clauses
def req_uri(req_id):
    return AIDGO[req_id]

def clause_uri(clause_id):
    return AIDGO[clause_id]

# Helper: mapping alignment types to URIs
ALIGN_MAP = {
    "CompletelySatisfies": AIDGO.CompletelySatisfies,
    "PartiallySatisfies": AIDGO.PartiallySatisfies,
    "ConflictsWith": AIDGO.ConflictsWith,
    "DefinitionDifference": AIDGO.DefinitionDifference
}

# Process rows
for row in rows:
    req_id = row["Requirement"]
    clause_id = row["Clause"]

    req = req_uri(req_id)
    clause = clause_uri(clause_id)

    # Create requirement concept
    g.add((req, RDF.type, AIDGO.RegulatoryRequirement))
    if row.get("skos:prefLabel"):
        g.add((req, SKOS.prefLabel, Literal(row["skos:prefLabel"], lang="en")))
    if row.get("skos:definition"):
        g.add((req, SKOS.definition, Literal(row["skos:definition"], lang="en")))

    # Create clause concept
    g.add((clause, RDF.type, AIDGO.TechnicalClause))

    # Create alignment node
    alignment_node = AIDGO[f"Align_{req_id}_{clause_id}"]
    g.add((alignment_node, RDF.type, AIDGO.Alignment))
    g.add((alignment_node, AIDGO.regulatoryRequirement, req))
    g.add((alignment_node, AIDGO.technicalClause, clause))

    # Add alignment type
    if row["AlignmentType"] in ALIGN_MAP:
        g.add((alignment_node, AIDGO.alignmentType, ALIGN_MAP[row["AlignmentType"]]))

    # RDF-Star provenance triple
    if row.get("Rationale"):
        embedded_triple = g.rdf_star_triple(
            (alignment_node, AIDGO.alignmentType, ALIGN_MAP[row["AlignmentType"]])
        )
        g.add((embedded_triple, AIDGO.rationale, Literal(row["Rationale"], lang="en")))

# Save output
g.serialize("aidgo_output.ttl", format="turtle-star")
print("AIDGO RDF-Star graph generated successfully!")
