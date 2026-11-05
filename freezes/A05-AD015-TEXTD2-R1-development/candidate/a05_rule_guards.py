"""Limited executable rule guards for A0.5/Admission0.1.5.
NOT an admission certifier, semantic classifier, B implementation or Join.
A clean result means these guards passed, not that all instrument gates passed.
"""
import hashlib,json,re
import rfc8785

def sha(b): return hashlib.sha256(b).hexdigest()
def digest(obj, own): return sha(rfc8785.dumps({k:v for k,v in obj.items() if k!=own}))
def integer(x): return type(x) is int

def load_strict(raw):
    def pairs(items):
        out={}
        for key,value in items:
            if key in out: raise ValueError('duplicate JSON key')
            out[key]=value
        return out
    def invalid(x): raise ValueError('nonfinite number')
    obj=json.loads(raw,object_pairs_hook=pairs,parse_constant=invalid)
    rfc8785.dumps(obj) # also rejects surrogate strings and non-JCS values
    return obj

def admission_guards(manifest,report,node_bytes,source_bytes):
    """Return a list of mechanical defects; do not emit ADMITTED."""
    errors=[]
    def check(ok,code):
        if not ok: errors.append(code)
    try:
        check(manifest['admission_spec_version']=='0.1.5','VERSION')
        check(manifest['normalization_profile']=='EXACT_TEXT_UTF8','NORMALIZATION')
        check(manifest['apk_sha256']==digest(manifest,'apk_sha256'),'APK_HASH')
        check(report['report_sha256']==digest(report,'report_sha256'),'REPORT_HASH')
        check(report['apk_sha256']==manifest['apk_sha256'] and report['apk_id']==manifest['apk_id'],'REPORT_BINDING')
        check(report['outcome'] in ('ADMITTED','ADMITTED_WITH_WARNINGS') and not report['reject_codes'],'REJECTED')
        nodes=manifest['nodes']; turns=manifest['turns']; sources=manifest['sources']
        nm={n['node_id']:n for n in nodes}; tm={t['turn_id']:t for t in turns}; sm={s['source_id']:s for s in sources}
        check(len(nm)==len(nodes) and len(tm)==len(turns) and len(sm)==len(sources),'DUPLICATE_ID')
        check(all(re.fullmatch(r'T[0-9]{6,}',x) for x in tm),'TURN_ID')
        check(all(re.fullmatch(r'SRC[0-9]{6,}',x) for x in sm),'SOURCE_ID')
        seqs=[n['seq'] for n in nodes]
        check(all(integer(x) and x>0 for x in seqs) and len(set(seqs))==len(seqs),'SEQ')
        seqmap={n['seq']:n for n in nodes}
        members=[x for t in turns for x in t['node_ids']]
        check(len(members)==len(nodes) and set(members)==set(nm) and len(set(members))==len(members),'MEMBERSHIP')
        ordered=sorted(nodes,key=lambda n:n['seq']); seen=[]
        for n in ordered:
            if not seen or seen[-1]!=n['turn_id']:seen.append(n['turn_id'])
        check(len(seen)==len(set(seen)) and seen==[t['turn_id'] for t in turns],'TURN_BLOCK')
        for t in turns:
            check(t['interleaving_status'] in ('PRESERVED','NOT_PRESERVED','NOT_APPLICABLE'),'INTERLEAVING_ENUM')
            check(t['interleaving_status']!='NOT_APPLICABLE' or len(t['node_ids'])==1,'NOT_APPLICABLE_MULTINODE')
            check(t['node_ids']==[n['node_id'] for n in ordered if n['turn_id']==t['turn_id']],'TURN_ORDER')
        for n in nodes:
            nid=n['node_id']; kind=n['node_kind']; t=tm[n['turn_id']]
            check(kind in ('MESSAGE_TEXT','OP_CALL','OP_RESULT','ATTACHMENT_REF','UNKNOWN_PAYLOAD','WITHHELD'),'NODE_KIND')
            check(bool(re.fullmatch(('M' if kind=='MESSAGE_TEXT' else 'OP')+r'[0-9]{6,}',nid)),'NODE_ID')
            check(n['role']==t['role'] or (n['role']=='TOOL' and kind!='MESSAGE_TEXT' and t['role']=='ASSISTANT'),'ROLE')
            check(n['assistant_context_visibility'] in ('VISIBLE','NOT_VISIBLE','UNKNOWN'),'VISIBILITY_ENUM')
            if kind=='WITHHELD':
                check(n['content_sha256'] is None and n['content_length_bytes'] is None and nid not in node_bytes and n['content_encoding']=='NONE' and n['text_rendering']=='NONE','WITHHELD')
            else:
                raw=node_bytes[nid]
                check(type(raw) is bytes and n['content_sha256']==sha(raw),'CONTENT_HASH')
                check(integer(n['content_length_bytes']) and n['content_length_bytes']==len(raw),'CONTENT_LENGTH')
                if n['content_encoding']=='UTF8':raw.decode('utf-8')
            if kind=='OP_RESULT':
                call=nm[n['op_link']['call_node_id']]
                check(call['node_kind']=='OP_CALL','OP_LINK')
                unordered=call['turn_id']==n['turn_id'] and t['interleaving_status']=='NOT_PRESERVED'
                check(unordered or call['seq']<n['seq'],'OP_ORDER')
            for sid in n['delivers_source_ids']:
                check(sm[sid]['delivered_by_node_id']==nid,'RECIPROCAL_DELIVERY')
        for s in sources:
            raw=source_bytes[s['source_id']]
            check(type(raw) is bytes and sha(raw)==s['sha256'],'SOURCE_HASH')
            check(integer(s['length_bytes']) and len(raw)==s['length_bytes'],'SOURCE_LENGTH')
            check(s['supplier_declared_origin'] in ('ORIGINAL_SESSION','UNKNOWN'),'SOURCE_ORIGIN')
            basis=s['availability_basis']; seq=s['available_first_seq']; delivery=s['delivered_by_node_id']
            check(basis in ('UNKNOWN','RECORD_EVIDENCED','PROVIDER_DECLARED'),'AVAILABILITY_ENUM')
            if basis=='UNKNOWN':check(seq is None and delivery is None,'UNKNOWN_AVAILABILITY')
            else:
                check(integer(seq) and seq in seqmap,'AVAILABILITY_ANCHOR')
                anchor=seqmap[seq]
                check(anchor['assistant_context_visibility']=='VISIBLE','AVAILABILITY_VISIBILITY')
                if basis=='RECORD_EVIDENCED':check(delivery is not None,'RECORD_DELIVERY')
                if basis=='PROVIDER_DECLARED':
                    check(s['availability_declaration_ref'] in {d['decl_id'] for d in manifest['declarations']},'PROVIDER_DECLARATION')
                if delivery is not None:
                    check(nm[delivery]['seq']==seq and s['source_id'] in nm[delivery]['delivers_source_ids'],'RECIPROCAL_DELIVERY')
        sc=report['source_completeness']
        check(sc['status'] in ('RECONCILED_AS_DECLARED','UNVERIFIED','KNOWN_INCOMPLETE'),'COMPLETENESS_ENUM')
        check(bool(sc['declared_boundary']),'COMPLETENESS_BOUNDARY')
        if sc['status']=='RECONCILED_AS_DECLARED':
            check(bool(sc['original_artifact_sha256']) and all(sc.get(k) for k in ('original_inventory_sha256','canonical_inventory_sha256','reconciliation_sha256')),'COMPLETENESS_RECEIPTS')
    except (KeyError,TypeError,ValueError,UnicodeError,OverflowError) as e:
        errors.append('MALFORMED:'+type(e).__name__)
    return sorted(set(errors))

