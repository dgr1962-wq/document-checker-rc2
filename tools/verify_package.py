"""Offline package integrity only. Never launches an assessment or a model."""
from pathlib import Path
import hashlib,json
root=Path(__file__).resolve().parents[1]
def digest(p):return hashlib.sha256(p.read_bytes()).hexdigest()
rows=json.loads((root/'PUBLIC-INVENTORY.json').read_text())['files']
expected={x['path'] for x in rows}|{'PUBLIC-INVENTORY.json','SHA256SUMS'}
actual={str(p.relative_to(root)) for p in root.rglob('*') if p.is_file() and not any(x in p.relative_to(root).parts for x in ['.venv','__pycache__','.git'])}
assert actual==expected,{'missing':sorted(expected-actual),'unexpected':sorted(actual-expected)}
for row in rows:
 p=root/row['path'];assert p.is_file() and not p.is_symlink(),row['path']
 assert len(p.read_bytes())==row['bytes'] and digest(p)==row['sha256'],row['path']
checks={}
for line in (root/'SHA256SUMS').read_text().splitlines():
 sha,name=line.split('  ',1);assert name not in checks,name;checks[name]=sha
assert set(checks)==expected-{'SHA256SUMS'}
for name,sha in checks.items():assert digest(root/name)==sha,name
for row in json.loads((root/'provenance/source-map.json').read_text()):
 assert digest(root/row['path'])==row['sha256']
 if row['transformation']=='byte-identical':assert row['sha256']==row['source_sha256']
print(json.dumps({'status':'PASS','inventoried_payload_files':len(rows),'checksums_verified':len(checks),'models_or_assessments_executed':0}))
