from pathlib import Path
import unittest,importlib.util,hashlib
R=Path(__file__).resolve().parents[1]
p=R/'candidate/neutral_contract.py'
if p.exists():
 s=importlib.util.spec_from_file_location('neutral',p);n=importlib.util.module_from_spec(s);s.loader.exec_module(n)
else:n=None
class Repairs(unittest.TestCase):
 def api(self):self.assertIsNotNone(n,'Required successor contract is absent');return n
 def test_N01_separate_source_domain(self):
  self.assertIn('<source_id>@B', (R/'candidate/Input_Admission_v0.1.5.txt').read_text())
  self.assertEqual(self.api().slice_reference('SOURCE','SRC000001',0,3,{'OP000001':b'attachment'},{'SRC000001':b'abc'}),b'abc')
 def test_N01_no_source_node_conflation(self):
  with self.assertRaises(ValueError):self.api().slice_reference('NODE','SRC000001',0,3,{}, {'SRC000001':b'abc'})
 def test_N01_codepoint_boundary(self):
  with self.assertRaises((ValueError,UnicodeError)):self.api().slice_reference('SOURCE','SRC000001',1,2,{}, {'SRC000001':'é'.encode()})
 def test_N02_wrong_node_length(self):
  with self.assertRaises(ValueError):self.api().check_lengths([{'node_id':'M000001','node_kind':'MESSAGE_TEXT','content_length_bytes':4}],[],{'M000001':b'abc'},{})
 def test_N02_wrong_source_length(self):
  with self.assertRaises(ValueError):self.api().check_lengths([],[{'source_id':'SRC000001','length_bytes':4}],{}, {'SRC000001':b'abc'})
 def test_N02_boolean_rejected(self):
  with self.assertRaises(ValueError):self.api().check_lengths([],[{'source_id':'SRC000001','length_bytes':True}],{}, {'SRC000001':b'x'})
 def test_N02_empty_and_withheld(self):self.api().check_lengths([{'node_id':'OP000001','node_kind':'WITHHELD','content_length_bytes':None},{'node_id':'M000002','node_kind':'MESSAGE_TEXT','content_length_bytes':0}],[],{'M000002':b''},{})
 def test_N03_pinned_spec(self):
  self.api().check_spec('0.1.5',b'exact',hashlib.sha256(b'exact').hexdigest())
  with self.assertRaises(ValueError):self.api().check_spec('0.1.4',b'exact',hashlib.sha256(b'exact').hexdigest())
 def test_N03_wrong_spec(self):
  with self.assertRaises(ValueError):self.api().check_spec('0.1.5',b'other',hashlib.sha256(b'exact').hexdigest())
 def test_N04_exact_envelope(self):
  a=[{'artifact_class':'APK','identity_sha256':'a'*64,'members':{'manifest.json':b'{ "x": 1 }','node/M000001':b'Caf\xc3\xa9\n'}}];raw=self.api().envelope(a)
  self.assertEqual(self.api().verify_envelope(raw,hashlib.sha256(raw).hexdigest()),a)
 def test_N04_raw_change_detected(self):
  raw=self.api().envelope([{'artifact_class':'APK','identity_sha256':'a'*64,'members':{'x':b'abc'}}])
  with self.assertRaises(ValueError):self.api().verify_envelope(raw+b' ',hashlib.sha256(raw).hexdigest())
 def test_N04_binary_remains_unsupported(self):
  with self.assertRaises((ValueError,UnicodeError)):self.api().envelope([{'artifact_class':'APK','identity_sha256':'a'*64,'members':{'x':b'\xff'}}])
if __name__=='__main__':unittest.main(verbosity=2)
