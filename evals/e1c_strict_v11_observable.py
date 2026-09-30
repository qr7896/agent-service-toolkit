"""Strict-v11 structural observable binding; development-only until frozen."""
from __future__ import annotations
import hashlib,json,re
from evals.e1c_strict_v5_boundary import audit_repair_visible_payload
from evals.e1c_strict_v10_observable import observable_contracts as v10_contracts

_FAIL_CALL=re.compile(r"(?i)\b(?P<action>[A-Za-z_]\w*)\s*\([^\n]{0,220}?\)\s*(?:#\s*)?(?:crashes?|fails?|raises?|errors?)\b")
_EXPECTED_UNLINK=re.compile(r"(?i)(?P<subject>(?:class|instance|global)\s+variable(?:\s+documentation)?).{0,100}?(?:not\s+be\s+linked|not\s+link|without\s+linking)")

def _rows(loc): return [x for x in loc.get('candidates',[]) if isinstance(x,dict) and isinstance(x.get('path'),str) and x['path'].endswith('.py')]
def _bind(loc,hints):
 hints=[h.lower() for h in hints if h]; scored=[]
 for x in _rows(loc):
  sym=str(x.get('symbol') or '').lower(); path=x['path'].lower(); origin=str(x.get('origin') or ''); score=0
  for h in hints:
   toks=[t for t in re.findall(r'[a-z_][a-z0-9_]*',h) if len(t)>2]
   if h==sym: score+=12
   elif h in sym: score+=7
   score+=sum(2 for t in toks if t in sym)+sum(1 for t in toks if t in path)
  if origin=='issue_ast_definition': score+=3
  scored.append((score,x['path']))
 if not scored:return None
 best=max(s for s,_ in scored); winners=list(dict.fromkeys(p for s,p in scored if s==best)); runner=max((s for s,_ in scored if s<best),default=-1)
 return winners[0] if best>=5 and len(winners)==1 and (runner<0 or best-runner>=3) else None
def _emit(kind,subject,verb,path,origin):
 v={'schema':'e1c-strict-v11-observable-contract-v1','kind':kind,'subject':subject,'verb':verb,'object':'','candidate_path':path,'execution_ready':True,'origin':origin,'provenance':'projected_issue_plus_production_localization','benchmark_assertion_used':False,'task_id_used':False}; audit_repair_visible_payload(v); v['witness_sha256']=hashlib.sha256(json.dumps(v,sort_keys=True,separators=(',',':')).encode()).hexdigest(); return v
def observable_contracts(issue,localization):
 out=list(v10_contracts(issue,localization))
 for m in _FAIL_CALL.finditer(issue):
  a=m.group('action'); p=_bind(localization,(a,));
  if p: out.append(_emit('nonfailure_postcondition',a,'not_fail',p,'structural_exact_action_binding'))
 for m in _EXPECTED_UNLINK.finditer(issue):
  p=_bind(localization,('project','reference','resolve','link'))
  if p: out.append(_emit('semantic_postcondition',m.group('subject'),'not_link',p,'structural_reference_binding'))
 seen=set(); result=[]
 for x in out:
  k=x.get('witness_sha256');
  if k not in seen: seen.add(k); result.append(x)
 return result
