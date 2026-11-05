"""Bounded OP-R2.1 receipt comparison; external trusted preflight is mandatory.
No trust acquisition, authenticity proof, full Admission, network or runner.
"""
import datetime,re
FIELDS=('neutral_freeze_id','neutral_manifest_sha256','consumer_freeze_id','consumer_manifest_sha256','admission_spec_sha256','run_id','consumer','stage','admission_spec_version','cdm_raw_sha256','cdm_identity_sha256','delivery_transport_sha256','original_manifest_raw_sha256','original_report_raw_sha256','canonicality_evidence_sha256','verified_at','outcome','independent_pin_status','original_raw_jcs_status')
def validate_receipt(receipt,verified_context):
    """verified_context MUST originate in successful independent external preflight.
    Comparing two caller-authored matching objects cannot satisfy that prerequisite.
    Receipt bytes/hash retention and execution holds remain separate obligations.
    """
    if not isinstance(receipt,dict):raise ValueError('PREFLIGHT_RECEIPT_MISSING')
    if not isinstance(verified_context,dict):raise ValueError('PREFLIGHT_CONTEXT_UNVERIFIED')
    if set(receipt)!=set(FIELDS)|{'receipt_version'} or receipt['receipt_version']!='OP-R2.1':raise ValueError('PREFLIGHT_RECEIPT_FIELDS')
    for key in ('outcome','independent_pin_status','original_raw_jcs_status'):
        if receipt[key]!='VERIFIED' or verified_context.get(key)!='VERIFIED':raise ValueError('PREFLIGHT_UNVERIFIED')
    for key in FIELDS:
        value=receipt[key]
        if not isinstance(value,str) or not value or value!=verified_context.get(key):raise ValueError('PREFLIGHT_RECEIPT_MISMATCH:'+key)
        if key.endswith('_sha256') and not re.fullmatch('[a-f0-9]{64}',value):raise ValueError('PREFLIGHT_DIGEST:'+key)
    if receipt['admission_spec_version']!='0.1.5':raise ValueError('PREFLIGHT_VERSION')
    stages={'PASS_B':{'PASS_B_ASSESSMENT'},'PASS_A':{'PASS_A_INVENTORY','PASS_A_CLASSIFICATION'}}
    if receipt['stage'] not in stages.get(receipt['consumer'],set()):raise ValueError('PREFLIGHT_STAGE')
    try:
        t=datetime.datetime.fromisoformat(receipt['verified_at'].replace('Z','+00:00'))
        if t.utcoffset()!=datetime.timedelta(0):raise ValueError()
    except (ValueError,TypeError):raise ValueError('PREFLIGHT_TIMESTAMP')
    return True
