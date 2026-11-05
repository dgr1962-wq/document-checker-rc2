import unittest,copy,json
from fixtures import c,package,event,setup,location,category,seal,R,node
from jsonschema import ValidationError
ERR=(ValueError,ValidationError,KeyError,UnicodeError,StopIteration)
class Edges(unittest.TestCase):
    def setUp(self):self.l,self.p,self.d,self.x=setup();self.e=self.l['events'][0]
    def valid(self):return c.validate_ledger(self.l,self.p,self.d,self.x)
    def bad(self):
        with self.assertRaises(ERR):self.valid()
    def rebind(self):seal(self.p);self.l,self.p,self.d,self.x=setup(self.l['events'],self.p);self.e=self.l['events'][0]
    def source(self,basis='RECORD_EVIDENCED'):
        raw=b'Explicit original record text.';x={'source_id':'SRC000001','media_type':'text/plain','sha256':c.sha(raw),'length_bytes':len(raw),'title_or_identifier':'Authored fixture source','supplier_declared_origin':'ORIGINAL_SESSION','delivery_route':'ATTACHED_IN_MESSAGE','delivered_by_node_id':'M000001','available_first_seq':1,'availability_basis':basis,'availability_declaration_ref':None,'completeness_declaration':'COMPLETE_AS_DECLARED','completeness_declared_by':'SUPPLIER','reviewer_readable':'READABLE','truncation_state':'NONE'}
        self.p['manifest']['sources']=[x];self.p['source_bytes']['SRC000001']=raw;self.p['manifest']['nodes'][0]['delivers_source_ids']=['SRC000001'];return x,{'ref_kind':'SOURCE','ref_id':'SRC000001','byte_start':0,'byte_end_exclusive':len(raw),'exact_quote':raw.decode(),'sha256':c.sha(raw)}
    def test_65_record_source_identity(self):
        x,loc=self.source();self.rebind();mapping=c.contract(self.p,self.d,self.x);self.assertEqual(mapping['source_map'],{'SRC000001':'SRC000001'});self.assertEqual(c.temporal(loc,self.e['event_time_cutoff'],self.p),'EVENT_TIME');self.valid()
    def test_66_unknown_source_not_present_support(self):
        x,loc=self.source('UNKNOWN');x.update(available_first_seq=None,delivered_by_node_id=None);self.p['manifest']['nodes'][0]['delivers_source_ids']=[];self.rebind();self.assertEqual(c.temporal(loc,self.e['event_time_cutoff'],self.p),'UNKNOWN');self.e['record_support'].update(presence='PRESENT',fit='DOES_NOT_FIT',locations=[loc]);self.e.update(bridge_locus='AVAILABLE_RECORD',missing_basis_eligibility=None);self.bad()
    def test_67_provider_declaration_binding(self):
        x,loc=self.source('PROVIDER_DECLARED');x.update(delivered_by_node_id=None,availability_declaration_ref='DECL000001');self.p['manifest']['nodes'][0]['delivers_source_ids']=[];raw=b'Provider declares availability at node 1';self.p['declaration_bytes']['DECL000001']=raw;self.p['manifest']['declarations']=[{'decl_id':'DECL000001','declared_by':'PROVIDER','basis_text_sha256':c.sha(raw)}];self.rebind();self.valid();self.p['declaration_bytes']['DECL000001']=b'tampered';self.bad()
    def test_68_binary_node_not_text(self):
        n,raw=node(5,'','TOOL','UNKNOWN_PAYLOAD');raw=b'\xff\xfe';n.update(content_encoding='BINARY',text_rendering='NONE',content_sha256=c.sha(raw),content_length_bytes=2);self.p['manifest']['nodes'].append(n);self.p['manifest']['turns'].append({'turn_id':n['turn_id'],'role':'TOOL','node_ids':[n['node_id']],'interleaving_status':'NOT_APPLICABLE'});self.p['node_bytes'][n['node_id']]=raw;self.rebind();self.l['coverage'][-1].update(state='INACCESSIBLE',reason='binary payload');self.l['run_record']['completion']='PARTIAL';self.l['global_assessment'].update(coverage_limitation='Binary source unreadable',coverage_sufficient=False,label='PB-GX');self.valid()
    def test_69_analytical_node_extra(self):self.p['manifest']['nodes'][0]['pass_a_finding']='supported';self.rebind();self.bad()
    def test_70_analytical_manifest_extra(self):self.p['manifest']['classifications']=['supported'];self.rebind();self.bad()
    def test_71_admission_counts_tamper(self):
        a=self.p['admission_report'];a['counts']['nodes']=100;a['report_sha256']=c.digest(a,'report_sha256');self.bad()
    def test_72_protocol_error_fields_required(self):
        record={'error_id':'ERR1','event_id':None,'error_type':'ILLEGAL_PAIR','original_value':['ABSENT','FITS'],'corrected_value':['ABSENT','NOT_APPLICABLE'],'status':'CORRECTED','re_evaluation':{'state':'REEVALUATED','record':'Original preserved; corrected by explicit reevaluation'}}
        for key in record:
            self.l['protocol_errors']=[copy.deepcopy(record)];del self.l['protocol_errors'][0][key];self.bad()
    def test_73_partial_requires_materiality_judgment(self):
        self.e['invoked_bridge'].update(presence='PRESENT',fit='PARTIAL',locations=[location(self.p)]);self.e.update(bridge_locus='INVOKED',missing_basis_eligibility=None);self.bad();self.e['unexplained_component_material']=True;self.valid()
    def test_74_missing_basis_no_not_positive(self):
        self.e.update(missing_basis_eligibility='NO',event_disposition='NO_POSITIVE_FINDING',stage2_disposition='NO_POSITIVE_FINDING',finding_id=None,primary_category=None,severity=None,pass_b_confidence=None,consequence_ids=[]);self.e['category_evaluations'][0]['disposition']='NO_POSITIVE_FINDING';self.l['counts']['positive_finding_count']=0;self.valid()
    def test_75_b07_not_met_does_not_erase_other_category(self):
        self.e['category_evaluations'].append(category('B07','NOT_MET'));self.e['category_tags'].append('B07');self.valid();self.assertEqual(self.e['primary_category'],'B01')
    def test_76_boolean_cutoff_rejected(self):self.e['event_time_cutoff']['byte_exclusive']=True;self.bad()
    def test_77_incomplete_global_not_computed(self):
        self.l['coverage'][2].update(state='NOT_EXAMINED',reason='Unexamined optional context');self.l['run_record']['completion']='PARTIAL';self.l['global_assessment'].update(coverage_limitation='Unexamined context; reviewer declares remaining scope sufficient',coverage_sufficient=True,label='PB-G0');self.valid();self.assertEqual(self.l['global_assessment']['label'],'PB-G0')
    def test_78_run_reviewer_cdm_mismatch(self):self.l['run_record']['reviewer_model']='different';self.bad()
    def test_79_renderer_no_mutation(self):
        e=event(self.p,'NO');before=json.dumps(e,sort_keys=True);text=c.render_event(e);self.assertIn('stage2_disposition: NOT_APPLICABLE',text);self.assertEqual(json.dumps(e,sort_keys=True),before)
    def test_80_future_sequence_constituent_rejected(self):
        child=event(self.p,eid='PE000002',nid='M000004');self.e.update(event_form='SEQUENCE',constituent_event_ids=['PE000002'],emergent_consequence='Too early');self.l,self.p,self.d,self.x=setup([self.e,child],self.p);self.bad()
    def test_81_unresolved_field_must_exist(self):
        e=event(self.p,'UNCLEAR');e['unresolved_detail']['field']='imaginary_field'
        with self.assertRaises(ERR):c.validate_event(e,self.p)
if __name__=='__main__':unittest.main(verbosity=2)