def checked_range(raw,start,end,expected_hash):
    if not integer(start) or not integer(end) or not 0<=start<end<=len(raw):raise ValueError('invalid range')
    raw.decode('utf-8');raw[:start].decode('utf-8');text=raw[start:end].decode('utf-8')
    if sha(raw[start:end])!=expected_hash:raise ValueError('quote hash')
    return text

def relation(manifest,evidence_id,claim_node_ids,location_complete=True,evidence_kind='NODE'):
    """Typed temporal boundary. SOURCE ID is never replaced by a node identity."""
    if evidence_kind not in ('NODE','EMBEDDED_SEGMENT','SOURCE'):raise ValueError('evidence kind')
    nm={n['node_id']:n for n in manifest['nodes']};tm={t['turn_id']:t for t in manifest['turns']}
    if evidence_kind!='SOURCE' and evidence_id in claim_node_ids:return 'SELF_EXCLUDED'
    if not location_complete or not claim_node_ids:return 'UNKNOWN'
    if evidence_kind=='SOURCE':
        source=next(s for s in manifest['sources'] if s['source_id']==evidence_id)
        if source['availability_basis']=='UNKNOWN':return 'UNKNOWN'
        e=next(n for n in nm.values() if n['seq']==source['available_first_seq'])
    else:e=nm[evidence_id]
    c=min((nm[x] for x in claim_node_ids),key=lambda n:n['seq'])
    if e['assistant_context_visibility']=='NOT_VISIBLE':return 'NOT_AVAILABLE'
    if e['assistant_context_visibility']=='UNKNOWN':return 'UNKNOWN'
    if e['turn_id']==c['turn_id'] and tm[e['turn_id']]['interleaving_status']=='NOT_PRESERVED':return 'UNKNOWN'
    return 'PRIOR' if e['seq']<c['seq'] else 'LATER'

