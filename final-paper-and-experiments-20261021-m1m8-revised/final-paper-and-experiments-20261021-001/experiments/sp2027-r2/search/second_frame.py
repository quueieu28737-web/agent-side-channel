"""B4 (partial): a second retrieval frame over the arXiv API, plus a screening queue.

What this does: runs a fixed, pre-written query set (QUERIES below) that targets
the vocabulary the first frame missed ("prompt leakage", "keylogging", "timing
attack", "fingerprinting", "traffic analysis") over title+abstract, deduplicates,
matches returns to the 82-family index and to the 565-record first frame, and
writes a screening queue of unmatched returns.

What this does NOT do: estimate field-wide recall. The queries were written by the
corpus authors with knowledge of the first frame's misses, so the two frames are
not independent and a Lincoln-Petersen/Chapman estimate would be biased. That
estimate needs (a) a second searcher who has not seen the corpus and (b) eligibility
screening of the queue by blinded coders (see ../coding/CODEBOOK.md).

  python -B second_frame.py            # ~1 min; 3 s between API requests (arXiv policy)
"""
import csv
import json
import re
import time
import urllib.parse
import urllib.request
import xml.etree.ElementTree as ET
from pathlib import Path

HERE = Path(__file__).resolve().parent
SU = HERE.parents[2] / "evidence/retained-release007/search-update"
DATE = "submittedDate:[202001010000 TO 202610212359]"
LLM = '(abs:"language model" OR abs:LLM OR abs:"AI agent" OR abs:"LLM agent" OR abs:chatbot)'
QUERIES = {
    "F2-01": f'{LLM} AND (abs:"side channel" OR abs:"side-channel" OR abs:"sidechannel")',
    "F2-02": f'{LLM} AND (abs:"prompt leakage" OR abs:"prompt stealing" OR abs:"prompt extraction") AND (abs:timing OR abs:cache OR abs:traffic)',
    "F2-03": f'{LLM} AND (abs:keylogging OR abs:"token length" OR abs:"packet length" OR abs:"encrypted traffic")',
    "F2-04": f'{LLM} AND (abs:"timing attack" OR abs:"timing leakage" OR abs:"timing side")',
    "F2-05": f'{LLM} AND (abs:"KV cache" OR abs:"KV-cache" OR abs:"prefix caching" OR abs:"prompt caching") AND (abs:leak OR abs:privacy OR abs:attack)',
    "F2-06": f'(abs:agent OR abs:agentic) AND (abs:fingerprinting OR abs:"traffic analysis" OR abs:"metadata leakage")',
    "F2-07": f'{LLM} AND (abs:"speculative decoding" OR abs:"mixture of experts" OR abs:"sparse attention") AND (abs:leak OR abs:"side channel")',
    "F2-08": f'{LLM} AND (abs:"electromagnetic" OR abs:"power side" OR abs:"GPU" ) AND abs:"side channel"',
    "F2-09": f'(abs:"browser agent" OR abs:"web agent" OR abs:"GUI agent") AND (abs:fingerprint OR abs:detection OR abs:humanization OR abs:leak)',
    "F2-10": f'{LLM} AND (abs:padding OR abs:"cover traffic" OR abs:obfuscation) AND (abs:traffic OR abs:"side channel")',
}


def fetch(q, start, n=100):
    url = "https://export.arxiv.org/api/query?" + urllib.parse.urlencode(
        {"search_query": f"({q}) AND {DATE}", "start": start, "max_results": n, "sortBy": "submittedDate"})
    with urllib.request.urlopen(url, timeout=60) as r:
        return ET.fromstring(r.read())


def norm(t):
    return re.sub(r"[^a-z0-9]+", "", re.sub(r"\{|\}", "", t.lower()))[:80]


def arxiv_id(s):
    m = re.search(r"(\d{4}\.\d{4,5})", s or "")
    return m.group(1) if m else None


