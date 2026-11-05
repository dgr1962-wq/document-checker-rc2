from pathlib import Path
import unittest,importlib.util,sys,json,copy
R=Path(__file__).resolve().parents[1];sys.path.insert(0,str(R/'vendor'))
s=importlib.util.spec_from_file_location('a',R/'candidate/a05_rule_guards.py');g=importlib.util.module_from_spec(s);s.loader.exec_module(g)
class Repairs(unittest.TestCase):
 def api(self,name):self.assertTrue(hasattr(g,name),'Missing successor '+name);return getattr(g,name)
 def test_A01_shared_target_spans(self):
  entries=[{'claim_id':'C1','selected_proposition':'A says X','attribution_target':{'id':'SRC000001'},'ranges':[{'node_id':'M000001','byte_start':0,'byte_end':19}]},{'claim_id':'C2','selected_proposition':'B says X','attribution_target':{'id':'SRC000002'},'ranges':[{'node_id':'M000001','byte_start':0,'byte_end':19}]}]
  self.api('validate_inventory_units')(entries)
 def test_A01_duplicate_unit_rejected(self):
  x={'claim_id':'C1','selected_proposition':'A says X','attribution_target':{'id':'SRC000001'},'ranges':[{'node_id':'M000001','byte_start':0,'byte_end':1}]};y=copy.deepcopy(x);y['claim_id']='C2'
  with self.assertRaises(ValueError):self.api('validate_inventory_units')([x,y])
 def test_A01_normative_split_policy(self):self.assertIn('Shared lexical ranges across distinct propositions are permitted',(R/'candidate/Pass_A_v0.5.txt').read_text())
 def test_A02_other_tier_portions(self):self.api('check_tier_result')('RETROSPECTIVE',{'supported_portion':'narrow part','evidence_relations':['LATER']})
 def test_A02_no_retro_to_contemporary(self):
  with self.assertRaises(ValueError):self.api('check_tier_result')('CONTEMPORANEOUS',{'supported_portion':'narrow part','evidence_relations':['LATER']})
 def test_A02_unknown_separate(self):self.api('check_tier_result')('AVAILABILITY_UNKNOWN',{'supported_portion':'part','evidence_relations':['UNKNOWN']})
 def test_A02_reject_prior_in_unknown(self):
  with self.assertRaises(ValueError):self.api('check_tier_result')('AVAILABILITY_UNKNOWN',{'supported_portion':'part','evidence_relations':['PRIOR']})
 def test_A03_mixed_success_precedence(self):
  x=[{'attempt_id':'1','call_relation':'PRIOR','result_relation':'PRIOR','result_state':'SUCCESS','truncation_state':'NONE','target_match':True},{'attempt_id':'2','call_relation':'PRIOR','result_relation':None,'result_state':None,'truncation_state':None,'target_match':True}]
  out=self.api('derive_ce_act')(x);self.assertEqual(out['act'],'PRESENT');self.assertEqual(out['partial_attempt_ids'],['2'])
 def test_A03_partial_only(self):self.assertEqual(self.api('derive_ce_act')([{'attempt_id':'1','call_relation':'PRIOR','result_relation':None,'result_state':None,'truncation_state':None,'target_match':True}])['act'],'PARTIAL')
 def test_A03_unknown_not_partial(self):self.assertEqual(self.api('derive_ce_act')([{'attempt_id':'1','call_relation':'UNKNOWN','result_relation':'UNKNOWN','result_state':'SUCCESS','truncation_state':'NONE','target_match':True}])['act'],'ABSENT')
 def manifest(self):return {'nodes':[{'node_id':'M000001','seq':1,'turn_id':'T000001','assistant_context_visibility':'VISIBLE'}],'turns':[{'turn_id':'T000001','interleaving_status':'NOT_APPLICABLE'}],'sources':[{'source_id':'SRC000001','availability_basis':'RECORD_EVIDENCED','available_first_seq':1}]}
 def test_A04_source_anchor(self):self.assertEqual(g.relation(self.manifest(),'SRC000001',['M000001'],evidence_kind='SOURCE'),'LATER')
 def test_A04_node_still_excluded(self):self.assertEqual(g.relation(self.manifest(),'M000001',['M000001']),'SELF_EXCLUDED')
 def raw(self):
  i={'inventory_id':'I1','run_id':'R1','run_version':1,'apk_sha256':'a'*64,'inventory_schema_version':'PA-INV-0.5','claims':[]};i['inventory_sha256']=g.digest(i,'inventory_sha256');return json.dumps(i).encode()
 def test_A06_valid_receipt(self):
  raw=self.raw();receipt=self.api('make_inventory_receipt')(raw,'b'*64);self.api('verify_inventory_receipt')(raw,receipt,{'inventory_id':'I1','run_id':'R1','run_version':1,'apk_sha256':'a'*64,'inventory_stage_cdm_sha256':'b'*64})
 def test_A06_missing_receipt(self):
  with self.assertRaises(ValueError):self.api('verify_inventory_receipt')(self.raw(),None,{})
 def test_A06_wrong_run(self):
  raw=self.raw();receipt=self.api('make_inventory_receipt')(raw,'b'*64)
  with self.assertRaises(ValueError):self.api('verify_inventory_receipt')(raw,receipt,{'inventory_id':'I1','run_id':'R2','run_version':1,'apk_sha256':'a'*64,'inventory_stage_cdm_sha256':'b'*64})
 def test_A06_wrong_stage(self):
  raw=self.raw();receipt=self.api('make_inventory_receipt')(raw,'b'*64)
  with self.assertRaises(ValueError):self.api('verify_inventory_receipt')(raw,receipt,{'inventory_id':'I1','run_id':'R1','run_version':1,'apk_sha256':'a'*64,'inventory_stage_cdm_sha256':'c'*64})
 def test_A06_raw_bytes_binding(self):
  raw=self.raw();receipt=self.api('make_inventory_receipt')(raw,'b'*64)
  with self.assertRaises(ValueError):self.api('verify_inventory_receipt')(raw+b' ',receipt,{'inventory_id':'I1','run_id':'R1','run_version':1,'apk_sha256':'a'*64,'inventory_stage_cdm_sha256':'b'*64})
if __name__=='__main__':unittest.main(verbosity=2)
