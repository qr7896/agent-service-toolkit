"""Strict-v16 development: explicit issue-callable structural corroboration."""
from __future__ import annotations
import hashlib,json,re
from evals.e1c_strict_v15_probe import candidate_plan as v15_plan,_family

_IDENT=re.compile(r'(?<![A-Za-z0-9_])([A-Za-z_][A-Za-z0-9_]{3,})(?![A-Za-z0-9_])')

def _explicit_callable_bindings(issue,localization):
 """Bind only identifiers literally named by the projected issue to a unique
 production definition.  No task ids, benchmark assertions, or outcome labels.
 """
 names=set(_IDENT.findall(issue or '')); defs={}
 for x in localization.get('candidates',[]):
  if x.get('origin')!='issue_ast_definition': continue
  p=str(x.get('path') or ''); s=str(x.get('symbol') or '')
  if p.endswith('.py') and s in names: defs.setdefault(s,[]).append(p)
 out=[]
 for s,paths in defs.items():
  uniq=sorted(set(paths))
  if len(uniq)!=1: continue
  v={'schema':'e1c-strict-v16-explicit-callable-v1','kind':'structural_binding','subject':s,'candidate_path':uniq[0],'execution_ready':True,'origin':'explicit_issue_callable_binding','provenance':'projected_issue_identifier_plus_unique_production_definition','benchmark_assertion_used':False,'task_id_used':False}
  v['witness_sha256']=hashlib.sha256(json.dumps(v,sort_keys=True,separators=(',',':')).encode()).hexdigest(); out.append({'execution_ready':True,'origin':v['origin'],'witness':v})
 return out

def _callable_context_corroboration(issue,localization,rows):
 """Corroborate a behavioral witness when an explicitly named unique callable
 and that witness are localized to the same production module.

 The callable is not treated as proof of the behavior by itself; it only adds
 independent structural localization for an already issue-derived behavior.
 """
 explicit=_explicit_callable_bindings(issue,localization); out=[]
 for e in explicit:
  ep=e['witness']['candidate_path']
  for x in rows:
   if not x.get('execution_ready') or _family(x.get('origin',''))!='semantic_localization': continue
   w=x.get('witness') or {}; wp=w.get('candidate_path') or w.get('path')
   if not wp or wp!=ep: continue
   v={'schema':'e1c-strict-v16-callable-context-v1','kind':'structural_corroboration','subject':w.get('subject'),'callable':e['witness']['subject'],'candidate_path':wp,'execution_ready':True,'origin':'explicit_callable_same_module_corroboration','provenance':'projected_issue_callable_plus_existing_issue_behavior_plus_same_production_path','benchmark_assertion_used':False,'task_id_used':False}
   v['witness_sha256']=hashlib.sha256(json.dumps(v,sort_keys=True,separators=(',',':')).encode()).hexdigest(); out.append({'execution_ready':True,'origin':v['origin'],'witness':v})
 return out

def candidate_plan(issue,localization,*,limit=12):
 b=v15_plan(issue,localization,limit=limit); rows=list(b['candidates']); known={(x.get('witness') or {}).get('witness_sha256') for x in rows}
 for x in _explicit_callable_bindings(issue,localization):
  k=x['witness']['witness_sha256']
  if k not in known and len(rows)<limit: rows.append(x); known.add(k)
 for x in _callable_context_corroboration(issue,localization,rows):
  k=x['witness']['witness_sha256']
  if k not in known and len(rows)<limit: rows.append(x); known.add(k)
 by_path={}
 for x in rows:
  if not x.get('execution_ready'): continue
  w=x.get('witness') or {}; p=w.get('candidate_path') or w.get('path')
  if p: by_path.setdefault(p,set()).add('structural' if x.get('origin') in {'explicit_issue_callable_binding','explicit_callable_same_module_corroboration'} else _family(x.get('origin','')))
 consensus={p:sorted(fs) for p,fs in by_path.items() if len(fs)>=2}
 for x in rows:
  w=x.get('witness') or {}; p=w.get('candidate_path') or w.get('path'); x['v16_evidence_consensus']=consensus.get(p,[])
 v={'schema':'e1c-strict-v16-candidate-plan-v1','candidate_count':len(rows),'executable_candidate_count':sum(bool(x.get('execution_ready')) for x in rows),'consensus_path_count':len(consensus),'consensus_paths':consensus,'status':b['status'],'candidates':rows,'provider_calls':0,'benchmark_assertion_used':False}; v['plan_sha256']=hashlib.sha256(json.dumps(v,sort_keys=True,separators=(',',':')).encode()).hexdigest(); return v
