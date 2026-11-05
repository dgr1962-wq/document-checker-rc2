"""Bounded Admission 0.1.5 / TEXT-D2 identity helpers. Not a full Admission gate."""
from pathlib import Path
import sys,hashlib,json,re
sys.path.insert(0,str(Path(__file__).resolve().parents[1]/'vendor'))
import rfc8785
def require(ok,reason):
 if not ok:raise ValueError(reason)
def sha(b):return hashlib.sha256(b).hexdigest()
def slice_reference(kind,id,start,end,node_bytes,source_bytes):
 require(kind in ('NODE','SOURCE'),'reference domain')
 require(bool(re.fullmatch(r'(?:M|OP)[0-9]{6,}' if kind=='NODE' else r'SRC[0-9]{6,}',id)),'domain ID')
 mapping=node_bytes if kind=='NODE' else source_bytes
 require(id in mapping,'missing reference');raw=mapping[id]
 require(type(start) is int and type(end) is int and 0<=start<end<=len(raw),'range')
 raw.decode('utf8');raw[:start].decode('utf8');raw[start:end].decode('utf8');return raw[start:end]
def check_lengths(nodes,sources,node_bytes,source_bytes):
 for n in nodes:
  length=n['content_length_bytes'];id=n['node_id']
  if n['node_kind']=='WITHHELD':require(length is None and id not in node_bytes,'ADM-02 withheld length');continue
  require(id in node_bytes and type(length) is int and length>=0 and length==len(node_bytes[id]),'ADM-02 node length')
 for s in sources:
  id=s['source_id'];v=s['length_bytes'];require(id in source_bytes and type(v) is int and v>=0 and v==len(source_bytes[id]),'ADM-02 source length')
def check_spec(version,supplied_bytes,trusted_sha256):
 require(version=='0.1.5','ADMISSION_VERSION_MISMATCH')
 require(bool(re.fullmatch('[a-f0-9]{64}',trusted_sha256)) and sha(supplied_bytes)==trusted_sha256,'ADMISSION_SPEC_HASH_MISMATCH')
def envelope(artifacts):
 """Raw transport identity is distinct from artifact semantic identity; CDM excluded."""
 seen=set();rows=[]
 for a in artifacts:
  require(set(a)=={'artifact_class','identity_sha256','members'},'artifact fields')
  cls=a['artifact_class'];require(cls not in seen and cls!='CDM','duplicate/self-included CDM');seen.add(cls)
  require(bool(re.fullmatch('[a-f0-9]{64}',a['identity_sha256'])),'identity digest')
  rows.append({'artifact_class':cls,'identity_sha256':a['identity_sha256'],'members':[{'name':k,'text':v.decode('utf8'),'raw_sha256':sha(v)} for k,v in sorted(a['members'].items())]})
 return rfc8785.dumps({'transport_version':'NENV-1','artifacts':rows})
def verify_envelope(raw,expected_raw_sha256):
 require(sha(raw)==expected_raw_sha256,'TRANSPORT_HASH_MISMATCH')
 def pairs(items):
  d={}
  for k,v in items:require(k not in d,'duplicate JSON key');d[k]=v
  return d
 x=json.loads(raw,object_pairs_hook=pairs);require(set(x)=={'transport_version','artifacts'} and x['transport_version']=='NENV-1','transport version/fields');out=[]
 for a in x['artifacts']:
  require(set(a)=={'artifact_class','identity_sha256','members'},'artifact fields');members={}
  for m in a['members']:
   require(set(m)=={'name','text','raw_sha256'} and m['name'] not in members,'member fields/duplicate');b=m['text'].encode('utf8');require(sha(b)==m['raw_sha256'],'member integrity');members[m['name']]=b
  out.append({'artifact_class':a['artifact_class'],'identity_sha256':a['identity_sha256'],'members':members})
 require(envelope(out)==raw,'noncanonical envelope');return out
