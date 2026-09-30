from __future__ import annotations
import hashlib,json
from evals.e1c_strict_v9_probe import candidate_plan as v9_plan
from evals.e1c_strict_v10_observable import observable_contracts
def candidate_plan(issue,localization,*,limit=12):
 base=v9_plan(issue,localization,limit=limit); rows=list(base['candidates']); known=set()
 for r in rows:
  w=r.get('witness') or r.get('freeze',{}).get('witness') or {}; known.add(w.get('witness_sha256'))
 for w in observable_contracts(issue,localization):
  if w['witness_sha256'] not in known: rows.append({'execution_ready':True,'origin':w['origin'],'witness':w}); known.add(w['witness_sha256'])
 rows=rows[:limit]; n=sum(bool(r.get('execution_ready')) for r in rows); v={'schema':'e1c-strict-v10-candidate-plan-v1','candidate_count':len(rows),'executable_candidate_count':n,'status':'candidate_executable_witnesses' if n else 'no_executable_reproducer','candidates':rows,'provider_calls':0,'benchmark_assertion_used':False}; v['plan_sha256']=hashlib.sha256(json.dumps(v,sort_keys=True,separators=(',',':')).encode()).hexdigest(); return v