def main():
    ns = {"a": "http://www.w3.org/2005/Atom"}
    hits, log = {}, []
    for qid, q in QUERIES.items():
        start, got = 0, 0
        while True:
            root = fetch(q, start); time.sleep(3)
            entries = root.findall("a:entry", ns)
            for e in entries:
                aid = arxiv_id(e.find("a:id", ns).text)
                h = hits.setdefault(aid, {"arxiv_id": aid, "title": " ".join(e.find("a:title", ns).text.split()),
                                          "published": e.find("a:published", ns).text[:10],
                                          "abstract": " ".join(e.find("a:summary", ns).text.split()), "queries": []})
                h["queries"].append(qid)
            got += len(entries); start += 100
            if len(entries) < 100 or start >= 500:
                break
        log.append({"id": qid, "query": q, "returned": got})
        print(qid, got, flush=True)
    fam = list(csv.DictReader((SU / "final-family-index.csv").open(encoding="utf-8")))
    f1 = list(csv.DictReader((SU / "records.csv").open(encoding="utf-8")))
    f1_ids = {arxiv_id(r["arxiv_id"]) or arxiv_id(r["source_url"]) for r in f1} - {None}
    f1_titles = {norm(r["title"]) for r in f1}
    by_title = {norm(h["title"]): h for h in hits.values()}
    rows = []
    for r in fam:
        aid = arxiv_id(r["source_url"]) or arxiv_id(r["source_version"])
        in2 = (aid in hits) or (norm(r["title"]) in by_title)
        in1 = (aid in f1_ids) or (norm(r["title"]) in f1_titles)
        rows.append({"citation_key": r["citation_key"], "classification": r["classification"], "arxiv_id": aid or "",
                     "in_frame1_565": in1, "in_frame2_arxiv": in2})
    idx_ids = {x["arxiv_id"] for x in rows if x["arxiv_id"]}; idx_titles = {norm(r["title"]) for r in fam}
    queue = [h for h in hits.values() if h["arxiv_id"] not in idx_ids and h["arxiv_id"] not in f1_ids
             and norm(h["title"]) not in idx_titles and norm(h["title"]) not in f1_titles]
    with (HERE / "frame2_family_overlap.csv").open("w", newline="", encoding="utf-8") as fh:
        w = csv.DictWriter(fh, fieldnames=list(rows[0])); w.writeheader(); w.writerows(rows)
    with (HERE / "frame2_screening_queue.csv").open("w", newline="", encoding="utf-8") as fh:
        w = csv.DictWriter(fh, fieldnames=["arxiv_id", "published", "title", "queries", "abstract", "decision", "criterion", "coder", "note"])
        w.writeheader()
        for h in sorted(queue, key=lambda h: h["arxiv_id"]):
            w.writerow({**{k: h[k] for k in ("arxiv_id", "published", "title", "abstract")}, "queries": ";".join(h["queries"]),
                        "decision": "", "criterion": "", "coder": "", "note": ""})
    summ = {"queries": log, "unique_returns": len(hits), "screening_queue": len(queue)}
    for cls in ("core", "adjacent"):
        rs = [x for x in rows if x["classification"] == cls]
        ax = [x for x in rs if x["arxiv_id"]]
        summ[cls] = {"families": len(rs), "with_arxiv_id": len(ax),
                     "frame1_565": sum(x["in_frame1_565"] for x in rs), "frame2": sum(x["in_frame2_arxiv"] for x in rs),
                     "either": sum(x["in_frame1_565"] or x["in_frame2_arxiv"] for x in rs),
                     "neither": [x["citation_key"] for x in rs if not (x["in_frame1_565"] or x["in_frame2_arxiv"])]}
    summ["interpretation"] = ("Overlap with an author-designed second frame; not an independent recall estimate. "
                              "Families found by neither frame were found by seed snowballing only.")
    summ["retrieved_utc"] = time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime())
    (HERE / "frame2_summary.json").write_text(json.dumps(summ, indent=1))
    (HERE / "frame2_returns.json").write_text(json.dumps(sorted(hits.values(), key=lambda h: h["arxiv_id"]), indent=0))
    print(json.dumps({k: v for k, v in summ.items() if k != "queries"}, indent=1))


if __name__ == "__main__":
    main()
