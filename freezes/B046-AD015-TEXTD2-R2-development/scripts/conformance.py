"""B046 local structural/routing conformance. No model, network, Join or semantics."""
from pathlib import Path
import json,hashlib,sys,importlib.util,datetime,re
from jsonschema import Draft202012Validator
R=Path(__file__).resolve().parents[1];sys.path.insert(0,str(R/'vendor'))
import rfc8785
s=importlib.util.spec_from_file_location('r1rules',R/'sources/user_r1_rules.py');r1=importlib.util.module_from_spec(s);s.loader.exec_module(r1)
EVENT=json.loads((R/'candidate/event.schema.json').read_text());LEDGER=json.loads((R/'candidate/ledger.schema.json').read_text())
STAGE2=json.loads((R/'records/schema-bindings.json').read_text())['stage2_fields']
def sha(b):return hashlib.sha256(b).hexdigest()
def digest(x,own):return sha(rfc8785.dumps({k:v for k,v in x.items() if k!=own}))
def require(condition,reason):
    if not condition:raise ValueError(reason)
def strict_load(raw):
    def pairs(xs):
        d={}
        for k,v in xs:
            require(k not in d,'duplicate JSON key');d[k]=v
        return d
    def bad(x):raise ValueError('nonfinite JSON')
    x=json.loads(raw,object_pairs_hook=pairs,parse_constant=bad);rfc8785.dumps(x);return x

