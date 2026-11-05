# Architecture and operational boundary

Neutral specifies admission, content identity and text transport. Admission 0.1.5 distinguishes original raw JSON/JCS evidence, canonical identities, completeness declarations and exact source bytes. Bounded helpers implement only part of the requirements; passing them is not full Admission.

Pass A 0.5 concerns claim/source support and evidence timing. Its Neutral R1 binding remains unchanged. Pass B 0.4.6 concerns event criteria and ledger structure under Neutral R2. They are separate components; this package establishes neither a paired execution workflow nor Join eligibility.

B's canonical class order is APK, ADMISSION_REPORT, ADMISSION_SPEC, PASS_B_INSTRUMENT, RUN_WRAPPER, PASS_B_EVENT_SCHEMA, PASS_B_LEDGER_SCHEMA. APK uses manifest.json and domain-qualified members; the report uses report.json; normative text classes use content.txt; schema classes use schema.json. Exact names, order and bytes matter.

B13 MET requires a SEQUENCE event. Every constituent establishing locus must be contained recursively within its sequence boundary and satisfy event-time restrictions. Later information cannot repair an invalid event-time boundary.

Operator R2.1 specifies independent trusted-pin acquisition and detached preflight receipts. Its comparator checks supplied bindings; it does not authenticate an operator or create a trust root. R3.1 clarifies selection of exactly one verified receipt for the specific run and stage and preserves UNKNOWN historical dependency provenance. The overlay does not replace runnable pins or analytical artifacts.

Before any separately authorized assessment, full external Admission, original raw/JCS and canonicality evidence, verified freeze identities, CDM/delivery binding, actual transport compatibility, isolation and exactly one independently verified receipt are required. Preserve tools_available=[], prior_context NONE and external_access NONE. Stop on a missing, unverified, ambiguous or mismatched prerequisite. Temporary browser mode or old readability probes do not establish isolation. Read the exact Operator PREFLIGHT-R2.txt and both R3.1 supplements under freezes; this overview does not supersede them.
