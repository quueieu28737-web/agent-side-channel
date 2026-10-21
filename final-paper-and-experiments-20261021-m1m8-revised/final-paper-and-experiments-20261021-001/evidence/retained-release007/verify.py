"""Portable saved-evidence verifier. Standard library; no fitting or network."""
import csv
import hashlib
import importlib.util
import json
from pathlib import Path, PurePosixPath
import re
import subprocess
import sys

sys.dont_write_bytecode = True
ROOT = Path(__file__).resolve().parent
HISTORICAL_MANIFEST = "c90bdda17d6faf56c612c8eddb8989258d03b3c17b9b3033b0eb84689a4b769c"
DOCUMENTS = {"main": ("main.tex", "paper.pdf"), "supplement": ("supplement.tex", "supplement.pdf")}


def sha(path):
    return hashlib.sha256(Path(path).read_bytes()).hexdigest()


def load(path):
    return json.loads(Path(path).read_text(encoding="utf-8-sig"))


def inside(root, relative):
    relative = PurePosixPath(str(relative).replace("\\", "/"))
    assert not relative.is_absolute() and ".." not in relative.parts and ":" not in str(relative)
    root = Path(root).resolve()
    path = root.joinpath(*relative.parts)
    assert root in path.resolve().parents and not path.is_symlink()
    return path


def check_manifest(root):
    root = Path(root).resolve()
    manifest = load(root / "SHA256SUMS.json")
    files = manifest["files"]
    actual = {p.relative_to(root).as_posix() for p in root.rglob("*") if p.is_file()}
    assert actual == set(files) | {"SHA256SUMS.json"}, "Exact manifest membership"
    assert not any(p.is_symlink() for p in root.rglob("*"))
    for relative, expected in files.items():
        assert re.fullmatch(r"[0-9a-f]{64}", expected) and sha(inside(root, relative)) == expected, relative
    return manifest


def active_tex_closure(root, entry):
    found = set()
    def visit(relative):
        if relative in found:
            return
        found.add(relative)
        text = inside(root, relative).read_text(encoding="utf-8-sig")
        text = re.sub(r"(?<!\\)%[^\n]*", "", text)
        text = re.sub(r"\\iffalse\b.*?\\fi\b", "", text, flags=re.S)
        for name in re.findall(r"\\(?:input|include)\s*\{([^}]+)\}", text):
            visit(name if Path(name).suffix else name + ".tex")
        for names in re.findall(r"\\bibliography\s*\{([^}]+)\}", text):
            found.update(n.strip() + ".bib" for n in names.split(","))
        for name in re.findall(r"\\includegraphics(?:\[[^]]*\])?\s*\{([^}]+)\}", text):
            matches = [name] if Path(name).suffix else [name+e for e in (".pdf", ".png", ".jpg", ".jpeg") if inside(root,name+e).is_file()]
            assert len(matches) == 1
            found.add(matches[0])
    visit(entry)
    assert all(inside(root,p).is_file() for p in found)
    return sorted(found)


