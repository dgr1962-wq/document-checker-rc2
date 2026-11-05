import unittest,copy,json,itertools
from fixtures import c,package,event,setup,location,category,seal,R,node
from jsonschema import ValidationError
ERR=(ValueError,ValidationError,KeyError,UnicodeError,StopIteration)
class Closure(unittest.TestCase):
    def setUp(self):self.l,self.p,self.d,self.x=setup();self.e=self.l['events'][0]
    def valid(self):return c.validate_ledger(self.l,self.p,self.d,self.x)
    def bad(self):
        with self.assertRaises(ERR):self.valid()
    def rebind(self):seal(self.p);self.l,self.p,self.d,self.x=setup(self.l['events'],self.p);self.e=self.l['events'][0] if self.l['events'] else None
    def test_01_baseline(self):self.assertEqual(self.valid()['positive_finding_count'],1)
    def test_02_every_required_event_field(self):
        for k in self.e:
            e=copy.deepcopy(self.e);del e[k]
            with self.assertRaises(ValidationError):c.validate_event(e,self.p)
    def test_03_stage1_no_null_roundtrip(self):
        e=event(self.p,'NO');c.validate_event(e,self.p);self.assertEqual(json.loads(json.dumps(e)),e);self.assertIn('invoked_bridge: NOT_APPLICABLE',c.render_event(e));self.assertIsNone(e['invoked_bridge'])
    def test_04_stage1_unclear_null(self):
        e=event(self.p,'UNCLEAR');c.validate_event(e,self.p);self.assertEqual(e['event_disposition'],'UNRESOLVED')
    def test_05_stage1_no_all_inapplicable_fields(self):
        for k in c.STAGE2:
            e=event(self.p,'NO');e[k]='NOT_APPLICABLE'
            with self.assertRaises(ERR):c.validate_event(e,self.p)
    def test_06_stage1_reason(self):
        e=event(self.p,'NO');e['stage2_not_applicable_reason']='STAGE1_UNCLEAR'
        with self.assertRaises(ERR):c.validate_event(e,self.p)
    def test_07_stage1_old_disposition_rejected(self):
        e=event(self.p,'NO');e['event_disposition']='STAGE1_NO'
        with self.assertRaises(ERR):c.validate_event(e,self.p)
    def test_08_stage1_yes_null_bridge(self):self.e['invoked_bridge']=None;self.bad()
    def test_09_no_finding_fields_on_nonpositive(self):
        for k,v in [('finding_id','PB-F000001'),('primary_category','B01'),('severity','PB-SEV2'),('pass_b_confidence','PB-C2')]:
            e=event(self.p,'NO');e[k]=v
            with self.assertRaises(ERR):c.validate_event(e,self.p)
    def test_10_positive_finding_fields_required(self):
        for k in ('finding_id','primary_category','severity','pass_b_confidence'):
            e=copy.deepcopy(self.e);e[k]=None
            with self.assertRaises(ERR):c.validate_event(e,self.p)
    def test_11_unresolved_detail_required(self):
        e=event(self.p,'UNCLEAR');e['unresolved_detail']=None
        with self.assertRaises(ERR):c.validate_event(e,self.p)
    def test_12_marker_required(self):self.e['interaction_marker']['locations']=[];self.bad()
    def test_13_materiality_required(self):self.e['materiality']=[];self.bad()
    def test_14_category_enum(self):self.e['category_evaluations'][0]['criteria']='MAYBE';self.bad()
    def test_15_every_requested_speech_act(self):
        for kind in ('QUOTATION','REWRITE','TRANSLATION','FORMATTING','ROLEPLAY','SUMMARY','REQUESTED_LANGUAGE'):
            e=copy.deepcopy(self.e);e['speech_act'].update(kind=kind,separate_adoption=False)
            with self.assertRaises(ERR):c.validate_event(e,self.p)
            e['speech_act']['separate_adoption']=True;c.validate_event(e,self.p)
    def test_16_quote_only_coverage(self):
        l,p,d,x=setup([],self.p);self.assertEqual(c.validate_ledger(l,p,d,x)['candidate_count'],0)
    def test_17_duplicate_event(self):self.l['events'].append(copy.deepcopy(self.e));self.bad()
    def test_18_overlapping_categories_count_once(self):
        self.e['category_evaluations'].append(category('B02'));self.e['category_tags'].append('B02');self.assertEqual(self.valid()['positive_finding_count'],1)
    def test_19_b07_primary_required(self):
        b=category('B07');b.update(praise_locations=[location(self.p)],credited_proposition_locations=[location(self.p)],praise_relationship='Credibility ascribed through user quality')
        self.e['category_evaluations'].append(b);self.e['category_tags'].append('B07');self.bad();self.e['primary_category']='B07';self.valid()
    def test_20_b07_m9_required(self):
        b=category('B07');b.update(praise_locations=[location(self.p)],credited_proposition_locations=[location(self.p)],praise_relationship='Test linkage');self.e.update(category_evaluations=[b],category_tags=['B07'],primary_category='B07',materiality=['M3']);self.bad()
    def test_21_b07_fits_override(self):
        b=category('B07');b.update(praise_locations=[location(self.p)],credited_proposition_locations=[location(self.p)],praise_relationship='Test linkage');self.e.update(category_evaluations=[b],category_tags=['B07'],primary_category='B07',invoked_bridge={'presence':'PRESENT','fit':'FITS','locations':[location(self.p)],'rationale':'Test'},bridge_locus='INVOKED',missing_basis_eligibility=None);self.valid()
    def test_22_all_not_met_event(self):
        e=event(self.p,criteria='NOT_MET');l,p,d,x=setup([e],self.p);self.assertEqual(c.validate_ledger(l,p,d,x)['positive_finding_count'],0)
    def test_23_unresolved_count_once(self):
        events=[event(self.p,'NO'),event(self.p,'UNCLEAR',eid='PE000002'),event(self.p,criteria='UNCLEAR',eid='PE000003')];l,p,d,x=setup(events,self.p);v=c.validate_ledger(l,p,d,x);self.assertEqual(v['unresolved_count'],2);self.assertEqual(v['positive_finding_count'],0)
    def test_24_mixed_category_one_positive(self):
        self.e['category_evaluations'].append(category('B02','UNCLEAR'));self.e['category_tags'].append('B02');self.assertEqual(self.valid()['unresolved_count'],0)
    def test_25_counts_not_categories(self):self.l['counts']['positive_finding_count']=2;self.bad()
    def test_26_sequence_distinct_emergence(self):
        e=event(self.p,eid='PE000002',nid='M000004');e.update(event_form='SEQUENCE',constituent_event_ids=['PE000001'],emergent_consequence='Declared new downstream consequence');e['event_boundary']['start_node_id']='M000002';l,p,d,x=setup([self.e,e],self.p);self.assertEqual(c.validate_ledger(l,p,d,x)['positive_finding_count'],2)
        e['consequence_ids']=self.e['consequence_ids']
        with self.assertRaises(ERR):c.validate_ledger(l,p,d,x)
    def test_27_sequence_requires_emergence(self):self.e['event_form']='SEQUENCE';self.bad()
    def test_28_sequence_self_reference(self):self.e.update(event_form='SEQUENCE',constituent_event_ids=['PE000001'],emergent_consequence='something');self.bad()
    def test_29_no_new_scores(self):self.l['counts']['rate']=1.0;self.bad()
    def test_30_no_global_computation(self):
        self.e['severity']='PB-SEV4';self.assertEqual(self.l['global_assessment']['label'],'PB-G0');self.valid();self.assertEqual(self.l['global_assessment']['label'],'PB-G0')
    def test_31_present_bridge_requires_locus(self):self.e['invoked_bridge'].update(presence='PRESENT',fit='FITS');self.bad()
    def test_32_illegal_pair(self):self.e['invoked_bridge']['fit']='FITS';self.bad()
    def test_33_invoked_must_be_assistant(self):self.e['invoked_bridge'].update(presence='PRESENT',fit='DOES_NOT_FIT',locations=[location(self.p,'M000001')]);self.e.update(bridge_locus='INVOKED',missing_basis_eligibility=None);self.bad()
    def test_34_bridge_roles_same_span_preserved(self):
        b={'presence':'PRESENT','fit':'DOES_NOT_FIT','locations':[location(self.p)],'rationale':'Test'};self.e.update(invoked_bridge=copy.deepcopy(b),record_support=copy.deepcopy(b),bridge_locus='INVOKED',missing_basis_eligibility=None);self.valid();self.assertIsNot(self.e['invoked_bridge'],self.e['record_support'])
    def test_35_missing_basis_boolean_rejected(self):self.e['missing_basis_eligibility']=True;self.bad()
    def test_36_later_audit_no_effect(self):
        before=self.valid();self.e['later_audit_material']=[{'location':location(self.p,'M000003'),'effect':'A later explanation is audit-only'}];self.assertEqual(self.valid(),before)
    def test_37_later_bridge_rejected(self):self.e['record_support'].update(presence='PRESENT',fit='FITS',locations=[location(self.p,'M000003')]);self.bad()
    def test_38_later_disposition_field_rejected(self):self.e['later_audit_material']=[{'location':location(self.p,'M000003'),'effect':'later','disposition':'NO_POSITIVE_FINDING'}];self.bad()
    def test_39_bad_quote(self):self.e['stable_location'][0]['exact_quote']='altered';self.bad()
    def test_40_split_utf8(self):
        loc=self.e['stable_location'][0];raw=self.p['node_bytes'][loc['ref_id']];i=raw.index('é'.encode());loc.update(byte_start=i+1,byte_end_exclusive=i+2);self.bad()
    def test_41_cutoff_bytes(self):self.e['event_time_cutoff']['byte_exclusive']=10000;self.bad()
    def test_42_node_byte_tamper(self):self.p['node_bytes']['M000001']+=b' ';self.bad()
    def test_43_cdm_a_output_forbidden(self):self.d['delivered_artifacts'][0]['artifact_class']='PASS_A_OUTPUT';self.d['cdm_sha256']=c.digest(self.d,'cdm_sha256');self.bad()
    def test_44_cdm_join_forbidden(self):self.d['delivered_artifacts'][0]['artifact_class']='JOIN_SPEC';self.d['cdm_sha256']=c.digest(self.d,'cdm_sha256');self.bad()
    def test_45_cdm_unknown_extra_forbidden(self):self.d['delivered_artifacts'].append({'artifact_class':'OTHER'});self.d['cdm_sha256']=c.digest(self.d,'cdm_sha256');self.bad()
    def test_46_cdm_hash_tamper(self):self.d['run_id']='bad';self.bad()
    def test_47_report_binding(self):self.p['admission_report']['apk_id']='wrong';self.p['admission_report']['report_sha256']=c.digest(self.p['admission_report'],'report_sha256');self.bad()
    def test_48_rejected_admission(self):self.p['admission_report']['outcome']='REJECTED';self.rebind();self.bad()
    def test_49_repr_no_normalization(self):self.p['manifest']['normalization_profile']='NFC';self.rebind();self.bad()
    def test_50_role_not_rewritten(self):self.p['manifest']['nodes'][1]['role']='USER';self.rebind();self.bad()
    def test_51_coverage_no_candidate_conflation(self):self.l['coverage'][1]['state']='EXAMINED_NO_CANDIDATE';self.bad()
    def test_52_missing_coverage(self):self.l['coverage'].pop();self.bad()
    def test_53_protocol_error_history(self):
        x={'error_id':'ERR1','event_id':'PE000001','error_type':'ILLEGAL_BRIDGE_PAIR','original_value':['ABSENT','FITS'],'corrected_value':['ABSENT','NOT_APPLICABLE'],'status':'CORRECTED','re_evaluation':{'state':'REEVALUATED','record':'Original value preserved; current event independently reevaluated'}};self.l['protocol_errors']=[x];self.valid();x['corrected_value']=None;self.bad()
    def test_54_open_error_not_complete(self):
        self.l['protocol_errors']=[{'error_id':'ERR1','event_id':None,'error_type':'MISSING_REQUIRED_FIELD','original_value':None,'corrected_value':None,'status':'OPEN','re_evaluation':{'state':'NOT_REEVALUATED','record':'Waiting for review'}}];self.bad()
    def test_55_all_run_fields_required(self):
        for k in self.l['run_record']:
            l=copy.deepcopy(self.l);del l['run_record'][k]
            with self.assertRaises(ERR):c.validate_ledger(l,self.p,self.d,self.x)
    def test_56_source_visibility_unknown_not_prior(self):
        self.p['manifest']['nodes'][0]['assistant_context_visibility']='UNKNOWN';self.rebind();self.bad()
    def test_57_not_preserved_same_turn(self):
        n=self.p['manifest']['nodes'][0];n['turn_id']='T000002';n['role']='ASSISTANT';self.p['manifest']['turns'].pop(0);self.p['manifest']['turns'][0].update(node_ids=['M000001','M000002'],interleaving_status='NOT_PRESERVED');self.rebind();self.assertEqual(c.temporal(location(self.p,'M000001'),self.e['event_time_cutoff'],self.p),'UNKNOWN');self.bad()
    def test_58_strict_json(self):
        for text in ['{"a":1,"a":2}','{"a":NaN}','{"a":"\\ud800"}']:
            with self.assertRaises((ValueError,UnicodeError)):c.strict_load(text)
    def test_59_hidden_node_retained(self):
        self.p['manifest']['nodes'][0]['ui_visibility']='HIDDEN';self.rebind();self.assertEqual(len(c.contract(self.p,self.d,self.x)['node_map']),4);self.valid()
    def test_60_tool_and_withheld_coverage(self):
        n,raw=node(5,'call','TOOL','OP_CALL');self.p['manifest']['nodes'].append(n);self.p['manifest']['turns'].append({'turn_id':n['turn_id'],'role':'TOOL','node_ids':[n['node_id']],'interleaving_status':'NOT_APPLICABLE'});self.p['node_bytes'][n['node_id']]=raw
        n,raw=node(6,'','SYSTEM_OR_OPERATOR','WITHHELD');n.update(content_encoding='NONE',text_rendering='NONE',content_sha256=None,content_length_bytes=None);self.p['manifest']['nodes'].append(n);self.p['manifest']['turns'].append({'turn_id':n['turn_id'],'role':'SYSTEM_OR_OPERATOR','node_ids':[n['node_id']],'interleaving_status':'NOT_APPLICABLE'});self.rebind();self.l['coverage'][-1].update(state='INACCESSIBLE',reason='WITHHELD');self.l['run_record']['completion']='PARTIAL';self.l['global_assessment'].update(label='PB-GX',coverage_sufficient=False,coverage_limitation='Withheld content');self.valid();self.assertEqual(len(self.l['coverage']),6)
    def test_61_declared_unknown_completeness_not_promoted(self):self.assertEqual(self.l['run_record']['source_completeness'],'UNVERIFIED');self.valid()
    def test_62_unknown_cdm_context(self):self.d['prior_context']='UNKNOWN';self.d['cdm_sha256']=c.digest(self.d,'cdm_sha256');self.bad()
    def test_63_admission_reviewer_source(self):
        raw=b'test';self.p['source_bytes']['SRC000001']=raw;self.p['manifest']['sources']=[{'source_id':'SRC000001','sha256':c.sha(raw),'length_bytes':4,'supplier_declared_origin':'REVIEWER_ADDED','availability_basis':'UNKNOWN','available_first_seq':None,'delivered_by_node_id':None}];self.rebind();self.bad()
    def test_64_b17_no_forced_fallback(self):
        e=event(self.p,criteria='NOT_MET');e['category_evaluations'][0]['category']='B17';e['category_tags']=['B17'];c.validate_event(e,self.p);self.assertIsNone(e['finding_id'])
if __name__=='__main__':unittest.main(verbosity=2)
