"""Repository paths, namespaces and controlled vocabularies shared by every module."""

from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
DATA = ROOT / "data"
CODING = DATA / "coding"
ONTOLOGY = ROOT / "ontology" / "aidgo.ttl"
SHAPES = ROOT / "shapes" / "aidgo-shapes.ttl"
QUERIES = ROOT / "queries"
OUTPUT = ROOT / "output"

KG_TTL = OUTPUT / "aidgo_kg.ttl"            # plain RDF 1.1 (ontology + data) - any tool
KG_STAR_TTL = OUTPUT / "aidgo_kg_star.ttl"  # KG + RDF 1.2 / RDF-star annotation layer

# Namespaces (kept identical to those documented on https://w3id.org/aidgo)
AIDGO = "https://w3id.org/aidgo#"
ISO5259 = "https://w3id.org/aidgo/iso5259#"
AIAPR = "https://w3id.org/euaiact/art10#"
TAIR = "https://w3id.org/tair#"
RDF = "http://www.w3.org/1999/02/22-rdf-syntax-ns#"
RDFS = "http://www.w3.org/2000/01/rdf-schema#"
OWL = "http://www.w3.org/2002/07/owl#"
XSD = "http://www.w3.org/2001/XMLSchema#"
SKOS = "http://www.w3.org/2004/02/skos/core#"
DCT = "http://purl.org/dc/terms/"
PROV = "http://www.w3.org/ns/prov#"

PREFIXES = {
    "aidgo": AIDGO, "iso5259": ISO5259, "aiapr": AIAPR, "tair": TAIR,
    "rdf": RDF, "rdfs": RDFS, "owl": OWL, "xsd": XSD, "skos": SKOS,
    "dct": DCT, "prov": PROV,
}

SPARQL_PREFIXES = "\n".join(f"PREFIX {k}: <{v}>" for k, v in PREFIXES.items()) + "\n"

# The five-type alignment taxonomy and the five alignment bases.
ALIGNMENT_TYPES = ["CompletelySatisfies", "PartiallySatisfies", "RelatedTo",
                   "ConflictsWith", "NoAlignment"]
ALIGNMENT_BASES = ["SemanticEquivalence", "FunctionalEquivalence",
                   "ConceptualCoverage", "ScopeOverlap", "GapIdentified"]

# ISO/IEC 5259-3 Data Quality Management Life Cycle stages, keyed by FDIS clause prefix.
# Longest prefix wins (see stage_for_clause).
DQMLC_STAGES = {
    "6": "OrganisationalStage",
    "7.2": "LifeCycleGeneralStage",
    "7.3.1": "MotivationStage",
    "7.3.2": "SpecificationStage",
    "7.3.3": "PlanningStage",
    "7.3.4": "AcquisitionStage",
    "7.3.5": "PreprocessingStage",
    "7.3.6": "AugmentationStage",
    "7.3.7": "ProvisioningStage",
    "7.3.8": "DecommissioningStage",
    "8": "HorizontalProcessStage",
    "9": "SupplyChainStage",
    "10": "ToolManagementStage",
    "11": "DependencyManagementStage",
    "12": "ProjectSpecificStage",
}


def stage_for_clause(clause: str) -> str | None:
    """Return the DQMLC stage local name for an ISO/IEC 5259-3 clause number."""
    clause = (clause or "").strip()
    best = None
    for prefix in DQMLC_STAGES:
        if clause == prefix or clause.startswith(prefix + "."):
            if best is None or len(prefix) > len(best):
                best = prefix
    return DQMLC_STAGES[best] if best else None
