"""Build the PUBLIC AIDGO graph for the demo: everything in the KG except copyrighted ISO/IEC text.
Removes skos:definition / skos:altLabel from ISO requirements, atomic requirements, ISO concepts and
requirement collections; keeps identifiers, clause numbers, short labels, structure, life-cycle stages,
Article 10 text (public law), the alignment assertions with justification/gap/provenance, and adds the
obligation-element decompositions.  Usage: python3 08_public_graph.py <kg.ttl> <metadata.ttl> <elements.json> <out.ttl>"""
import sys, json, rdflib
from rdflib import RDF, RDFS, Literal, URIRef, Namespace
from rdflib.namespace import SKOS, DCTERMS, XSD

kg, meta, elems, out = sys.argv[1:5]
A = Namespace("https://w3id.org/aidgo#"); T = Namespace("https://w3id.org/tair#")
AIA = Namespace("https://w3id.org/aidgo/aiact#")
g = rdflib.Graph(); g.parse(kg); g.parse(meta)
for p, n in g.namespaces(): pass
ISO_CLASSES = [T.Requirement, T.ConjuntiveRequirement, A.Concept, A.RequirementCollection]
removed = 0
for cls in ISO_CLASSES:
    for s in set(g.subjects(RDF.type, cls)):
        for p in (SKOS.definition, SKOS.altLabel, RDFS.comment):
            for o in list(g.objects(s, p)):
                g.remove((s, p, o)); removed += 1

ART = {"10.1": "10(1)", "10.2_1": "10(2)", "10.2_2": "10(2)(a)", "10.2_3": "10(2)(b)", "10.2_4": "10(2)(c)",
       "10.2_5": "10(2)(d)", "10.2_6": "10(2)(e)", "10.2_7": "10(2)(f)", "10.2_8": "10(2)(h)", "10.3_1": "10(3), 1st sentence",
       "10.3_2": "10(3), 2nd sentence", "10.4": "10(4)", "10.5": "10(5)", "10.5_a": "10(5)(a)", "10.5_b": "10(5)(b)",
       "10.5_e": "10(5)(e)", "10.6": "10(6)"}
E = json.load(open(elems))["obligations"]
legal = {str(s).split("#")[-1].split("/")[-1]: s for s in g.subjects(RDF.type, A.LegalRequirement)}
g.bind("aidgo", A); g.bind("tair", T)
n_el = 0
for lid, s in legal.items():
    g.add((s, A.articleReference, Literal("Art. " + ART[lid.replace("AiaPrReq_", "")])))
    for e in E.get(lid, {}).get("elements", []):
        en = URIRef(str(s) + "_" + e["id"])
        g.add((en, RDF.type, A.ObligationElement)); g.add((s, A.hasElement, en))
        g.add((en, A.elementRole, Literal(e["role"]))); g.add((en, A.isCoreElement, Literal(bool(e["core"]))))
        g.add((en, SKOS.definition, Literal(e["text"], lang="en"))); n_el += 1
g.add((A.ObligationElement, RDF.type, URIRef("http://www.w3.org/2002/07/owl#Class")))
g.add((A.ObligationElement, RDFS.label, Literal("Obligation element", lang="en")))
# FIXES for the public release (documented):
PROV = Namespace("http://www.w3.org/ns/prov#")
# (a) generatedAtTime in the build output is the rebuild timestamp, not the date the expert made the assertion
for a in set(g.subjects(RDF.type, A.AlignmentAssertion)):
    for o in list(g.objects(a, PROV.generatedAtTime)): g.remove((a, PROV.generatedAtTime, o))
# (b) Art. 10(2)(f): use the wording of the Regulation (the stored text omitted 'fundamental rights')
f = legal.get("AiaPrReq_10.2_7")
if f is not None:
    for o in list(g.objects(f, SKOS.definition)): g.remove((f, SKOS.definition, o))
    g.add((f, SKOS.definition, Literal("[Data governance and management practices shall concern in particular] examination in view of possible biases that are likely to affect the health and safety of persons, have a negative impact on fundamental rights or lead to discrimination prohibited under Union law, especially where data outputs influence inputs for future operations.", lang="en")))
# (c) justification for 10(2)(f) x 8.3.4.2 misdescribed the clause: 8.3.4.2 does not mention bias
for a in set(g.subjects(RDF.type, A.AlignmentAssertion)):
    for o in list(g.objects(a, A.alignmentJustification)):
        if "8.3.4 requires risk assessment covering data quality risks including bias" in str(o):
            g.remove((a, A.alignmentJustification, o))
            g.add((a, A.alignmentJustification, Literal(str(o).replace("ISO 5259-3 \u00a78.3.4 requires risk assessment covering data quality risks including bias.", "").replace("ISO 5259-3 §8.3.4 requires risk assessment covering data quality risks including bias.", "ISO 5259-3 §8.3.4.2 requires a documented assessment of risks to data quality and processes to minimise them.").strip(), lang="en")))
ds = A.AIDGO_KG
g.add((ds, DCTERMS.description, Literal("Public release: ISO/IEC requirement text is not included (copyright); identifiers, clause numbers, labels and structure only.", lang="en")))
g.add((ds, DCTERMS.license, URIRef("https://creativecommons.org/licenses/by/4.0/")))  # dct_license
g.serialize(out, format="turtle")
# leak check: no literal longer than 25 words on ISO nodes
iso_nodes = {s for cls in ISO_CLASSES for s in g.subjects(RDF.type, cls)}
long_lits = [(s, p, o) for s in iso_nodes for p, o in g.predicate_objects(s) if isinstance(o, Literal) and len(str(o).split()) > 12]
print(f"triples {len(g)}  removed ISO text literals {removed}  elements {n_el}  long literals left on ISO nodes {len(long_lits)}")
for x in long_lits[:5]: print("  ", x)