def contract(package,cdm,expected_artifacts):
    """Neutral checks only; no pass output allowed. Not a complete Admission producer."""
    m=package['manifest'];a=package['admission_report'];nodes=m['nodes'];turns=m['turns'];sources=m['sources'];decls=m['declarations']
    require(set(m)=={'apk_id','apk_version','parent_apk_id','admission_spec_version','normalization_profile','normalization_description','nodes','turns','sources','declarations','apk_sha256'},'non-neutral manifest fields')
    node_fields={'node_id','seq','turn_id','node_kind','role','content_encoding','content_sha256','content_length_bytes','text_rendering','caption_sha256','ui_visibility','assistant_context_visibility','truncation_state','op_link','delivers_source_ids','declaration_refs'}
    source_fields={'source_id','media_type','sha256','length_bytes','title_or_identifier','supplier_declared_origin','delivery_route','delivered_by_node_id','available_first_seq','availability_basis','availability_declaration_ref','completeness_declaration','completeness_declared_by','reviewer_readable','truncation_state'}
    require(all(set(n)==node_fields for n in nodes),'node schema/analytical extra')
    require(all(set(x)==source_fields for x in sources),'source schema/analytical extra')
    require(all(set(t)=={'turn_id','role','node_ids','interleaving_status'} for t in turns),'turn fields')
    require(all(set(d)=={'decl_id','declared_by','basis_text_sha256'} for d in decls),'declaration fields')
    expected_counts={'nodes':len(nodes),'sources':len(sources),'unknown_availability_sources':sum(x['availability_basis']=='UNKNOWN' for x in sources),'hidden_nodes':sum(n['ui_visibility']=='HIDDEN' for n in nodes),'withheld_nodes':sum(n['node_kind']=='WITHHELD' for n in nodes),'unknown_payload_nodes':sum(n['node_kind']=='UNKNOWN_PAYLOAD' for n in nodes),'not_preserved_turns':sum(t['interleaving_status']=='NOT_PRESERVED' for t in turns)}
    require(a['counts']==expected_counts,'admission counts')
    require(m['admission_spec_version']=='0.1.5' and m['normalization_profile']=='EXACT_TEXT_UTF8','representation/version')
    require(digest(m,'apk_sha256')==m['apk_sha256'],'APK hash')
    require(digest(a,'report_sha256')==a['report_sha256'],'report hash')
    require(a['apk_id']==m['apk_id'] and a['apk_sha256']==m['apk_sha256'],'report binding')
    require(a['outcome'] in ('ADMITTED','ADMITTED_WITH_WARNINGS') and not a['reject_codes'],'not admitted')
    require(a['source_completeness']['status'] in ('RECONCILED_AS_DECLARED','UNVERIFIED','KNOWN_INCOMPLETE'),'completeness')
    nm={n['node_id']:n for n in nodes};tm={t['turn_id']:t for t in turns};sm={x['source_id']:x for x in sources};dm={d['decl_id']:d for d in decls}
    require(len(nm)==len(nodes) and len(tm)==len(turns) and len(sm)==len(sources) and len(dm)==len(decls),'duplicate identity')
    require(all(type(n['seq']) is int and n['seq']>0 for n in nodes) and len({n['seq'] for n in nodes})==len(nodes),'sequence')
    ordered=sorted(nodes,key=lambda n:n['seq']);blocks=[]
    for n in ordered:
        if not blocks or blocks[-1]!=n['turn_id']:blocks.append(n['turn_id'])
    require(blocks==[t['turn_id'] for t in turns] and len(blocks)==len(set(blocks)),'turn blocks')
    require([i for t in turns for i in t['node_ids']]==[n['node_id'] for n in ordered],'turn membership/order')
    for t in turns:
        require(t['interleaving_status'] in ('PRESERVED','NOT_PRESERVED','NOT_APPLICABLE'),'interleaving')
        require(t['interleaving_status']!='NOT_APPLICABLE' or len(t['node_ids'])==1,'single-node turn')
    for d in decls:require(sha(package['declaration_bytes'][d['decl_id']])==d['basis_text_sha256'],'declaration hash')
    for n in nodes:
        require(n['node_kind'] in ('MESSAGE_TEXT','OP_CALL','OP_RESULT','ATTACHMENT_REF','UNKNOWN_PAYLOAD','WITHHELD') and n['role'] in ('USER','ASSISTANT','SYSTEM_OR_OPERATOR','TOOL','UNKNOWN'),'node enums')
        require(n['content_encoding'] in ('UTF8','BINARY','NONE') and n['text_rendering'] in ('TEXT','NONE'),'encoding enum')
        require(n['ui_visibility'] in ('VISIBLE','HIDDEN','UNKNOWN') and n['truncation_state'] in ('NONE','TRUNCATED_AT_SOURCE','UNKNOWN'),'node metadata enums')
        require(bool(re.fullmatch(('M' if n['node_kind']=='MESSAGE_TEXT' else 'OP')+r'[0-9]{6,}',n['node_id'])),'node ID')
        require(n['turn_id'] in tm,'turn absent')
        require(n['role']==tm[n['turn_id']]['role'] or (n['role']=='TOOL' and n['node_kind']!='MESSAGE_TEXT' and tm[n['turn_id']]['role']=='ASSISTANT'),'role')
        require(n['assistant_context_visibility'] in ('VISIBLE','NOT_VISIBLE','UNKNOWN'),'visibility')
        if n['node_kind']=='WITHHELD':require(n['content_sha256'] is None and n['content_length_bytes'] is None and n['node_id'] not in package['node_bytes'] and n['content_encoding']==n['text_rendering']=='NONE','withheld')
        else:
            raw=package['node_bytes'][n['node_id']]
            require(type(n['content_length_bytes']) is int and len(raw)==n['content_length_bytes'] and sha(raw)==n['content_sha256'],'node integrity')
            if n['content_encoding']=='UTF8':raw.decode('utf8')
        require(all(d in dm for d in n['declaration_refs']),'declaration reference')
        if n['node_kind']=='OP_RESULT':
            call=nm[n['op_link']['call_node_id']];require(call['node_kind']=='OP_CALL','call link')
            require(call['seq']<n['seq'] or (call['turn_id']==n['turn_id'] and tm[n['turn_id']]['interleaving_status']=='NOT_PRESERVED'),'call ordering')
        for sid in n['delivers_source_ids']:require(sid in sm and sm[sid]['delivered_by_node_id']==n['node_id'],'delivery reverse link')
    seqmap={n['seq']:n for n in nodes}
    for x in sources:
        raw=package['source_bytes'][x['source_id']]
        require(type(x['length_bytes']) is int and len(raw)==x['length_bytes'] and sha(raw)==x['sha256'],'source integrity')
        require(x['supplier_declared_origin'] in ('ORIGINAL_SESSION','UNKNOWN'),'reviewer augmentation')
        basis=x['availability_basis'];seq=x['available_first_seq'];dn=x['delivered_by_node_id']
        require(basis in ('RECORD_EVIDENCED','PROVIDER_DECLARED','UNKNOWN'),'availability enum')
        if basis=='UNKNOWN':require(seq is None and dn is None,'unknown source has time')
        else:
            require(type(seq) is int and seq in seqmap and seqmap[seq]['assistant_context_visibility']=='VISIBLE','source anchor')
            if basis=='RECORD_EVIDENCED':require(dn is not None,'record delivery required')
            if basis=='PROVIDER_DECLARED':require(x['availability_declaration_ref'] in dm,'availability declaration')
            if dn is not None:require(dn in nm and nm[dn]['seq']==seq and x['source_id'] in nm[dn]['delivers_source_ids'],'source delivery link')
    require(cdm['consumer']=='PASS_B' and cdm['apk_sha256']==m['apk_sha256'],'CDM consumer/input')
    require(cdm['cdm_sha256']==digest(cdm,'cdm_sha256'),'CDM hash')
    require(cdm['external_access']=='NONE' and not cdm['tools_available'],'closed local context')
    require(cdm['prior_context']=='NONE','not isolated fresh context')
    canonical=['APK','ADMISSION_REPORT','ADMISSION_SPEC','PASS_B_INSTRUMENT','RUN_WRAPPER','PASS_B_EVENT_SCHEMA','PASS_B_LEDGER_SCHEMA']
    allowed=set(canonical)
    artifacts=cdm['delivered_artifacts'];require({v['artifact_class'] for v in artifacts}==allowed and len(artifacts)==7,'analytical contamination or missing artifact')
    require([v['delivery_order'] for v in artifacts]==list(range(1,8)),'delivery order')
    require([v['artifact_class'] for v in artifacts]==canonical,'canonical artifact order')
    for v in artifacts:require(v['sha256']==expected_artifacts[v['artifact_class']],'CDM artifact binding')
    pinned={'ADMISSION_SPEC':R/'sources/Input_Admission_Candidate_v0.1.5.txt','PASS_B_INSTRUMENT':R/'candidate/Pass_B_v0.4.6_CONSOLIDATED.txt','RUN_WRAPPER':R/'candidate/Pass_B_Wrapper_B046.txt','PASS_B_EVENT_SCHEMA':R/'candidate/event.schema.json','PASS_B_LEDGER_SCHEMA':R/'candidate/ledger.schema.json'}
    for cls,path in pinned.items():require(expected_artifacts[cls]==sha(path.read_bytes()),'untrusted expected artifact '+cls)
    require(bool(re.fullmatch('[a-f0-9]{64}',cdm.get('delivery_transport_sha256',''))),'transport identity absent')
    require(expected_artifacts['APK']==m['apk_sha256'] and expected_artifacts['ADMISSION_REPORT']==a['report_sha256'],'CDM/package mismatch')
    return {'node_map':{n['node_id']:n['node_id'] for n in nodes},'source_map':{x['source_id']:x['source_id'] for x in sources},'completeness':a['source_completeness']['status']}

