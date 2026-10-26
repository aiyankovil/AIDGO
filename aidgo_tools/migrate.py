"""One-off migration: extract the curated AIDGO dataset into data/*.csv.

Until v2.0 the curated dataset (17 Article 10 obligations, 71 clause-level ISO/IEC 5259-3
requirements, 119 atomic ConjunctiveRequirements, 74 concepts, 51 collections and the 24
expert alignment assertions) existed only as a JSON blob (``ONTO_DATA``) embedded in
index.html. This script reproduces data/*.csv from that blob so the provenance of the CSVs
is auditable:

    git show 895429c:index.html > /tmp/index_v1.html
    git show 895429c:aidgo_knowledge_graph.html > /tmp/kg_v1.html
    python -m aidgo_tools.migrate /tmp/index_v1.html /tmp/kg_v1.html [arellano.xlsx]

The index.html blob is authoritative for all text (the explorer's copy truncates text at 200
characters); the explorer blob (``KG``) is the only source of the requirement -> collection
links, which the index.html blob leaves empty.

It also converts M. Arellano's independent coding of ISO/IEC 5259-3 into
data/coding/arellano_5259-3_*.csv. Verbatim ISO text columns are deliberately NOT copied
(ISO/IEC 5259-3 is copyrighted; only identifiers, clause numbers and concept links are kept).
"""

from __future__ import annotations

import csv
import json
import re
import sys
from pathlib import Path

from .paths import CODING, DATA

# Article 10 paragraph / point for each atomic legal requirement.
# Art. 10(2) points: (a) design choices ... (h) data gaps. Point (g) (bias detection,
# prevention and mitigation measures) has no atomic requirement in the v2 dataset.
ARTICLE_REF = {
    "AiaPrReq_10.1": "Art. 10(1)",
    "AiaPrReq_10.2_1": "Art. 10(2)",
    "AiaPrReq_10.2_2": "Art. 10(2)(a)",
    "AiaPrReq_10.2_3": "Art. 10(2)(b)",
    "AiaPrReq_10.2_4": "Art. 10(2)(c)",
    "AiaPrReq_10.2_5": "Art. 10(2)(d)",
    "AiaPrReq_10.2_6": "Art. 10(2)(e)",
    "AiaPrReq_10.2_7": "Art. 10(2)(f)",
    "AiaPrReq_10.2_8": "Art. 10(2)(h)",
    "AiaPrReq_10.3_1": "Art. 10(3)",
    "AiaPrReq_10.3_2": "Art. 10(3)",
    "AiaPrReq_10.4": "Art. 10(4)",
    "AiaPrReq_10.5": "Art. 10(5)",
    "AiaPrReq_10.5_a": "Art. 10(5)(a)",
    "AiaPrReq_10.5_b": "Art. 10(5)(b)",
    "AiaPrReq_10.5_e": "Art. 10(5)(e)",
    "AiaPrReq_10.6": "Art. 10(6)",
}

# Arellano's clause numbers -> ISO/IEC FDIS 5259-3 numbering used by AIDGO.
# Established by comparing the coded paragraph text with the FDIS table of contents.
ARELLANO_CROSSWALK = {
    "6.1": "",          # text is from ISO/IEC 5259-2 (data quality measures), not 5259-3
    "6.2": "6.3.2",     # data quality culture (FDIS 6.3.2 a-h)
    "7.3.1": "7.3.1.1", # data motivation and conceptualization
    "8.3.1": "8.3.1.1", # verification and validation, general
}


def write_csv(path: Path, header: list[str], rows: list[dict]) -> None:
    if path.exists() and "--force" not in sys.argv:
        raise SystemExit(f"{path} exists; data/ is edited directly now. Re-run with --force to overwrite.")
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", newline="", encoding="utf-8") as fh:
        w = csv.DictWriter(fh, fieldnames=header, lineterminator="\n")
        w.writeheader()
        for r in rows:
            w.writerow({k: ("" if r.get(k) is None else r.get(k)) for k in header})
    print(f"  wrote {path.relative_to(DATA.parent)} ({len(rows)} rows)")


def extract_onto_data(html_path: Path, var: str = "ONTO_DATA") -> dict:
    text = html_path.read_text(encoding="utf-8")
    m = re.search(r"const " + var + r"\s*=\s*", text)
    if not m:
        raise SystemExit("ONTO_DATA blob not found")
    obj, _ = json.JSONDecoder().raw_decode(text[m.end():])
    return obj


