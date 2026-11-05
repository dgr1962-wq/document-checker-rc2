import unittest,sys,importlib.util
from pathlib import Path
R=Path(__file__).resolve().parents[1]
s=importlib.util.spec_from_file_location('n',R/'candidate/neutral_contract.py');n=importlib.util.module_from_spec(s);s.loader.exec_module(n)
class Contract(unittest.TestCase):
 def test_nonempty_range(self):
  with self.assertRaises(ValueError):n.slice_reference('NODE','M000001',0,0,{'M000001':b''},{})
 def test_empty_payload_length_still_valid(self):n.check_lengths([{'node_id':'M000001','node_kind':'MESSAGE_TEXT','content_length_bytes':0}],[],{'M000001':b''},{})
 def test_exact_names_in_contract(self):
  text=(R/'candidate/Shared_R2_Addendum.txt').read_text();self.assertIn('exactly content.txt',text);self.assertIn('exactly schema.json',text);self.assertIn('No document alias',text)
 def test_helper_documents_external_precondition(self):self.assertIn('externally verified freeze pin',n.check_spec.__doc__)
if __name__=='__main__':unittest.main(verbosity=2)