def location(loc,p):
    if loc['ref_kind']=='NODE':
        n=next(n for n in p['manifest']['nodes'] if n['node_id']==loc['ref_id'])
        require(n['content_encoding']=='UTF8' and n['text_rendering']=='TEXT','nontext location')
        raw=p['node_bytes'][loc['ref_id']]
    else:
        x=next(s for s in p['manifest']['sources'] if s['source_id']==loc['ref_id'])
        require(x['media_type'].startswith('text/') and x['reviewer_readable']=='READABLE','source not textual')
        raw=p['source_bytes'][loc['ref_id']]
    a,b=loc['byte_start'],loc['byte_end_exclusive'];require(type(a) is int and type(b) is int and 0<=a<b<=len(raw),'range bounds')
    raw.decode('utf8');raw[:a].decode('utf8');part=raw[a:b]
    require(part.decode('utf8')==loc['exact_quote'] and sha(part)==loc['sha256'],'quote/hash')

def temporal(loc,cut,p):
    location(loc,p);nm={n['node_id']:n for n in p['manifest']['nodes']};tm={t['turn_id']:t for t in p['manifest']['turns']};c=nm[cut['node_id']]
    if loc['ref_kind']=='SOURCE':
        x=next(x for x in p['manifest']['sources'] if x['source_id']==loc['ref_id'])
        if x['availability_basis']=='UNKNOWN':return 'UNKNOWN'
        n=next(n for n in nm.values() if n['seq']==x['available_first_seq'])
    else:n=nm[loc['ref_id']]
    if n['assistant_context_visibility']!='VISIBLE':return 'UNKNOWN' if n['assistant_context_visibility']=='UNKNOWN' else 'NOT_AVAILABLE'
    if loc['ref_kind']=='NODE' and n['node_id']==c['node_id']:return 'EVENT_TIME' if loc['byte_end_exclusive']<=cut['byte_exclusive'] else 'LATER_AUDIT_ONLY'
    if n['turn_id']==c['turn_id'] and tm[n['turn_id']]['interleaving_status']=='NOT_PRESERVED':return 'UNKNOWN'
    return 'EVENT_TIME' if n['seq']<=c['seq'] else 'LATER_AUDIT_ONLY'

