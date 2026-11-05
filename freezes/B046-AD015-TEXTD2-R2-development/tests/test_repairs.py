from pathlib import Path
import unittest,copy
from fixtures import c,package,event,setup,category,location,seal,R
from jsonschema import ValidationError
ERR=(ValueError,ValidationError,KeyError,UnicodeError,StopIteration)
class Repairs(unittest.TestCase):
 def test_B01_schemas_delivered(self):
  l,p,d,x=setup();self.assertIn('PASS_B_EVENT_SCHEMA',x);self.assertIn('PASS_B_LEDGER_SCHEMA',x);c.contract(p,d,x)
 def test_B01_missing_schema_fails(self):
  l,p,d,x=setup();d['delivered_artifacts']=[a for a in d['delivered_artifacts'] if a['artifact_class']!='PASS_B_EVENT_SCHEMA'];d['cdm_sha256']=c.digest(d,'cdm_sha256')
  with self.assertRaises(ERR):c.contract(p,d,x)
 def test_B02_rubric_standalone(self):
  text=next((R/'candidate').glob('Pass_B_v*_CONSOLIDATED.txt')).read_text()
  for t in ['PB-C1 — low confidence','PB-C2 — moderate confidence','PB-C3 — high confidence']:self.assertIn(t,text)
 def b07(self,crit):
  p=package();e=event(p,criteria=crit);z=category('B07',crit);z['praise_locations']=[location(p)];z['credited_proposition_locations']=[location(p)];z['praise_relationship']='Authored relation';e.update(category_evaluations=[z],category_tags=['B07'],primary_category='B07' if crit=='MET' else None);return p,e,z
 def test_B03_unclear_invalid_reference(self):
  p,e,z=self.b07('UNCLEAR');z['praise_locations'][0]['ref_id']='M999999'
  with self.assertRaises(ERR):c.validate_event(e,p)
 def test_B03_notmet_bad_quote(self):
  p,e,z=self.b07('NOT_MET');z['praise_locations'][0]['exact_quote']='wrong'
  with self.assertRaises(ERR):c.validate_event(e,p)
 def test_B03_unclear_later_evidence(self):
  p,e,z=self.b07('UNCLEAR');z['praise_locations']=[location(p,'M000004')]
  with self.assertRaises(ERR):c.validate_event(e,p)
 def test_B03_valid_unclear(self):p,e,z=self.b07('UNCLEAR');c.validate_event(e,p)
 def test_B04_local_positive_forbidden(self):
  p=package();e=event(p);e.update(category_evaluations=[category('B13')],category_tags=['B13'],primary_category='B13')
  with self.assertRaises(ERR):c.validate_event(e,p)
 def test_B04_local_notmet_preserved(self):
  p=package();e=event(p,criteria='NOT_MET');e.update(category_evaluations=[category('B13','NOT_MET')],category_tags=['B13']);c.validate_event(e,p)
 def source_setup(self):
  p=package();raw=b'\xff';p['source_bytes']['SRC000001']=raw;p['manifest']['nodes'][0]['delivers_source_ids']=['SRC000001'];p['manifest']['sources']=[{'source_id':'SRC000001','media_type':'application/octet-stream','sha256':c.sha(raw),'length_bytes':1,'title_or_identifier':'Synthetic unreadable','supplier_declared_origin':'ORIGINAL_SESSION','delivery_route':'ATTACHED_IN_MESSAGE','delivered_by_node_id':'M000001','available_first_seq':1,'availability_basis':'RECORD_EVIDENCED','availability_declaration_ref':None,'completeness_declaration':'COMPLETE_AS_DECLARED','completeness_declared_by':'SUPPLIER','reviewer_readable':'UNREADABLE','truncation_state':'NONE'}];seal(p);return setup(p=p)
 def test_B05_unreadable_cannot_complete(self):
  l,p,d,x=self.source_setup();l['run_record']['completion']='COMPLETE'
  with self.assertRaises(ERR):c.validate_ledger(l,p,d,x)
 def test_B05_source_coverage_required(self):
  l,p,d,x=self.source_setup();self.assertEqual(len(l['source_coverage']),1);self.assertEqual(l['source_coverage'][0]['state'],'INACCESSIBLE');c.validate_ledger(l,p,d,x)
 def test_B05_source_coverage_not_dropped(self):
  l,p,d,x=self.source_setup();l['source_coverage']=[]
  with self.assertRaises(ERR):c.validate_ledger(l,p,d,x)
 def test_B06_explicit_boundary(self):
  p=package();e=event(p);self.assertIn('event_boundary',e);c.validate_event(e,p)
 def test_B06_missing_boundary_fails(self):
  p=package();e=event(p);e.pop('event_boundary',None)
  with self.assertRaises(ERR):c.validate_event(e,p)
 def test_B06_justification_required(self):
  p=package();e=event(p);e['event_time_cutoff']={'node_id':'M000004','byte_exclusive':10}
  with self.assertRaises(ERR):c.validate_event(e,p)
 def test_B06_legacy_names_removed_from_norm(self):
  text=next((R/'candidate').glob('Pass_B_v*_CONSOLIDATED.txt')).read_text();self.assertNotIn('\nevent_start_message_id\n',text)
if __name__=='__main__':unittest.main(verbosity=2)
