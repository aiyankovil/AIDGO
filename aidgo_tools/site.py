"""Regenerate the data-driven parts of index.html and aidgo_knowledge_graph.html from data/*.csv.

What is regenerated (everything else in the pages is hand-written prose and left untouched):
  * the six data tables in index.html (concepts, collections, requirements, atomic requirements,
    obligations, alignments) and the alignment-distribution sentence
  * every number marked <span data-stat="...">
  * the embedded JSON datasets (ONTO_DATA in index.html, KG in aidgo_knowledge_graph.html)
  * the SPARQL presets (one per file in queries/) and the DQMLC stage table

    python -m aidgo_tools site            # rewrite the pages
    python -m aidgo_tools site --check    # exit 1 if the pages are out of date (used in CI)
"""

from __future__ import annotations

import html
import json
import re
import sys
from collections import Counter

from . import paths
from .build import Dataset, coverage_status
from .query import query_files

INDEX = paths.ROOT / "index.html"
EXPLORER = paths.ROOT / "aidgo_knowledge_graph.html"

TYPE_CLASS = {"CompletelySatisfies": "align-cs", "PartiallySatisfies": "align-ps",
              "RelatedTo": "align-rt", "ConflictsWith": "align-cw", "NoAlignment": "align-na"}
TYPE_LABEL = {"CompletelySatisfies": "Completely Satisfies", "PartiallySatisfies": "Partially Satisfies",
              "RelatedTo": "Related To", "ConflictsWith": "Conflicts With", "NoAlignment": "No Alignment"}

e = lambda s: html.escape(s or "", quote=True)  # noqa: E731
MUTED = '<span class="muted">—</span>'


def _short(s: str, n: int = 60) -> str:
    return s if len(s) <= n else s[: n - 1].rstrip() + "…"


def rows_concepts(ds: Dataset) -> str:
    out = []
    for c in ds.concepts:
        broader = f'<code class="link">{e(c["broader"])}</code>' if c["broader"] else MUTED
        out.append(f"""<tr data-source="{e(c['source'])}">
          <td><code class="iri" title="{e(paths.ISO5259 + c['id'])}">{e(c['id'])}</code></td>
          <td><strong>{e(c['label'])}</strong></td>
          <td class="clause-cell">{e(c['source'].replace('ISO/IEC ', ''))} §{e(c['clause'])}</td>
          <td class="def-cell">{e(c['definition'])}</td>
          <td>{broader}</td>
        </tr>""")
    return "\n".join(out)


def rows_collections(ds: Dataset) -> str:
    return "\n".join(f"""<tr>
          <td><code class="iri">{e(c['id'])}</code></td>
          <td>{e(c['clause'])}</td>
          <td><strong>{e(c['label'])}</strong></td>
          <td>{f'<code class="link">{e(c["broader"])}</code>' if c['broader'] else MUTED}</td>
        </tr>""" for c in ds.collections)


def rows_requirements(ds: Dataset) -> str:
    return "\n".join(f"""<tr>
          <td><code class="iri" title="{e(paths.ISO5259 + r['id'])}">{e(r['id'])}</code></td>
          <td>{e(r['clause'])}</td>
          <td><strong>{e(r['label'])}</strong></td>
          <td class="def-cell">{e(r['definition'])}</td>
          <td>{f'<code class="link">{e(r["collection"])}</code>' if r['collection'] else MUTED}</td>
        </tr>""" for r in ds.requirements)


def rows_conj(ds: Dataset) -> str:
    return "\n".join(f"""<tr>
          <td><code class="iri" title="{e(paths.ISO5259 + r['id'])}">{e(r['id'])}</code></td>
          <td>{e(r['clause'])}</td>
          <td><strong>{e(r['label'])}</strong></td>
          <td class="def-cell">{e(r['definition'])}</td>
          <td><code class="link">{e(r['decomposes'])}</code></td>
        </tr>""" for r in ds.conj)


def rows_legal(ds: Dataset) -> str:
    return "\n".join(f"""<tr>
          <td><code class="iri legal-iri" title="{e(paths.AIAPR + l['id'])}">{e(l['id'])}</code><div class="small-label">{e(l['article_ref'])}</div></td>
          <td><strong>{e(l['label'])}</strong></td>
          <td class="def-cell">{e(l['definition'])}</td>
        </tr>""" for l in ds.legal)


