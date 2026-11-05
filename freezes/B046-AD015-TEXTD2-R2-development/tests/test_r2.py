"""Targeted R2 synthetic regressions; no real corpus, network or assessment."""
import unittest,copy,sys,importlib.util
from pathlib import Path
sys.path.insert(0,str(Path(__file__).parent))
from fixtures import c,setup,package,event,category,location,seal,node,R
from test_delivery_ported import fixture,pack
class R2(unittest.TestCase):
 def named(self):
  p,d,e,rows=fixture()
  for r in rows[2:]:r['members']={('schema.json' if r['artifact_class'].endswith('_SCHEMA') else 'content.txt'):next(iter(r['members'].values()))}
  return p,d,e,rows
 def test_P01_exact_names_control(self):
  p,d,e,r=self.named();self.assertTrue(c.verify_delivery(pack(d,r),p,d,e))
 def test_P01_legacy_document_rejected(self):
  p,d,e,r=self.named()
  for row in r[2:]:row['members']={'document':next(iter(row['members'].values()))}
  with self.assertRaises(ValueError):c.verify_delivery(pack(d,r),p,d,e)
 def test_P01_wrong_schema_name_rejected(self):
  p,d,e,r=self.named();r[-1]['members']={'content.txt':next(iter(r[-1]['members'].values()))}
  with self.assertRaises(ValueError):c.verify_delivery(pack(d,r),p,d,e)
 def test_P02_cdm_permutation_rejected(self):
  _,p,d,e=setup();a=d['delivered_artifacts'];a[0],a[-1]=a[-1],a[0]
  for i,x in enumerate(a,1):x['delivery_order']=i
  d['cdm_sha256']=c.digest(d,'cdm_sha256')
  with self.assertRaisesRegex(ValueError,'canonical'):c.contract(p,d,e)
 def test_P02_matching_cdm_envelope_permutation_rejected(self):
  p,d,e,r=self.named();r[0],r[-1]=r[-1],r[0];a=d['delivered_artifacts'];a[0],a[-1]=a[-1],a[0]
  for i,x in enumerate(a,1):x['delivery_order']=i
  with self.assertRaisesRegex(ValueError,'canonical'):c.verify_delivery(pack(d,r),p,d,e)
 def test_P02_envelope_only_permutation_rejected(self):
  p,d,e,r=self.named();r[0],r[-1]=r[-1],r[0]
  with self.assertRaises(ValueError):c.verify_delivery(pack(d,r),p,d,e)
 def b13(self,result,form='FIRST_INSTANCE_STATE'):
  p=package();e=event(p);z=category('B13');z['disposition']=result;e.update(category_evaluations=[z],category_tags=['B13'],event_form=form,event_disposition=result,stage2_disposition=result,primary_category='B13')
  if result!='POSITIVE_FINDING':
   e.update(invoked_bridge={'presence':'PRESENT','fit':'FITS' if result=='NO_POSITIVE_FINDING' else 'NOT_ASSESSABLE','locations':[location(p)],'rationale':'Synthetic declared premise'},bridge_locus='INVOKED',missing_basis_eligibility=None,consequence_ids=[],finding_id=None,primary_category=None,severity=None,pass_b_confidence=None)
   if result=='UNRESOLVED':e['unresolved_detail']={'field':'invoked_bridge.fit','reason':'Synthetic unclear fit'}
  return p,e
 def test_P04_nonsequence_MET_all_dispositions(self):
  for result in ['POSITIVE_FINDING','NO_POSITIVE_FINDING','UNRESOLVED']:
   with self.subTest(result=result):
    p,e=self.b13(result)
    with self.assertRaisesRegex(ValueError,'B13'):c.validate_event(e,p)
 def test_P04_sequence_MET_controls(self):
  for result in ['POSITIVE_FINDING','NO_POSITIVE_FINDING','UNRESOLVED']:
   with self.subTest(result=result):
    p,e=self.b13(result,'SEQUENCE');e.update(event_boundary={'start_node_id':'M000002','end_node_id':'M000004','cutoff_justification':None},event_time_cutoff={'node_id':'M000004','byte_exclusive':len(p['node_bytes']['M000004'])},stable_location=[location(p,'M000004')],event_id='PE000002',constituent_event_ids=['PE000001'],emergent_consequence='Distinct declared sequence consequence')
    if result=='POSITIVE_FINDING':e.update(finding_id='PB-F000002',consequence_ids=['C-sequence'])
    l,p,d,x=setup([event(p),e],p);c.validate_ledger(l,p,d,x)
 def test_P04_nonsequence_NOT_MET_UNCLEAR_controls(self):
  for crit in ['NOT_MET','UNCLEAR']:
   p=package();e=event(p,criteria=crit);e.update(category_evaluations=[category('B13',crit)],category_tags=['B13']);c.validate_event(e,p)
 def sequence(self):
  p=package();child=event(p);parent=event(p,eid='PE000002',nid='M000004');parent.update(event_form='SEQUENCE',constituent_event_ids=['PE000001'],emergent_consequence='Distinct synthetic consequence');return p,child,parent
 def check(self,p,events):
  l,p,d,x=setup(events,p);return c.validate_ledger(l,p,d,x)
 def test_P05_before_start_rejected(self):
  p,a,b=self.sequence()
  with self.assertRaisesRegex(ValueError,'constituent.*boundary'):self.check(p,[a,b])
 def test_P05_contained_control(self):
  p,a,b=self.sequence();b['event_boundary']['start_node_id']='M000002';self.check(p,[a,b])
 def test_P05_after_end_later_rejected(self):
  p=package();a=event(p,eid='PE000001',nid='M000004');b=event(p,eid='PE000002');b.update(event_form='SEQUENCE',constituent_event_ids=['PE000001'],emergent_consequence='Synthetic')
  with self.assertRaises(ValueError):self.check(p,[a,b])
 def test_P05_nested_before_start_rejected(self):
  p,a,b=self.sequence();b['event_boundary']['start_node_id']='M000002';n,raw=node(6,'A separate later assistant event.','ASSISTANT');p['manifest']['nodes'].append(n);p['manifest']['turns'].append({'turn_id':n['turn_id'],'role':'ASSISTANT','node_ids':[n['node_id']],'interleaving_status':'NOT_APPLICABLE'});p['node_bytes'][n['node_id']]=raw;seal(p)
  root=event(p,eid='PE000003',nid='M000006');root.update(event_form='SEQUENCE',constituent_event_ids=['PE000002'],emergent_consequence='Distinct root');root['event_boundary']['start_node_id']='M000004'
  with self.assertRaisesRegex(ValueError,'constituent.*boundary'):self.check(p,[a,b,root])
 def test_P05_nested_contained_control(self):
  p,a,b=self.sequence();b['event_boundary']['start_node_id']='M000002';root=event(p,eid='PE000003',nid='M000004');root.update(event_form='SEQUENCE',constituent_event_ids=['PE000002'],emergent_consequence='Distinct nested');root['event_boundary']['start_node_id']='M000002';self.check(p,[a,b,root])
 def test_P05_unknown_turn_timing_rejected(self):
  p,a,b=self.sequence();b['event_boundary']['start_node_id']='M000002';m=p['manifest'];m['nodes'][2]['seq']=5;m['nodes'][3]['turn_id']='T000002';m['turns']=[m['turns'][0],{'turn_id':'T000002','role':'ASSISTANT','node_ids':['M000002','M000004'],'interleaving_status':'NOT_PRESERVED'},m['turns'][2]];seal(p)
  with self.assertRaises(ValueError):self.check(p,[a,b])
 def test_P05_later_audit_cannot_repair_boundary(self):
  p,a,b=self.sequence();a['later_audit_material']=[{'location':location(p,'M000004'),'effect':'Later note; not a boundary repair'}]
  with self.assertRaisesRegex(ValueError,'constituent.*boundary'):self.check(p,[a,b])
 def test_S17_missing_justification_exact_guard(self):
  p=package();e=event(p);e['event_time_cutoff']['byte_exclusive']=10;e['stable_location']=[location(p,end=10)]
  with self.assertRaisesRegex(ValueError,'nondefault cutoff justification'):c.validate_event(e,p)
 def test_S17_justified_control(self):
  p=package();e=event(p);e['event_time_cutoff']['byte_exclusive']=10;e['stable_location']=[location(p,end=10)];e['event_boundary']['cutoff_justification']='Bounded synthetic partial-node cutoff';c.validate_event(e,p)
if __name__=='__main__':unittest.main(verbosity=2)
