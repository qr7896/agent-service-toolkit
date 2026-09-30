"""Strict-v17 development: relation-object type corroboration."""
from __future__ import annotations
import hashlib,json,re
from evals.e1c_strict_v16_probe import candidate_plan as v16_plan,_family

_TYPE_WORD=re.compile(r'\b(?:concrete\s+)?([A-Za-z_][A-Za-z0-9_]*)\b',re.I)

def _relation_type_corroboration(rows,localization):
 """Corroborate an issue-derived relation witness from its object type.

 Requires exactly one case-insensitive production definition for a type token
 from the relation object and exact path agreement with the relation witness.
 Ambiguity or disagreement fails closed.
 """
 defs={}
 for x in localization.get('candidates',[]):
  if x.get('origin')!='issue_ast_definition': continue
  p=str(x.get('path') or ''); s=str(x.get('symbol') or '')
  if p.endswith('.py') and s: defs.setdefault(s.lower(),set()).add(p)
 out=[]
 for x in rows:
  if not x.get('execution_ready') or x.get('origin')!='generic_relation_clause': continue
  w=x.get('witness') or {}; path=w.get('candidate_path'); obj=str(w.get('object') or '')
  tokens=[t.lower() for t in _TYPE_WORD.findall(obj) if len(t)>=4 and t.lower() not in {'concrete','attribute','field','belongs'}]
  matches=[(t,next(iter(defs[t]))) for t in tokens if t in defs and len(defs[t])==1]
  matches=[m for m in matches if m[1]==path]
  if len(matches)!=1: continue
  token,_=matches[0]
  v={'schema':'e1c-strict-v17-relation-type-corroboration-v1','kind':'structural_corroboration','subject':w.get('subject'),'relation_object_type':token,'candidate_path':path,'execution_ready':True,'origin':'relation_object_unique_type_corroboration','provenance':'issue_relation_object_plus_unique_production_type_definition_same_path','benchmark_assertion_used':False,'task_id_used':False}
  v['witness_sha256']=hashlib.sha256(json.dumps(v,sort_keys=True,separators=(',',':')).encode()).hexdigest(); out.append({'execution_ready':True,'origin':v['origin'],'witness':v})
 return out

def candidate_plan(issue,localization,*,limit=12):
 b=v16_plan(issue,localization,limit=limit); rows=list(b['candidates']); known={(x.get('witness') or {}).get('witness_sha256') for x in rows}
 for x in _relation_type_corroboration(rows,localization):
  k=x['witness']['witness_sha256']
  if k not in known and len(rows)<limit: rows.append(x); known.add(k)
 by_path={}
 for x in rows:
  if not x.get('execution_ready'): continue
  w=x.get('witness') or {}; p=w.get('candidate_path') or w.get('path'); origin=x.get('origin','')
  fam='structural' if origin in {'explicit_issue_callable_binding','explicit_callable_same_module_corroboration','relation_object_unique_type_corroboration'} else _family(origin)
  if p: by_path.setdefault(p,set()).add(fam)
 consensus={p:sorted(fs) for p,fs in by_path.items() if len(fs)>=2}
 for x in rows:
  w=x.get('witness') or {}; p=w.get('candidate_path') or w.get('path'); x['v17_evidence_consensus']=consensus.get(p,[])
 v={'schema':'e1c-strict-v17-candidate-plan-v1','candidate_count':len(rows),'executable_candidate_count':sum(bool(x.get('execution_ready')) for x in rows),'consensus_path_count':len(consensus),'consensus_paths':consensus,'status':b['status'],'candidates':rows,'provider_calls':0,'benchmark_assertion_used':False}; v['plan_sha256']=hashlib.sha256(json.dumps(v,sort_keys=True,separators=(',',':')).encode()).hexdigest(); return v