def rows_mappings(ds: Dataset) -> str:
    legal = {l["id"]: l for l in ds.legal}
    tech = {r["id"]: r for r in ds.requirements + ds.conj}
    out = []
    for a in ds.alignments:
        t = a["alignment_type"]
        llabel = a["legal_focus"] or legal[a["legal_id"]]["label"]
        if a["tech_id"]:
            tcell = (f'<code class="small-iri tech-iri">{e(a["tech_id"])}</code>'
                     f'<div class="small-label">{e(tech[a["tech_id"]]["label"])}</div>')
        else:
            tcell = '<code class="small-iri">rdf:nil</code>'
        gap = f'<div class="gap-note">{e(a["gap"])}</div>' if a["gap"] else ""
        out.append(f"""<tr class="map-row {TYPE_CLASS[t]}">
          <td><code class="small-iri">{e(a['mapping_id'])}</code></td>
          <td><code class="small-iri legal-iri">{e(a['legal_id'])}</code><div class="small-label" title="{e(llabel)}">{e(_short(llabel))}</div></td>
          <td>{tcell}</td>
          <td><span class="align-badge {TYPE_CLASS[t]}">{TYPE_LABEL[t]}</span></td>
          <td><span class="basis-pill">{e(a['alignment_basis'])}</span></td>
          <td class="just-cell">{e(a['justification'])}{gap}</td>
        </tr>""")
    return "\n".join(out)


def stats(ds: Dataset) -> dict[str, int]:
    from .build import build_graph
    types = Counter(a["alignment_type"] for a in ds.alignments)
    parts = Counter(c["source"] for c in ds.concepts)
    g, _ = build_graph(ds)
    s = {"concepts": len(ds.concepts), "collections": len(ds.collections),
         "requirements": len(ds.requirements), "conjreqs": len(ds.conj), "legal": len(ds.legal),
         "alignments": len(ds.alignments), "cs": types["CompletelySatisfies"],
         "ps": types["PartiallySatisfies"], "na": types["NoAlignment"], "triples": len(g)}
    s["nodes"] = s["concepts"] + s["collections"] + s["requirements"] + s["conjreqs"] + s["legal"]
    for i in range(1, 6):
        s[f"part{i}"] = parts[f"ISO/IEC 5259-{i}"]
    return s


def distribution_paragraph(ds: Dataset, s: dict[str, int]) -> str:
    per: dict[str, list[str]] = {}
    for a in ds.alignments:
        per.setdefault(a["legal_id"], []).append(a["alignment_type"])
    cov = Counter(coverage_status(v) for v in per.values())
    return (f'<p id="map-distribution">All alignment assertions between EU AI Act Article 10 obligations and '
            f'ISO/IEC 5259-3 requirements. <strong>Assertion level</strong> ({s["alignments"]} assertions): '
            f'<span class="align-badge align-cs">{s["cs"]} CompletelySatisfies</span> &nbsp;'
            f'<span class="align-badge align-ps">{s["ps"]} PartiallySatisfies</span>&nbsp; '
            f'<span class="align-badge align-na">{s["na"]} NoAlignment</span>. '
            f'<strong>Obligation level</strong> ({len(per)} obligations): '
            f'{cov["FullyCovered"]} fully covered, {cov["PartiallyCovered"]} partially covered, '
            f'{cov["NotCovered"]} not covered — an obligation is fully covered only if every assertion on it '
            f'is CompletelySatisfies (query <code>CQ-COV</code>).</p>')


def blob_index(ds: Dataset) -> dict:
    legal = {l["id"]: l for l in ds.legal}
    tech = {r["id"]: r for r in ds.requirements + ds.conj}
    return {
        "concepts": [{"id": c["id"], "clause": c["clause"], "alt": c["alt_label"], "label": c["label"],
                      "def": c["definition"], "broader": c["broader"], "source": c["source"]} for c in ds.concepts],
        "collections": [{"id": c["id"], "clause": c["clause"], "label": c["label"], "def": c["definition"],
                         "broader": c["broader"]} for c in ds.collections],
        "requirements": [{"id": r["id"], "clause": r["clause"], "label": r["label"], "def": r["definition"],
                          "broader": r["collection"]} for r in ds.requirements],
        "conjReqs": [{"id": r["id"], "clause": r["clause"], "label": r["label"], "def": r["definition"],
                      "broader": r["decomposes"], "decomposes": r["decomposes"], "collection": r["collection"]}
                     for r in ds.conj],
        "legalReqs": [{"id": l["id"], "label": l["label"], "def": l["definition"], "articleRef": l["article_ref"]}
                      for l in ds.legal],
        "mappings": [{"id": a["mapping_id"], "legalId": a["legal_id"],
                      "legalLabel": a["legal_focus"] or legal[a["legal_id"]]["label"],
                      "legalDef": a["legal_focus_text"] or legal[a["legal_id"]]["definition"],
                      "techId": a["tech_id"] or "rdf:nil",
                      "techLabel": tech[a["tech_id"]]["label"] if a["tech_id"] else "",
                      "techDef": tech[a["tech_id"]]["definition"] if a["tech_id"] else "",
                      "alignType": a["alignment_type"], "basis": a["alignment_basis"],
                      "justification": a["justification"], "gap": a["gap"], "cqs": a["covered_cqs"]}
                     for a in ds.alignments],
    }


