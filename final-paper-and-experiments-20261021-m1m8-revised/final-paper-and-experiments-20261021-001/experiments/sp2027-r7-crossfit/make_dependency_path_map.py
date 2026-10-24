from pathlib import Path
import json
h=Path(__file__).resolve().parent;root=h.parents[1]
for name in ['sp2027-r7-crossfit','sp2027-r7-localization']:
 d=root/'experiments'/name;c=json.loads((d/'dependency-closure.json').read_text())
 payload=dict(version=1,current_package_root='relative to dependency_check.py: ../..',scope='Only the explicit original-manifest-bound supplemental paths below; no primary frozen path map is modified.',allowed_relative_paths=sorted(set(c['anchors'])|{e['relative_path'] for e in c['dependencies']}),authority='dependency-closure.json requires original R4 episode-bound runtime SHA and original R6 frozen authority chain')
 (d/'dependency-path-map.json').write_text(json.dumps(payload,indent=2),encoding='utf8')