def check_documents(root):
    binding = load(root / "current/release-binding.json")
    hashes, closures, qa = [load(root / "current" / name) for name in ("source-hashes.json", "document-closures.json", "pdf-validation.json")]
    union = set()
    for name, (entry,pdf) in DOCUMENTS.items():
        current = active_tex_closure(root/"manuscript",entry)
        assert current == closures[name]
        union.update(current)
        assert sha(root/pdf) == qa[name]["pdf_sha256"] == binding["documents"][name]["pdf_sha256"]
        assert not qa[name]["log_failures"] and not qa[name].get("bib_warnings",[])
        assert qa[name]["US_letter"] and qa[name]["author"] in ("",None)
    assert set(hashes) == union
    assert all(sha(inside(root/"manuscript",p)) == value for p,value in hashes.items())
    assert sha(root/"current/source-hashes.json") == binding["source_hashes_sha256"]
    assert sha(root/"current/document-closures.json") == binding["document_closures_sha256"]
    assert qa["main"]["body_pages"] <= 13 and qa["main"]["appendix_pages"] <= 5
    assert qa["main"]["pages"] == sum(qa["main"][k] for k in ("body_pages","appendix_pages","reference_pages"))
    assert binding["uploaded"] is False and binding["public_hosting_claimed"] is False
    for claim in load(root/"current/claim-bindings.json")["claims"]:
        for anchor in claim["manuscript_anchors"]:
            assert anchor["path"] in closures[anchor["document"]]
            text=inside(root/"manuscript",anchor["path"]).read_text(encoding="utf-8-sig")
            assert hashes[anchor["path"]] == anchor["sha256"]
            matches=list(re.finditer(anchor["pattern"],text))
            assert len(matches)==1 and matches[0].group()==anchor["matched_text"]
            assert text.count("\n",0,matches[0].start())+1==anchor["line"]
        for record in claim["evidence_records"]:
            assert inside(root,record).is_file()
    return binding,qa


def check_search(root):
    folder=root/"search-update"
    records=list(csv.DictReader((folder/"records.csv").open(encoding="utf-8-sig",newline="")))
    assert len({r["record_id"] for r in records})==len(records)
    from collections import Counter
    counts=dict(Counter(r["decision"] for r in records))
    summary=load(folder/"screening-summary.json")
    assert len(records)==summary["unique_records"] and counts==summary["counts"]
    assert all(r["reason"] and r["criterion"] for r in records)
    assert all(len(r["evidence_excerpt"].split())<=25 for r in records)
    additions=list(csv.DictReader((folder/"addition.csv").open(encoding="utf-8-sig",newline="")))
    added=load(folder/"addition-summary.json")
    assert len(additions)==added["new_core"]==counts["NEW_CORE_SOURCE_VERIFIED"]
    assert all(r["record_id"] in {x["record_id"] for x in records} and r["source_url"] and r["source_locator"] and re.fullmatch("[0-9a-f]{64}",r["source_sha256"]) for r in additions)
    adjacent=list(csv.DictReader((folder/"addition-adjacent.csv").open(encoding="utf-8-sig",newline="")))
    merged=list(csv.DictReader((folder/"final-family-index.csv").open(encoding="utf-8-sig",newline="")))
    merge=load(folder/"final-family-index-check.json")
    with (folder/"final-family-index.csv").open(encoding="utf-8-sig",newline="") as handle:
        headers=csv.DictReader(handle).fieldnames
    assert len({h.casefold() for h in headers})==len(headers) and "NR_status" in headers and "update_nr_status" in headers
    assert merge["headers_casefold_unique"] is True
    legacy=list(csv.DictReader((folder/"original60-merge-input.csv").open(encoding="utf-8-sig",newline="")))
    assert merge["result"]=="PASS" and len(merged)==merge["families"]==82
    assert len({r["citation_key"] for r in merged})==82 and len(legacy)==60 and len(adjacent)==7
    assert dict(Counter(r["classification"] for r in merged))==merge["classification_counts"]=={"core":58,"adjacent":24}
    assert dict(Counter(r["origin_class"] for r in merged if r["classification"]=="core"))==merge["core_origin_counts"]=={"workflow-origin":20,"inherited-runtime/application":38}
    assert sum(r["diagnostic_component"].lower()=="true" for r in merged)==merge["diagnostic_count"]==5
    indexed={r["citation_key"]:r for r in merged}
    assert all(all(indexed[r["citation_key"]][key]==value for key,value in r.items()) for r in legacy),"Original60 fields retained"
    assert {r["citation_key"] for r in merged}=={r["citation_key"] for r in legacy+additions+adjacent}
    assert all(r["source_url"] and r["source_locator"] and re.fullmatch("[0-9a-f]{64}",r["source_sha256"]) for r in adjacent)
    definitions=(root/"manuscript/tables/final-counts.tex").read_text(encoding="utf-8")
    for macro,value in (("FinalN",82),("FinalCore",58),("FinalAdjacent",24),("FinalA",20),("FinalB",38),("SnapshotN",60),("SnapshotCore",43)):
        assert re.search(r"\\newcommand\{\\"+macro+r"\}\{"+str(value)+r"\}",definitions),"Manuscript count "+macro
    bibfiles=["refs.bib","refs-final-additions.bib","evidence/search-completion-20261021-001/new_refs.bib","evidence/search-completion-20261021-001/new_refs_adjacent.bib"]
    bibkeys=Counter(key for filename in bibfiles for key in re.findall(r"@\w+\s*\{\s*([^,\s]+)",(root/"manuscript"/filename).read_text(encoding="utf-8-sig")))
    assert all(bibkeys[r["citation_key"]]==1 for r in merged),"All82 family citations resolve exactly once"
    audits=list(csv.DictReader((folder/"exclusion-audit.csv").open(encoding="utf-8-sig",newline="")))
    audit_summary=load(folder/"exclusion-audit-summary.json")
    assert len(audits)==audit_summary["audited"]==204 and audit_summary["rerouted"]==4
    assert not any(p.name.lower().endswith((".pdf",".html")) for p in folder.rglob("*") if p.is_file())
    assert not (folder/"sources").exists() and not (folder/"raw").exists()
    return {"unique_records":len(records),"decisions":counts,"new_core_source_rows":len(additions),"new_selected_adjacent":len(adjacent),"merged_family_count":len(merged),"original60_fields_preserved":True,"exclusion_audit_rows":len(audits),"query_scope":"Frozen finite supplementary round; not the unacquired broad IEEE frame."}