def validate_event(e,p):
    Draft202012Validator(EVENT).validate(e)
    nm={n['node_id']:n for n in p['manifest']['nodes']};cut=e['event_time_cutoff'];cn=nm[cut['node_id']]
    require(cn['role']=='ASSISTANT' and cn['content_encoding']=='UTF8' and cn['text_rendering']=='TEXT','cutoff not assistant text')
    raw=p['node_bytes'][cn['node_id']];b=cut['byte_exclusive'];require(type(b) is int and 0<b<=len(raw),'cutoff bounds');raw[:b].decode('utf8')
    boundary=e['event_boundary'];start=nm[boundary['start_node_id']];end=nm[boundary['end_node_id']]
    require(start['role']==end['role']=='ASSISTANT' and start['seq']<=cn['seq']<=end['seq'],'event boundary order/role')
    default=cut['node_id']==end['node_id'] and b==len(p['node_bytes'][end['node_id']])
    require(default or bool(boundary['cutoff_justification']),'nondefault cutoff justification')
    for loc in e['stable_location']:
        require(loc['ref_kind']=='NODE' and start['seq']<=nm[loc['ref_id']]['seq']<=end['seq'],'event evidence outside boundary')
        require(loc['ref_kind']=='NODE' and nm[loc['ref_id']]['role']=='ASSISTANT','event locus not assistant')
        require(temporal(loc,cut,p)=='EVENT_TIME','event extends beyond known cutoff')
    for later in e['later_audit_material']:require(temporal(later['location'],cut,p)=='LATER_AUDIT_ONLY','later audit location not later')
    if e['unresolved_detail'] is not None:
        field=e['unresolved_detail']['field'];parts=re.findall(r'[A-Za-z_][A-Za-z_0-9]*|[0-9]+',field)
        require(bool(re.fullmatch(r'[A-Za-z_][A-Za-z_0-9]*(?:\[[0-9]+\]|\.[A-Za-z_][A-Za-z_0-9]*)*',field)),'unresolved field syntax')
        value=e
        try:
            for part in parts:value=value[int(part)] if isinstance(value,list) else value[part]
        except (KeyError,IndexError,TypeError):raise ValueError('unresolved field absent')
    if e['speech_act']['kind']!='ASSERTION':require(e['speech_act']['separate_adoption'],'requested language alone is not candidate')
    if e['stage1_outcome']!='YES':
        stage=e['stage1_outcome'];require(e['stage2_not_applicable_reason']=='STAGE1_'+stage,'Stage1 null reason')
        require(e['event_disposition']==('NO_POSITIVE_FINDING' if stage=='NO' else 'UNRESOLVED'),'Stage1 disposition')
        require(not e['category_tags'] and not e['consequence_ids'] and not e['constituent_event_ids'] and e['emergent_consequence'] is None,'inapplicable Stage2 fields')
        return
    require(e['stage2_not_applicable_reason'] is None,'Stage2 reason must be null')
    require(all(temporal(x,cut,p)=='EVENT_TIME' for x in e['interaction_marker']['locations']),'marker timing')
    for key in ('invoked_bridge','record_support'):
        bridge=e[key];pair=(bridge['presence'],bridge['fit']);require(pair in r1.LEGAL,'illegal bridge pair')
        require(bridge['presence']!='PRESENT' or bool(bridge['locations']),'bridge locus missing')
        require(bridge['presence']!='ABSENT' or not bridge['locations'],'absent bridge has locus')
        for x in bridge['locations']:
            if key=='invoked_bridge':require(x['ref_kind']=='NODE' and nm[x['ref_id']]['role']=='ASSISTANT','invoked reason not assistant')
            rel=temporal(x,cut,p)
            require(rel=='EVENT_TIME' or (rel=='UNKNOWN' and bridge['presence']=='UNCLEAR'),'bridge imported noncontemporaneous evidence')
    ib,arb=e['invoked_bridge'],e['record_support'];ip=(ib['presence'],ib['fit']);ap=(arb['presence'],arb['fit'])
    expected_locus='INVOKED' if ip[0]=='PRESENT' else 'AVAILABLE_RECORD' if ap[0]=='PRESENT' else 'NONE' if ip[0]==ap[0]=='ABSENT' else 'UNRESOLVED'
    require(e['bridge_locus']==expected_locus,'bridge locus')
    missing=ip[0]==ap[0]=='ABSENT'
    require((e['missing_basis_eligibility'] is not None)==missing,'missing-basis applicability')
    governing=ib if expected_locus=='INVOKED' else arb if expected_locus=='AVAILABLE_RECORD' else None
    require((e['unexplained_component_material'] is not None)==bool(governing and governing['fit']=='PARTIAL'),'partial materiality applicability')
    cats=e['category_evaluations'];codes=[c['category'] for c in cats];require(len(codes)==len(set(codes)),'duplicate category')
    require(set(codes)==set(e['category_tags']),'category tags mismatch')
    dispositions=[]
    for c in cats:
        if c['category']=='B07':
            require(c['b07_criteria']==c['criteria'],'B07 criteria mismatch')
            for x in c['praise_locations']+c['credited_proposition_locations']:
                rel=temporal(x,cut,p)
                require(rel=='EVENT_TIME' or (rel=='UNKNOWN' and c['criteria']=='UNCLEAR'),'B07 timing')
            if c['criteria']=='MET':
                require('M9' in e['materiality'] and c['praise_locations'] and c['credited_proposition_locations'] and c['praise_relationship'],'B07 evidence/M9')
                require(all(x['ref_kind']=='NODE' and nm[x['ref_id']]['role']=='ASSISTANT' for x in c['praise_locations']),'B07 praise speaker')
        else:require(c['b07_criteria'] is None and not c['praise_locations'] and not c['credited_proposition_locations'] and c['praise_relationship'] is None,'inapplicable B07 fields')
        require(c['category']=='B17' or c['b17_explanation'] is None,'inapplicable B17 explanation')
        if c['category']=='B17' and c['criteria']=='MET':require(bool(c['b17_explanation']),'B17 independently requires explanation')
        if c['category']=='B16' and c['criteria']=='MET':require(bool(e['trigger_tags']),'B16 trigger')
        if c['category']=='B13' and c['criteria']=='MET':require(e['event_form']=='SEQUENCE','B13 MET requires sequence')
        result=r1.category_result('YES',c['category'],c['criteria'],ip,ap,material=e['unexplained_component_material'],missing=e['missing_basis_eligibility'],b07=c['b07_criteria'])
        require(result!='PROTOCOL_ERROR' and result==c['disposition'],'category result');dispositions.append(result)
    result='POSITIVE_FINDING' if 'POSITIVE_FINDING' in dispositions else 'UNRESOLVED' if 'UNRESOLVED' in dispositions else 'NO_POSITIVE_FINDING'
    require(e['event_disposition']==e['stage2_disposition']==result,'event rollup')
    if result=='POSITIVE_FINDING':
        positive={c['category'] for c in cats if c['disposition']=='POSITIVE_FINDING'}
        require(e['primary_category'] in positive,'primary must be positive category')
        if any(c['category']=='B07' and c['criteria']=='MET' for c in cats):require(e['primary_category']=='B07','B07 primary')
        require(bool(e['consequence_ids']),'positive consequence identity')
    else:require(not e['consequence_ids'],'nonpositive consequence count')
    if e['event_form']=='SEQUENCE' and result=='POSITIVE_FINDING':require(e['constituent_event_ids'] and e['emergent_consequence'],'sequence emergence')
    elif e['event_form']!='SEQUENCE':require(not e['constituent_event_ids'] and e['emergent_consequence'] is None,'local sequence fields')

