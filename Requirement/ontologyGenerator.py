import pandas as pd
from rdflib import Graph, Literal, Namespace
from rdflib.namespace import RDF, SKOS

# Namespaces
AIDGO = Namespace("http://example.org/aidgo#")

# Input CSV files
REQ_CSV = "article10_requirements.csv"
ISO_CSV = "iso5259_clauses.csv"
ALIGN_CSV = "aidgo_alignment.csv"

# Output TTL file
OUTPUT_TTL = "aidgo_output.ttl"

# Load the CSVs
req_df = pd.read_csv(REQ_CSV)
iso_df = pd.read_csv(ISO_CSV)
align_df = pd.read_csv(ALIGN_CSV)

# Create RDF graph
g = Graph()
g.bind("aidgo", AIDGO)
g.bind("skos", SKOS)

# --- Helper functions ---

def req_uri(req_id):
    return AIDGO[req_id]

def clause_uri(clause_id):
    return AIDGO[clause_id]

def alignment_node(req_id, clause_id):
    return AIDGO[f"Align_{req_id}_{clause_id}"]

ALIGN_MAP = {
    "CompletelySatisfies": AIDGO.CompletelySatisfies,
    "PartiallySatisfies": AIDGO.PartiallySatisfies,
    "ConflictsWith": AIDGO.ConflictsWith,
    "DefinitionDifference": AIDGO.DefinitionDifference
}

# --- 1. Add Article 10 Requirements ---

for _, row in req_df.iterrows():
    req = req_uri(row["RequirementID"])

    g.add((req, RDF.type, AIDGO.RegulatoryRequirement))

    if "skos:prefLabel" in row and pd.notna(row["skos:prefLabel"]):
        g.add((req, SKOS.prefLabel, Literal(row["skos:prefLabel"], lang="en")))

    if "skos:definition" in row and pd.notna(row["skos:definition"]):
        g.add((req, SKOS.definition, Literal(row["skos:definition"], lang="en")))


# --- 2. Add ISO 5259 Clauses ---

for _, row in iso_df.iterrows():
    clause = clause_uri(row["ClauseID"])

    g.add((clause, RDF.type, AIDGO.TechnicalClause))

    if "skos:prefLabel" in row and pd.notna(row["skos:prefLabel"]):
        g.add((clause, SKOS.prefLabel, Literal(row["skos:prefLabel"], lang="en")))

    if "skos:definition" in row and pd.notna(row["skos:definition"]):
        g.add((clause, SKOS.definition, Literal(row["skos:definition"], lang="en")))


# --- 3. Add Alignments with RDF-Star Rationale ---

for _, row in align_df.iterrows():
    req_id = row["Requirement"]
    clause_id = row["Clause"]

    req = req_uri(req_id)
    clause = clause_uri(clause_id)

    align = alignment_node(req_id, clause_id)

    # Create alignment instance
    g.add((align, RDF.type, AIDGO.Alignment))
    g.add((align, AIDGO.regulatoryRequirement, req))
    g.add((align, AIDGO.technicalClause, clause))

    # Add alignment type
    align_type = ALIGN_MAP.get(row["AlignmentType"])
    if align_type:
        g.add((align, AIDGO.alignmentType, align_type))

        # Add RDF-Star provenance triple
        if "Rationale" in row and pd.notna(row["Rationale"]):
            embedded = g.rdf_star_triple((align, AIDGO.alignmentType, align_type))
            g.add((embedded, AIDGO.rationale, Literal(row["Rationale"], lang="en")))

    # Add SKOS metadata for requirements (optional duplicates from req CSV)
    if "skos:prefLabel" in row and pd.notna(row["skos:prefLabel"]):
        g.add((req, SKOS.prefLabel, Literal(row["skos:prefLabel"], lang="en")))

    if "skos:definition" in row and pd.notna(row["skos:definition"]):
        g.add((req, SKOS.definition, Literal(row["skos:definition"], lang="en")))


# --- Save output ---
g.serialize(destination=OUTPUT_TTL, format="turtle-star")
print(f"AIDGO RDF-Star ontology saved as {OUTPUT_TTL}")