def blob_explorer(ds: Dataset) -> dict:
    b = blob_index(ds)
    kinds = {"concepts": "concept", "collections": "collection", "requirements": "requirement",
             "conjReqs": "conjreq", "legalReqs": "legal"}
    for k, kind in kinds.items():
        for x in b[k]:
            x["type"] = kind
    for c in b["collections"]:
        c["collection"] = ""
    for r in b["requirements"]:
        r["collection"] = r["broader"]
    for m in b["mappings"]:
        for f in ("legalDef", "techDef", "cqs"):
            m.pop(f)
    return b


def replace_block(text: str, pattern: str, inner: str, what: str) -> str:
    new, n = re.subn(pattern, lambda m: m.group(1) + inner + m.group(len(m.groups())), text, count=1, flags=re.S)
    if n != 1:
        raise SystemExit(f"site: could not find {what} in page")
    return new


def set_json(text: str, var: str, obj) -> str:
    m = re.search(r"const " + var + r"\s*=\s*", text)
    if not m:
        raise SystemExit(f"site: const {var} not found")
    _, end = json.JSONDecoder().raw_decode(text[m.end():])
    blob = json.dumps(obj, ensure_ascii=False, separators=(",", ":"))
    blob = blob.replace("</", "<\\/")  # never close the <script> element from inside a string
    return text[: m.end()] + blob + text[m.end() + end:]


def render_index(text: str, ds: Dataset) -> str:
    s = stats(ds)
    text = replace_block(text, r'(<table id="concept-tbl">.*?<tbody>)(.*?)(\s*</tbody>)', rows_concepts(ds), "concept table")
    text = replace_block(text, r'(<table id="coll-tbl">.*?<tbody>)(.*?)(\s*</tbody>)', rows_collections(ds), "collection table")
    text = replace_block(text, r'(<table id="req-tbl">.*?<tbody>)(.*?)(\s*</tbody>)', rows_requirements(ds), "requirement table")
    text = replace_block(text, r'(<table id="conj-tbl">.*?<tbody>)(.*?)(\s*</tbody>)', rows_conj(ds), "conjunctive table")
    text = replace_block(text, r'(<table id="legal-tbl">.*?<tbody>)(.*?)(\s*</tbody>)', rows_legal(ds), "legal table")
    text = replace_block(text, r'(<tbody id="map-tbody">)(.*?)(\s*</tbody>)', rows_mappings(ds), "mapping table")
    text, n = re.subn(r'<p( id="map-distribution")?>All alignment assertions between.*?</p>',
                      lambda m: distribution_paragraph(ds, s), text, count=1, flags=re.S)
    assert n == 1, "distribution paragraph"
    text = re.sub(r'(<span data-stat="(\w+)">)[^<]*(</span>)',
                  lambda m: f'{m.group(1)}{s[m.group(2)]:,}{m.group(3)}' if m.group(2) == "triples"
                  else f'{m.group(1)}{s[m.group(2)]}{m.group(3)}', text)
    text = set_json(text, "ONTO_DATA", blob_index(ds))
    order = lambda p: ({"M": 0, "C": 1, "S": 2, "L": 3, "T": 4}.get(p.stem[3], 9), p.stem)  # noqa: E731
    presets = {p.stem: p.read_text(encoding="utf-8") for p in sorted(query_files(), key=order)}
    text = re.sub(r"const PRESETS = .*?;  /\* filled by aidgo_tools.site from queries/\*.rq \*/",
                  lambda m: "const PRESETS = " + json.dumps(presets, ensure_ascii=False).replace("</", "<\\/")
                  + ";  /* filled by aidgo_tools.site from queries/*.rq */", text, count=1, flags=re.S)
    text = re.sub(r"const DQMLC_STAGES = .*?;  /\* filled by aidgo_tools.site \*/",
                  lambda m: "const DQMLC_STAGES = " + json.dumps(paths.DQMLC_STAGES) + ";  /* filled by aidgo_tools.site */",
                  text, count=1)
    return text


def render_explorer(text: str, ds: Dataset) -> str:
    return set_json(text, "KG", blob_explorer(ds))


def main(argv: list[str]) -> int:
    ds = Dataset()
    stale = []
    for page, render in ((INDEX, render_index), (EXPLORER, render_explorer)):
        old = page.read_text(encoding="utf-8")
        new = render(old, ds)
        if new != old:
            stale.append(page.name)
            if "--check" not in argv:
                page.write_text(new, encoding="utf-8")
    if "--check" in argv:
        if stale:
            print("out of date (run `python -m aidgo_tools site`): " + ", ".join(stale))
            return 1
        print("site pages are up to date")
        return 0
    print("  regenerated: " + (", ".join(stale) if stale else "nothing changed"))
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
