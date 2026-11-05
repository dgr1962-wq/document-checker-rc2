import unittest,sys
from pathlib import Path
sys.path.insert(0,str(Path(__file__).resolve().parents[1]))
from receipt_contract import FIELDS,validate_receipt
class Receipt(unittest.TestCase):
 def fixture(self):
  expected={k:('a'*64 if k.endswith('_sha256') else 'SYNTHETIC-NOT-REAL-TRUST') for k in FIELDS}
  expected.update(consumer='PASS_B',stage='PASS_B_ASSESSMENT',admission_spec_version='0.1.5',verified_at='2026-11-04T00:00:00Z',outcome='VERIFIED',independent_pin_status='VERIFIED',original_raw_jcs_status='VERIFIED')
  return dict(expected,receipt_version='OP-R2.1'),expected
 def test_matching_synthetic_control(self):r,e=self.fixture();self.assertTrue(validate_receipt(r,e))
 def test_missing(self):
  _,e=self.fixture()
  with self.assertRaisesRegex(ValueError,'MISSING'):validate_receipt(None,e)
 def test_every_binding_mismatch(self):
  for k in FIELDS:
   with self.subTest(field=k):
    r,e=self.fixture();r[k]='b'*64 if k.endswith('_sha256') else 'WRONG'
    with self.assertRaises(ValueError):validate_receipt(r,e)
 def test_unverified_context(self):
  for k in ['outcome','independent_pin_status','original_raw_jcs_status']:
   r,e=self.fixture();e[k]='UNKNOWN'
   with self.assertRaisesRegex(ValueError,'UNVERIFIED'):validate_receipt(r,e)
 def test_missing_binding(self):
  r,e=self.fixture();del r['canonicality_evidence_sha256']
  with self.assertRaises(ValueError):validate_receipt(r,e)
 def test_stage_consumer_mismatch(self):
  r,e=self.fixture();r['stage']=e['stage']='PASS_A_INVENTORY'
  with self.assertRaisesRegex(ValueError,'STAGE'):validate_receipt(r,e)
 def test_no_timezone(self):
  r,e=self.fixture();r['verified_at']=e['verified_at']='2026-11-04T00:00:00'
  with self.assertRaisesRegex(ValueError,'TIMESTAMP'):validate_receipt(r,e)
 def test_A_external_stage_controls(self):
  for stage in ['PASS_A_INVENTORY','PASS_A_CLASSIFICATION']:
   r,e=self.fixture();r['consumer']=e['consumer']='PASS_A';r['stage']=e['stage']=stage;self.assertTrue(validate_receipt(r,e))
if __name__=='__main__':unittest.main(verbosity=2)