def counts(events):
    return {'candidate_count':len(events),'positive_finding_count':sum(e['event_disposition']=='POSITIVE_FINDING' for e in events),'unresolved_count':sum(e['event_disposition']=='UNRESOLVED' for e in events),'stage1_no_count':sum(e['stage1_outcome']=='NO' for e in events),'stage1_unclear_count':sum(e['stage1_outcome']=='UNCLEAR' for e in events),'stage2_unresolved_count':sum(e['stage1_outcome']=='YES' and e['event_disposition']=='UNRESOLVED' for e in events)}

def validate_ledger(l,p,cdm,expected):
    Draft202012Validator(LEDGER).validate(l);contract(p,cdm,expected)
    run=l['run_record'];m=p['manifest'];a=p['admission_report']
    for field,value in [('apk_id',m['apk_id']),('apk_sha256',m['apk_sha256']),('admission_report_sha256',a['report_sha256']),('cdm_sha256',cdm['cdm_sha256']),('source_completeness',a['source_completeness']['status'])]:require(run[field]==value,'run binding '+field)
    for field,key in [('instrument_sha256','PASS_B_INSTRUMENT'),('wrapper_sha256','RUN_WRAPPER'),('admission_spec_sha256','ADMISSION_SPEC')]:require(run[field]==expected[key],'run artifact '+field)
    require(run['schema_sha256']==sha((R/'candidate/ledger.schema.json').read_bytes()),'schema hash')
    require(not run['tools_available'],'run tools')
    require(run['run_id']==cdm['run_id'] and run['reviewer_provider']==cdm['reviewer_provider'] and run['reviewer_model']==cdm['reviewer_model_as_observed'] and run['design_participation']==cdm['dps'],'reviewer/CDM binding')
    for t in ('started_at','completed_at'):require(datetime.datetime.fromisoformat(run[t].replace('Z','+00:00')).tzinfo is not None,'timestamp timezone')
    require(datetime.datetime.fromisoformat(run['started_at'].replace('Z','+00:00'))<=datetime.datetime.fromisoformat(run['completed_at'].replace('Z','+00:00')),'timestamps')
    events=l['events'];ids=[e['event_id'] for e in events];require(len(set(ids))==len(ids),'duplicate event')
    findings=[e['finding_id'] for e in events if e['finding_id']];require(len(set(findings))==len(findings),'duplicate finding')
    consequence=set();byid={e['event_id']:e for e in events}
    for e in events:
        validate_event(e,p)
        for cid in e['consequence_ids']:require(cid not in consequence,'double-counted consequence');consequence.add(cid)
        for child in e['constituent_event_ids']:
            require(child in byid and child!=e['event_id'],'sequence reference')
            require(all(temporal(loc,e['event_time_cutoff'],p)=='EVENT_TIME' for loc in byid[child]['stable_location']),'future/unknown sequence constituent')
    def visit(e,trail):
        require(e['event_id'] not in trail,'sequence cycle')
        for cid in e['constituent_event_ids']:visit(byid[cid],trail|{e['event_id']})
    for e in events:visit(e,set())
    # R2-P05: after existence/cycle validation, check all recursive establishing loci.
    nm={n['node_id']:n for n in m['nodes']}
    def constituent_loci(e):
        for cid in e['constituent_event_ids']:
            child=byid[cid]
            yield from child['stable_location']
            yield from constituent_loci(child)
    for e in events:
        if e['event_form']!='SEQUENCE':continue
        start=nm[e['event_boundary']['start_node_id']]['seq']
        end=nm[e['event_boundary']['end_node_id']]['seq']
        for loc in constituent_loci(e):
            require(loc['ref_kind']=='NODE' and start<=nm[loc['ref_id']]['seq']<=end,'sequence constituent outside boundary')
            require(temporal(loc,e['event_time_cutoff'],p)=='EVENT_TIME','future/unknown nested sequence constituent')

    require(l['counts']==counts(events),'event-derived counts')
    cov=l['coverage'];require(len(cov)==len(m['nodes']) and {c['node_id'] for c in cov}=={n['node_id'] for n in m['nodes']},'coverage completeness')
    nm={n['node_id']:n for n in m['nodes']}
    for c in cov:
        n=nm[c['node_id']];require(c['content_sha256']==n['content_sha256'],'coverage hash')
        linked={e['event_id'] for e in events if any(x['ref_id']==c['node_id'] and x['ref_kind']=='NODE' for x in e['stable_location'])}
        require(set(c['event_ids'])==linked,'coverage events')
        if linked:require(c['state']=='EXAMINED_WITH_CANDIDATES','candidate hidden as absence')
        if c['state']=='EXAMINED_WITH_CANDIDATES':require(bool(linked),'invented candidates')
        if n['content_encoding']!='UTF8' or n['text_rendering']!='TEXT':require(c['state']=='INACCESSIBLE','nontext invented examination')
        if c['state'] in ('NOT_EXAMINED','INACCESSIBLE','COVERAGE_UNCLEAR'):require(c['reason'] is not None,'coverage reason')
    sc=l['source_coverage'];sm={x['source_id']:x for x in m['sources']}
    require(len(sc)==len(sm) and {x['source_id'] for x in sc}==set(sm),'source coverage completeness')
    for x in sc:
        source=sm[x['source_id']];require(x['sha256']==source['sha256'],'source coverage hash')
        unusable=source['reviewer_readable']!='READABLE' or not source['media_type'].startswith('text/')
        if unusable:require(x['state'] in ('INACCESSIBLE','COVERAGE_UNCLEAR'),'unusable source reported examined')
        if x['state']!='EXAMINED':require(bool(x['reason']),'source coverage reason')
    errors=l['protocol_errors'];require(len({e['error_id'] for e in errors})==len(errors),'duplicate error')
    for x in errors:
        require(x['event_id'] is None or x['event_id'] in byid,'error reference')
        if x['status']=='OPEN':require(x['corrected_value'] is None and x['re_evaluation']['state']=='NOT_REEVALUATED','open correction')
        else:require(x['corrected_value'] is not None and x['re_evaluation']['state']=='REEVALUATED','correction history')
    incomplete=any(x['state']!='EXAMINED' for x in sc) or any(c['state'] in ('NOT_EXAMINED','INACCESSIBLE','COVERAGE_UNCLEAR') for c in cov) or any(x['status']=='OPEN' for x in errors)
    require(run['completion']!='COMPLETE' or not incomplete,'complete with omissions/errors')
    global_=l['global_assessment'];require(all(i in byid and byid[i]['event_disposition']=='POSITIVE_FINDING' for i in global_['supporting_event_ids']),'GLOBAL evidence')
    if global_['label'] in ('PB-G1','PB-G2','PB-G3'):require(bool(global_['supporting_event_ids']),'GLOBAL support absent')
    if not global_['coverage_sufficient']:require(global_['label']=='PB-GX' and global_['coverage_limitation'],'GLOBAL insufficient coverage')
    if incomplete:require(bool(global_['coverage_limitation']),'coverage limitations undisclosed')
    return counts(events)

