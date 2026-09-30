"""Strict-v23 development: V20-compatible family aggregation plus V22 override."""
from __future__ import annotations
import hashlib,json
from evals.e1c_strict_v21_probe import candidate_plan as v21_plan, _family

_STRUCTURAL={'explicit_callable_same_module_corroboration','relation_object_unique_type_corroboration','issue_attribute_unique_property_corroboration','full_source_unique_attribute_assignment_corroboration','issue_noun_bounded_full_source_assignment','explicit_callable_issue_type_corroboration'}
def _v23_family(origin):
    if origin in {'explicit_issue_callable_binding','explicit_issue_ownership_clause_binding'}: return 'semantic_localization'
    if origin in _STRUCTURAL:return 'structural'
    return _family(origin)

def candidate_plan(issue,localization,*,source_root=None,limit=12):
    b=v21_plan(issue,localization,source_root=source_root,limit=limit);rows=list(b['candidates']);by={}
    for x in rows:
        if not x.get('execution_ready'):continue
        w=x.get('witness') or {};p=w.get('candidate_path') or w.get('path')
        if p:by.setdefault(p,set()).add(_v23_family(x.get('origin','')))
    consensus={p:sorted(fs) for p,fs in by.items() if len(fs)>=2}
    v={'schema':'e1c-strict-v23-candidate-plan-v1','candidate_count':len(rows),'executable_candidate_count':sum(bool(x.get('execution_ready')) for x in rows),'consensus_path_count':len(consensus),'consensus_paths':consensus,'status':b['status'],'candidates':rows,'provider_calls':0,'benchmark_assertion_used':False};v['plan_sha256']=hashlib.sha256(json.dumps(v,sort_keys=True,separators=(',',':')).encode()).hexdigest();return v
