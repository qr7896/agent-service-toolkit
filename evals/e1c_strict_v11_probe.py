from __future__ import annotations
import hashlib,json
from evals.e1c_strict_v10_probe import candidate_plan as v10_plan
from evals.e1c_strict_v11_observable import observable_contracts
def candidate_plan(issue,localization,*,limit=12):
 b=v10_plan(issue,localization,limit=limit); rows=list(b['candidates']); known={(r.get('witness') or {}).get('witness_sha256') for r in rows}
 for w in observable_contracts(issue,localization):
  if w['witness_sha256'] not in known: rows.append({'execution_ready':True,'origin':w['origin'],'witness':w}); known.add(w['witness_sha256'])
 rows=rows[:limit]; n=sum(bool(x.get('execution_ready')) for x in rows); v={'schema':'e1c-strict-v11-candidate-plan-v1','candidate_count':len(rows),'executable_candidate_count':n,'status':'candidate_executable_witnesses' if n else 'no_executable_reproducer','candidates':rows,'provider_calls':0,'benchmark_assertion_used':False}; v['plan_sha256']=hashlib.sha256(json.dumps(v,sort_keys=True,separators=(',',':')).encode()).hexdigest(); return v