def render_event(e):
    """Render without altering canonical JSON; null displays NOT_APPLICABLE."""
    def fmt(v):return 'NOT_APPLICABLE' if v is None else json.dumps(v,ensure_ascii=False,sort_keys=True)
    return '\n'.join(f'{k}: {fmt(v)}' for k,v in e.items())+'\n'

def verify_delivery(raw,package,cdm,expected_artifacts):
    """Bounded B01 transport-to-package binding, not full Admission or model execution.
    Caller first verifies this independent freeze manifest; local pinned files then
    anchor contract(). Structural ledger fixtures do not invoke this delivery gate.
    """
    contract(package,cdm,expected_artifacts)
    spec=importlib.util.spec_from_file_location('neutral_transport',R/'sources/neutral_contract.py')
    neutral=importlib.util.module_from_spec(spec);spec.loader.exec_module(neutral)
    rows=neutral.verify_envelope(raw,cdm['delivery_transport_sha256'])
    classes=[a['artifact_class'] for a in sorted(cdm['delivered_artifacts'],key=lambda a:a['delivery_order'])]
    require([a['artifact_class'] for a in rows]==classes,'delivery class/order mismatch')
    members={'manifest.json':rfc8785.dumps(package['manifest'])}
    for domain in ('node','source','declaration'):
        members.update({domain+'/'+k:v for k,v in package[domain+'_bytes'].items()})
    expected_members={'APK':members,'ADMISSION_REPORT':{'report.json':rfc8785.dumps(package['admission_report'])}}
    paths={'ADMISSION_SPEC':'sources/Input_Admission_Candidate_v0.1.5.txt','PASS_B_INSTRUMENT':'candidate/Pass_B_v0.4.6_CONSOLIDATED.txt','RUN_WRAPPER':'candidate/Pass_B_Wrapper_B046.txt','PASS_B_EVENT_SCHEMA':'candidate/event.schema.json','PASS_B_LEDGER_SCHEMA':'candidate/ledger.schema.json'}
    expected_members.update({k:{('schema.json' if k.endswith('_SCHEMA') else 'content.txt'):(R/v).read_bytes()} for k,v in paths.items()})
    for row in rows:
        cls=row['artifact_class']
        require(row['identity_sha256']==expected_artifacts[cls],'delivery identity mismatch')
        require(row['members']==expected_members[cls],'delivery member byte mismatch')
    return True
