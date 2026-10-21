from pathlib import Path
import zipfile

root = Path(__file__).resolve().parent
p = root / 'final-paper-and-experiments-20261021-m1m8-revised/final-paper-and-experiments-20261021-001'
out = p / 'experiments/reviewer-audit'
out.mkdir(exist_ok=True)
backup = p / 'provenance/pre-review-manuscript.zip'
if not backup.exists():
    with zipfile.ZipFile(backup, 'w', zipfile.ZIP_DEFLATED) as z:
        for f in (p/'manuscript').rglob('*'):
            if f.is_file(): z.write(f, f.relative_to(p))
        for f in (p/'pdf').glob('*.pdf'): z.write(f, f.relative_to(p))
        for name in ['README.md','SHA256SUMS.json','verify_package.py']:
            z.write(p/name, name)
src = (p/'experiments/revision-m1-m8/run_sp2027_experiments.py').read_text(encoding='utf-8')
src = src.replace('return summary\n', '(OUT / "retail_units.json").write_text(json.dumps(rows, indent=2), encoding="utf-8")\n    return summary\n')
src = src.replace('"cover_error": str(obs or "").startswith("Error:"),', '''"cover_error": str(obs or "").startswith("Error:"),
                        "cover_error_text": str(obs) if str(obs).startswith("Error:") else None,
                        "dispatch": dispatched_tools,
                        "baseline_errors": sum(x[2] for x in base_obs),
                        "reference_cancel_count": sum(a.name == "cancel_pending_order" for a in task.actions),
                        "obs_cancel_count": sum(t[0] == "cancel_pending_order" for t in dispatched_tools),''')
src = src.replace('for oid in candidates\n', 'for oid in base["orders"] if base["orders"][oid]["user_id"] == task.user_id\n')
src = src.replace('"eligible_user_orders_equal": uo_m,', '"eligible_user_orders_equal": uo_m,\n                "eligible_user_orders_ci95": [uo_lo, uo_hi],')
(out/'retail_replay.py').write_text(src, encoding='utf-8')
print(out)
