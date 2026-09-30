"""Strict-v25 development: explicit callable behavioral corroboration."""
from __future__ import annotations
import hashlib,json,re
from evals.e1c_strict_v23_probe import candidate_plan as v23_plan, _v23_family

_BEHAVIOR=re.compile(r'(?i)\b(?:requires?|refuses?|fails?|raises?|errors?|succeeds?|works?|allows?|prevents?|rejects?|accepts?|returns?|checks?|needs?)\b')

def _callable_behavior(issue,rows):
    if not _BEHAVIOR.search(issue): return []
    low=issue.lower();out=[]
    for x in rows:
        if not x.get('execution_ready') or x.get('origin')!='explicit_issue_callable_binding':continue
        w=x.get('witness') or {};name=str(w.get('subject') or w.get('callable') or '').lower();path=w.get('candidate_path') or w.get('path')
        if not name or not path or name not in low:continue
        v={'schema':'e1c-strict-v25-callable-behavior-v1','kind':'behavioral_claim','callable':name,'candidate_path':path,'execution_ready':True,'origin':'explicit_callable_behavior_claim','provenance':'explicit_issue_callable_name_plus_issue_execution_behavior_claim','benchmark_assertion_used':False,'task_id_used':False};v['witness_sha256']=hashlib.sha256(json.dumps(v,sort_keys=True,separators=(',',':')).encode()).hexdigest();out.append({'execution_ready':True,'origin':v['origin'],'witness':v})
    return out

def candidate_plan(issue,localization,*,source_root=None,limit=12):
    b=v23_plan(issue,localization,source_root=source_root,limit=limit);rows=list(b['candidates']);known={(x.get('witness') or {}).get('witness_sha256') for x in rows}
    for x in _callable_behavior(issue,rows):
        k=x['witness']['witness_sha256']
        if k not in known and len(rows)<limit:rows.append(x);known.add(k)
    by={}
    for x in rows:
        if not x.get('execution_ready'):continue
        w=x.get('witness') or {};p=w.get('candidate_path') or w.get('path');o=x.get('origin','');fam='behavioral' if o=='explicit_callable_behavior_claim' else _v23_family(o)
        if p:by.setdefault(p,set()).add(fam)
    consensus={p:sorted(fs) for p,fs in by.items() if len(fs)>=2}
    v={'schema':'e1c-strict-v25-candidate-plan-v1','candidate_count':len(rows),'executable_candidate_count':sum(bool(x.get('execution_ready')) for x in rows),'consensus_path_count':len(consensus),'consensus_paths':consensus,'status':b['status'],'candidates':rows,'provider_calls':0,'benchmark_assertion_used':False};v['plan_sha256']=hashlib.sha256(json.dumps(v,sort_keys=True,separators=(',',':')).encode()).hexdigest();return v