def run_checker(path,args=(),timeout=180):
    result=subprocess.run([sys.executable,"-B",str(path),*args],cwd=ROOT,capture_output=True,text=True,encoding="utf-8",timeout=timeout)
    assert result.returncode==0, result.stdout+result.stderr
    return json.loads(result.stdout)


def main():
    manifest=check_manifest(ROOT)
    historical=ROOT/"history-release006"
    assert sha(historical/"SHA256SUMS.json")==HISTORICAL_MANIFEST
    history=run_checker(historical/"verify.py")
    assert history["status"]=="LOCAL_RELEASE006_CHECKS_PASS"
    binding,qa=check_documents(ROOT)
    search=check_search(ROOT)
    e1=run_checker(ROOT/"controlled-study/verification/verify_e1.py")
    e2=run_checker(ROOT/"controlled-study/verification/verify_e2.py",["--check-only"])
    assert e1["source_outputs"]==48 and e1["replays"]==144 and e1["new_model_calls"]==e1["refits"]==e1["new_TLS_replays"]==0
    assert e2["task_count"]==24 and e2["arm_rows"]==120 and e2["new_model_calls"]==0
    assert e2["global_collection_observed_tokens"]==195927
    claims=load(ROOT/"current/claim-bindings.json")
    observed=load(ROOT/"controlled-study/data/E2/summary.json")["arms"]
    assert observed["state_changing"]["task_success_count"]==claims["numeric_bindings"]["E2_live_success"]==9
    assert observed["state_changing"]["protected_state_violation_count"]==claims["numeric_bindings"]["E2_protected_violations"]==6
    assert search["unique_records"]==claims["numeric_bindings"]["search_records"]
    check_manifest(ROOT)
    print(json.dumps({"status":"LOCAL_RELEASE007_CHECKS_PASS","manifest_files":len(manifest["files"]),"document_pages":{name:qa[name]["pages"] for name in DOCUMENTS},"search":search,"E1":e1,"E2":e2,"historical_verifier_status":history["status"],"verification_model_calls":0,"verification_fits":0,"verification_TLS_replays":0,"uploaded":False},ensure_ascii=False,indent=2))


if __name__=="__main__":
    main()
