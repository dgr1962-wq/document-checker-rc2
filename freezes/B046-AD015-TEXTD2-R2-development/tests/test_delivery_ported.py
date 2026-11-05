"""R1 B01 bounded local NENV-1 byte-binding checks, no delivery to a model."""
import unittest,sys,importlib.util
from pathlib import Path
sys.path.insert(0,str(Path(__file__).parent))
from fixtures import setup,c,R
s=importlib.util.spec_from_file_location('neutral',R/'sources/neutral_contract.py');n=importlib.util.module_from_spec(s);s.loader.exec_module(n)
PINS={'ADMISSION_SPEC':'sources/Input_Admission_Candidate_v0.1.5.txt','PASS_B_INSTRUMENT':'candidate/Pass_B_v0.4.6_CONSOLIDATED.txt','RUN_WRAPPER':'candidate/Pass_B_Wrapper_B046.txt','PASS_B_EVENT_SCHEMA':'candidate/event.schema.json','PASS_B_LEDGER_SCHEMA':'candidate/ledger.schema.json'}
def fixture():
 _,p,d,e=setup();members={'manifest.json':c.rfc8785.dumps(p['manifest'])}
 for domain in ('node','source','declaration'):
  members.update({domain+'/'+k:v for k,v in p[domain+'_bytes'].items()})
 rows=[{'artifact_class':'APK','identity_sha256':e['APK'],'members':members},{'artifact_class':'ADMISSION_REPORT','identity_sha256':e['ADMISSION_REPORT'],'members':{'report.json':c.rfc8785.dumps(p['admission_report'])}}]
 rows += [{'artifact_class':k,'identity_sha256':e[k],'members':{('schema.json' if k.endswith('_SCHEMA') else 'content.txt'):(R/v).read_bytes()}} for k,v in PINS.items()]
 return p,d,e,rows
def pack(d,rows):
 raw=n.envelope(rows);d['delivery_transport_sha256']=c.sha(raw);d['cdm_sha256']=c.digest(d,'cdm_sha256');return raw
class Delivery(unittest.TestCase):
 def test_valid_seven_artifacts(self):
  p,d,e,r=fixture();self.assertTrue(c.verify_delivery(pack(d,r),p,d,e))
 def test_missing_schema(self):
  p,d,e,r=fixture();r.pop()
  with self.assertRaises(ValueError):c.verify_delivery(pack(d,r),p,d,e)
 def test_changed_schema_rehashed_envelope(self):
  p,d,e,r=fixture();r[-1]['members']['schema.json']+=b' '
  with self.assertRaises(ValueError):c.verify_delivery(pack(d,r),p,d,e)
 def test_changed_node_rehashed_envelope(self):
  p,d,e,r=fixture();r[0]['members']['node/M000002']=b'changed'
  with self.assertRaises(ValueError):c.verify_delivery(pack(d,r),p,d,e)
 def test_raw_transport_tamper(self):
  p,d,e,r=fixture();raw=pack(d,r)
  with self.assertRaises(ValueError):c.verify_delivery(raw+b' ',p,d,e)
 def test_wrong_caller_pin(self):
  p,d,e,r=fixture();e['PASS_B_EVENT_SCHEMA']='0'*64
  with self.assertRaises(ValueError):c.verify_delivery(pack(d,r),p,d,e)
if __name__=='__main__':unittest.main(verbosity=2)
