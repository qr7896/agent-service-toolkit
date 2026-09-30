"""Strict-v22 development: independent semantic/AST callable consensus.

V21 showed that a unique explicit issue-callable binding and an AST-derived
role/type corroboration can agree on a path but were both collapsed into the
same structural family.  V22 treats the issue-text callable binding as
semantic localization and the independently derived production-AST witness as
structural evidence.  The two witnesses have different provenance and neither
uses benchmark assertions, task ids, grader data, or hidden tests.
"""
from __future__ import annotations
import hashlib,json
from evals.e1c_strict_v21_probe import candidate_plan as v21_plan, _family

def _v22_family(origin):
    if origin=='explicit_issue_callable_binding': return 'semantic_localization'
    if origin=='explicit_callable_issue_type_corroboration': return 'structural'
    return _family(origin)

def candidate_plan(issue,localization,*,source_root=None,limit=12):
    b=v21_plan(issue,localization,source_root=source_root,limit=limit);rows=list(b['candidates']);by={}
    for x in rows:
        if not x.get('execution_ready'): continue
        w=x.get('witness') or {};p=w.get('candidate_path') or w.get('path')
        if p: by.setdefault(p,set()).add(_v22_family(x.get('origin','')))
    consensus={p:sorted(fs) for p,fs in by.items() if len(fs)>=2}
    v={'schema':'e1c-strict-v22-candidate-plan-v1','candidate_count':len(rows),'executable_candidate_count':sum(bool(x.get('execution_ready')) for x in rows),'consensus_path_count':len(consensus),'consensus_paths':consensus,'status':b['status'],'candidates':rows,'provider_calls':0,'benchmark_assertion_used':False};v['plan_sha256']=hashlib.sha256(json.dumps(v,sort_keys=True,separators=(',',':')).encode()).hexdigest();return v
