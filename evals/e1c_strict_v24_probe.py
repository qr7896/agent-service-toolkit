"""Strict-v24 development: taxonomy correction for issue-described scenarios.

Development-only successor to sealed V23.  This changes no evidence producer:
an already-produced ``projected_issue_python_scenario`` is classified as
behavioral because its provenance is an explicit behavior/scenario described
by the issue, rather than production structure.
"""
from __future__ import annotations
import hashlib,json
from evals.e1c_strict_v23_probe import candidate_plan as v23_plan, _v23_family

def _v24_family(origin):
    if origin == 'projected_issue_python_scenario': return 'behavioral'
    return _v23_family(origin)

def candidate_plan(issue,localization,*,source_root=None,limit=12):
    b=v23_plan(issue,localization,source_root=source_root,limit=limit);rows=list(b['candidates']);by={}
    for x in rows:
        if not x.get('execution_ready'):continue
        w=x.get('witness') or {};p=w.get('candidate_path') or w.get('path')
        if p:by.setdefault(p,set()).add(_v24_family(x.get('origin','')))
    consensus={p:sorted(fs) for p,fs in by.items() if len(fs)>=2}
    v={'schema':'e1c-strict-v24-candidate-plan-v1','candidate_count':len(rows),'executable_candidate_count':sum(bool(x.get('execution_ready')) for x in rows),'consensus_path_count':len(consensus),'consensus_paths':consensus,'status':b['status'],'candidates':rows,'provider_calls':0,'benchmark_assertion_used':False};v['plan_sha256']=hashlib.sha256(json.dumps(v,sort_keys=True,separators=(',',':')).encode()).hexdigest();return v
