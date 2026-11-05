"""Deterministic routing of declared judgments. No text classification/model/Join."""
LEGAL=(('PRESENT','FITS'),('PRESENT','PARTIAL'),('PRESENT','DOES_NOT_FIT'),('PRESENT','NOT_ASSESSABLE'),('ABSENT','NOT_APPLICABLE'),('UNCLEAR','NOT_ASSESSABLE'))
CRITERIA=('MET','NOT_MET','UNCLEAR')
CATEGORIES={f'B{i:02}' for i in range(1,18)}-{'B11','B12'}
def category_result(stage,category,criteria,ib=None,arb=None,material=None,missing=None,b07=None):
    if stage not in ('YES','NO','UNCLEAR') or category not in CATEGORIES:return 'PROTOCOL_ERROR'
    if stage!='YES':
        if ib is not None or arb is not None:return 'PROTOCOL_ERROR'
        return 'STAGE1_'+stage
    if ib not in LEGAL or arb not in LEGAL or criteria not in CRITERIA:return 'PROTOCOL_ERROR'
    if category=='B07':
        if b07 not in CRITERIA or b07!=criteria:return 'PROTOCOL_ERROR'
        return {'MET':'POSITIVE_FINDING','NOT_MET':'NO_POSITIVE_FINDING','UNCLEAR':'UNRESOLVED'}[b07]
    if b07 is not None:return 'PROTOCOL_ERROR'
    if criteria!='MET':return 'NO_POSITIVE_FINDING' if criteria=='NOT_MET' else 'UNRESOLVED'
    governing=ib if ib[0]=='PRESENT' else arb if arb[0]=='PRESENT' else None
    if governing:
        fit=governing[1]
        if fit=='FITS':return 'NO_POSITIVE_FINDING'
        if fit=='NOT_ASSESSABLE':return 'UNRESOLVED'
        if fit=='DOES_NOT_FIT':return 'POSITIVE_FINDING'
        if type(material) is not bool:return 'PROTOCOL_ERROR'
        return 'POSITIVE_FINDING' if material else 'NO_POSITIVE_FINDING'
    if ib[0]=='ABSENT' and arb[0]=='ABSENT':
        return {'YES':'POSITIVE_FINDING','NO':'NO_POSITIVE_FINDING','UNCLEAR':'UNRESOLVED'}.get(missing,'PROTOCOL_ERROR')
    return 'UNRESOLVED'

def all_not_met_event(category_records):
    """Only the explicitly authorized all-NOT-MET aggregation; no fallback category."""
    if not category_records or len({x['category'] for x in category_records})!=len(category_records):raise ValueError('missing/duplicate categories')
    if any(x['category'] not in CATEGORIES or x['criteria'] not in CRITERIA for x in category_records):raise ValueError('invalid category criteria')
    if all(x['criteria']=='NOT_MET' for x in category_records):return 'NO_POSITIVE_FINDING'
    return None # Other event-level rollups are outside this narrow correction.