def consultation_status(polarity,target,act,act_relations,contrary_relations,available,unknown_relevant=False):
    """Given declared judgments, enforce temporal/polarity routing, not semantics."""
    if polarity not in ('AFFIRMATIVE','NEGATIVE','UNCLEAR'):raise ValueError('polarity')
    if polarity!='AFFIRMATIVE':return None
    if act not in ('PRESENT','PARTIAL','ABSENT'):raise ValueError('act')
    if available not in ('YES','NO','UNKNOWN','NOT_APPLICABLE'):raise ValueError('availability')
    if act in ('PRESENT','PARTIAL') and (not act_relations or any(r!='PRIOR' for r in act_relations)):raise ValueError('non-prior access')
    if any(r!='PRIOR' for r in contrary_relations):raise ValueError('non-prior disclaimer')
    if target=='UNRESOLVED':return 'CE5'
    if contrary_relations:return 'CE5' if act=='PRESENT' else 'CE4'
    if act=='PRESENT':return 'CE1'
    if act=='PARTIAL' or available=='YES':return 'CE2'
    if unknown_relevant or available=='UNKNOWN':return 'CE_UNDETERMINED'
    return 'CE3'

def content_complete(scope,items):
    """Completeness prerequisite only; true does not itself assign unsupported."""
    if not scope:return False
    return all(x in items and items[x]['kind']=='SRC' and items[x]['relation']=='PRIOR' and
       items[x]['readable']=='READABLE' and items[x]['completeness']=='COMPLETE_AS_DECLARED' and
       items[x]['search']=='FULL' for x in scope)

def unchanged_inventory(frozen,returned):
    return rfc8785.dumps(frozen)==rfc8785.dumps(returned)

# Bounded R1 checks consume authored records, never discover/assess propositions.
def validate_inventory_units(entries):
    seen=set();ids=set()
    for e in entries:
        if not isinstance(e.get('selected_proposition'),str) or not e['selected_proposition'].strip():raise ValueError('selected proposition')
        key=rfc8785.dumps({k:e.get(k) for k in ('selected_proposition','attribution_target','ranges')})
        if key in seen or e['claim_id'] in ids:raise ValueError('duplicate inventory unit')
        seen.add(key);ids.add(e['claim_id'])
    return True

def check_tier_result(tier,result):
    allowed={'CONTEMPORANEOUS':{'PRIOR'},'AVAILABILITY_UNKNOWN':{'UNKNOWN'},'RETROSPECTIVE':{'PRIOR','UNKNOWN','LATER','NOT_AVAILABLE'}}
    if tier not in allowed or any(x not in allowed[tier] for x in result['evidence_relations']):raise ValueError('tier evidence transfer')
    return True

def derive_ce_act(attempts):
    present=[];partial=[];observations=[];ids=set()
    for a in attempts:
        id=a['attempt_id']
        if id in ids:raise ValueError('duplicate attempt')
        ids.add(id);call=a['call_relation'];result=a['result_relation']
        if call=='PRIOR' and result=='PRIOR' and a['result_state']=='SUCCESS' and a['truncation_state']=='NONE' and a['target_match'] is True:present.append(id)
        elif call=='PRIOR' or result=='PRIOR':partial.append(id)
        else:observations.append(id)
    return {'act':'PRESENT' if present else 'PARTIAL' if partial else 'ABSENT','present_attempt_ids':present,'partial_attempt_ids':partial,'nonconclusive_attempt_ids':observations}

def make_inventory_receipt(raw,stage_cdm_sha256):
    i=load_strict(raw)
    if i.get('inventory_schema_version')!='PA-INV-0.5' or i.get('inventory_sha256')!=digest(i,'inventory_sha256'):raise ValueError('INVENTORY_RECEIPT_MISMATCH')
    if not re.fullmatch('[a-f0-9]{64}',stage_cdm_sha256):raise ValueError('INVENTORY_RECEIPT_MISMATCH')
    receipt={k:i[k] for k in ('inventory_id','run_id','run_version','apk_sha256','inventory_schema_version','inventory_sha256')}
    receipt.update(receipt_schema_version='PA-IR-0.5',inventory_stage_cdm_sha256=stage_cdm_sha256,raw_sha256=sha(raw))
    receipt['receipt_sha256']=digest(receipt,'receipt_sha256');return receipt

def verify_inventory_receipt(raw,receipt,expected):
    if receipt is None:raise ValueError('INVENTORY_RECEIPT_MISSING')
    try:
        actual=make_inventory_receipt(raw,expected['inventory_stage_cdm_sha256'])
        if receipt!=actual or any(actual[k]!=expected[k] for k in ('inventory_id','run_id','run_version','apk_sha256','inventory_stage_cdm_sha256')):raise ValueError('binding')
    except (KeyError,ValueError,TypeError):raise ValueError('INVENTORY_RECEIPT_MISMATCH')
    return True
