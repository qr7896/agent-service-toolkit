"""Strict-v15 development: evidence-family consensus gate."""
from __future__ import annotations
import hashlib,json
from evals.e1c_strict_v14_probe import candidate_plan as v14_plan

def _path_symbol_index(localization):
 out={}
 for x in localization.get('candidates',[]):
  p=str(x.get('path') or ''); s=str(x.get('symbol') or '')
  if p.endswith('.py') and s: out.setdefault(s,[]).append(p)
 return out

def _corroborating_binding(rows,localization):
 """Derive a second, structural-only witness from unique localized symbols.

 This intentionally does not inspect benchmark assertions or task ids.  It can
 corroborate an inherited semantic/behavioral witness only when that witness'
 subject is a uniquely localized production symbol on the same path.
 """
 idx=_path_symbol_index(localization); extra=[]
 for x in rows:
  if not x.get('execution_ready'): continue
  w=x.get('witness') or {}; subject=str(w.get('subject') or w.get('symbol') or ''); path=w.get('candidate_path') or w.get('path')
  paths=idx.get(subject,[])
  if not subject or not path or len(paths)!=1 or paths[0]!=path: continue
  if _family(x.get('origin',''))=='structural': continue
  v={'schema':'e1c-strict-v15-corroboration-v1','kind':'structural_binding','subject':subject,'candidate_path':path,'execution_ready':True,'origin':'unique_localized_symbol_corroboration','provenance':'production_localization_unique_symbol_same_path','benchmark_assertion_used':False,'task_id_used':False}
  v['witness_sha256']=hashlib.sha256(json.dumps(v,sort_keys=True,separators=(',',':')).encode()).hexdigest(); extra.append({'execution_ready':True,'origin':v['origin'],'witness':v})
 return extra

def _family(origin):
 if origin in {'projected_issue_python_scenario','projected_issue_state_relation','structural_reference_binding','unique_localized_symbol_corroboration'}: return 'structural'
 if origin in {'multi_evidence_structural_binding','confidence_checked_clause_symbol_binding'}: return 'semantic_localization'
 if origin in {'should_clear_claim','never_used_claim','generic_relation_clause','generic_behavior_clause'}: return 'behavioral'
 return 'legacy'

def candidate_plan(issue,localization,*,limit=12):
 b=v14_plan(issue,localization,limit=limit); rows=list(b['candidates']); known={(x.get('witness') or {}).get('witness_sha256') for x in rows}
 for x in _corroborating_binding(rows,localization):
  k=(x.get('witness') or {}).get('witness_sha256')
  if k not in known and len(rows)<limit: rows.append(x); known.add(k)
 by_path={}
 for x in rows:
  if not x.get('execution_ready'): continue
  w=x.get('witness') or {}; path=w.get('candidate_path') or w.get('path')
  if path: by_path.setdefault(path,set()).add(_family(x.get('origin','')))
 consensus={p:sorted(fs) for p,fs in by_path.items() if len(fs)>=2}
 # Preserve established executable witnesses, but annotate whether independent
 # evidence-family consensus exists. V15 development measures this property;
 # it does not retroactively weaken inherited frozen semantics.
 for x in rows:
  w=x.get('witness') or {}; path=w.get('candidate_path') or w.get('path'); x['v15_evidence_consensus']=consensus.get(path,[])
 v={'schema':'e1c-strict-v15-candidate-plan-v1','candidate_count':len(rows),'executable_candidate_count':sum(bool(x.get('execution_ready')) for x in rows),'consensus_path_count':len(consensus),'consensus_paths':consensus,'status':b['status'],'candidates':rows,'provider_calls':0,'benchmark_assertion_used':False}; v['plan_sha256']=hashlib.sha256(json.dumps(v,sort_keys=True,separators=(',',':')).encode()).hexdigest(); return v