def migrate_curated(d: dict, kg: dict) -> None:
    req_coll = {r["id"]: r.get("collection", "") for r in kg["requirements"]}
    write_csv(DATA / "iso_concepts.csv",
              ["id", "label", "alt_label", "definition", "broader", "source", "clause"],
              [{"id": c["id"], "label": c["label"], "alt_label": c.get("alt"),
                "definition": c.get("def"), "broader": c.get("broader"),
                "source": c.get("source"), "clause": c.get("clause")} for c in d["concepts"]])
    write_csv(DATA / "iso_collections.csv",
              ["id", "label", "definition", "broader", "clause"],
              [{"id": c["id"], "label": c["label"], "definition": c.get("def"),
                "broader": c.get("broader"), "clause": c.get("clause")} for c in d["collections"]])
    write_csv(DATA / "iso_requirements.csv",
              ["id", "label", "definition", "collection", "clause"],
              [{"id": r["id"], "label": r["label"], "definition": r.get("def"),
                "collection": r.get("broader") or req_coll.get(r["id"]), "clause": r.get("clause")}
               for r in d["requirements"]])
    write_csv(DATA / "iso_conjunctive_requirements.csv",
              ["id", "label", "definition", "decomposes", "collection", "clause"],
              [{"id": r["id"], "label": r["label"], "definition": r.get("def"),
                "decomposes": r.get("decomposes"), "collection": r.get("collection"),
                "clause": r.get("clause")} for r in d["conjReqs"]])

    legal = {l["id"]: l for l in d["legalReqs"]}
    write_csv(DATA / "legal_requirements.csv",
              ["id", "label", "definition", "article_ref"],
              [{"id": l["id"], "label": l["label"], "definition": l.get("def"),
                "article_ref": ARTICLE_REF[l["id"]]} for l in d["legalReqs"]])

    rows = []
    for m in d["mappings"]:
        lr = legal[m["legalId"]]
        focus = m.get("legalLabel") if m.get("legalLabel") != lr["label"] else ""
        focus_text = m.get("legalDef") if m.get("legalDef") and m.get("legalDef") != lr.get("def") else ""
        rows.append({
            "mapping_id": m["id"], "legal_id": m["legalId"],
            "tech_id": "" if m["techId"] == "rdf:nil" else m["techId"],
            "alignment_type": m["alignType"], "alignment_basis": m["basis"],
            "legal_focus": focus, "legal_focus_text": focus_text,
            "justification": m.get("justification"), "gap": m.get("gap"),
            "covered_cqs": m.get("cqs"),
        })
    write_csv(DATA / "alignments.csv",
              ["mapping_id", "legal_id", "tech_id", "alignment_type", "alignment_basis",
               "legal_focus", "legal_focus_text", "justification", "gap", "covered_cqs"], rows)


def migrate_arellano(xlsx: Path) -> None:
    import openpyxl
    wb = openpyxl.load_workbook(xlsx, data_only=True)
    req_rows, current = [], None
    for r in wb["ISO5259-3-req"].iter_rows(min_row=2, values_only=True):
        if not r[2]:
            continue
        if r[0]:
            current = str(r[0]).replace("ISO5259-3-", "")
        req_rows.append({
            "id": r[2], "coded_clause": current,
            "fdis_clause": ARELLANO_CROSSWALK.get(current, current),
            "norm_level": r[4], "related_category": r[6],
            "related_concepts": " ".join(str(r[7] or "").split()),
        })
    write_csv(CODING / "arellano_5259-3_requirements.csv",
              ["id", "coded_clause", "fdis_clause", "norm_level", "related_category",
               "related_concepts"], req_rows)
    con_rows = [{"id": r[0], "label": r[1], "subclass_of": r[2], "broader": r[4],
                 "related": r[5]}
                for r in wb["ISO5259-3-con"].iter_rows(min_row=2, values_only=True) if r[0]]
    write_csv(CODING / "arellano_5259-3_concepts.csv",
              ["id", "label", "subclass_of", "broader", "related"], con_rows)


def main(argv: list[str]) -> None:
    argv = [a for a in argv if a != "--force"]
    if len(argv) < 3:
        raise SystemExit(__doc__)
    migrate_curated(extract_onto_data(Path(argv[1])), extract_onto_data(Path(argv[2]), "KG"))
    if len(argv) > 3:
        migrate_arellano(Path(argv[3]))


if __name__ == "__main__":
    main(sys.argv)
