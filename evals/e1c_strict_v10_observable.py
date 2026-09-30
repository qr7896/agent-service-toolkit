"""Strict-v10 generic issue-to-observable extensions for exposed development only."""
from __future__ import annotations
import hashlib,json,re
from evals.e1c_strict_v5_boundary import audit_repair_visible_payload
from evals.e1c_strict_v9_observable import observable_contracts as v9_contracts

_CRASH = re.compile(r"(?i)\b(?P<action>exclude|filter|create|instantiate|render|build|access|introspect)\s*\([^\n]{0,160}?\)\s*(?:#\s*)?(?P<failure>crashes?|fails?|raises?|errors?)\b")
_RELATION = re.compile(r"(?i)(?:`(?P<quoted>[A-Za-z_]\w*)`|\b(?P<attribute>[A-Za-z_]\w*)\b).{0,40}?\b(?:doesn't|does not|should|must)\s+(?P<verb>point|refer|belong|identify|find)\w*\s+(?P<object>[^.\n]{1,100})")
_LET = re.compile(r"(?i)(?:suggest|expect|should|must|need)\w*.{0,80}?let\s+(?P<subject>\S+)\s+(?P<verb>succeed|work)(?P<object>[^.\n]{0,100})")
_NOT_LINK = re.compile(r"(?i)\b(?P<subject>(?:class|instance|global)?\s*variable(?:\s+documentation)?)\b.{0,120}?\b(?:not|no longer|without)\s+(?:be\s+)?(?P<verb>link|refer)\w*\s+(?P<object>[^.\n]{1,100})")

def _rows(localization): return [r for r in localization.get('candidates',[]) if isinstance(r,dict) and isinstance(r.get('path'),str) and r['path'].endswith('.py')]
def _path(localization,hints=()):
 rows=_rows(localization); hints=[h.lower() for h in hints if h]
 scored=[]
 for r in rows:
  symbol=str(r.get('symbol','')).lower(); path=r['path'].lower(); text=str(r.get('text','')).lower();
  score=0
  for h in hints:
   tokens=[t for t in re.findall(r'[a-z_][a-z0-9_]*',h) if len(t)>2]
   if h and h==symbol: score+=8
   if h and h in symbol: score+=5
   score+=sum(2 for t in tokens if t in symbol)
   score+=sum(1 for t in tokens if t in path)
   score+=min(2,sum(1 for t in tokens if t in text))
  if r.get('origin')=='issue_ast_definition': score+=2
  scored.append((score,r['path']))
 best=max((s for s,_ in scored),default=0); second=max((s for s,_ in scored if s<best),default=-1); paths=list(dict.fromkeys(p for s,p in scored if s==best and (best>0 or len({x['path'] for x in rows})==1)))
 if best>0 and second>=0 and best-second<2: return None
 return paths[0] if len(paths)==1 else None
def _emit(kind,subject,verb,obj,path,origin):
 v={'schema':'e1c-strict-v10-observable-contract-v1','kind':kind,'subject':subject,'verb':verb,'object':obj.strip().lower(),'candidate_path':path,'execution_ready':True,'origin':origin,'provenance':'projected_issue_plus_production_localization','benchmark_assertion_used':False,'task_id_used':False}; audit_repair_visible_payload(v); key=json.dumps(v,sort_keys=True,separators=(',',':')); v['witness_sha256']=hashlib.sha256(key.encode()).hexdigest(); return v
def observable_contracts(issue,localization):
 out=list(v9_contracts(issue,localization))
 for regex,kind,origin in [(_CRASH,'nonfailure_postcondition','generic_inline_failure'),(_RELATION,'semantic_postcondition','generic_relation_clause'),(_LET,'nonfailure_postcondition','generic_let_clause'),(_NOT_LINK,'semantic_postcondition','generic_negative_link_clause')]:
  for m in regex.finditer(issue):
   gd=m.groupdict(); subject=gd.get('action') or gd.get('quoted') or gd.get('attribute') or gd.get('subject') or 'operation'
   context=issue[max(0,m.start()-80):m.end()]
   quoted=re.findall(r'`([A-Za-z_]\w*)`',context)
   if quoted: subject=quoted[-1]
   path=_path(localization,(subject,gd.get('verb'),gd.get('object')))
   if path: out.append(_emit(kind,subject,(gd.get('verb') or 'not_fail').lower(),gd.get('object') or gd.get('failure') or '',path,origin))
 dedup=[]; seen=set()
 for r in out:
  k=r.get('witness_sha256');
  if k in seen: continue
  seen.add(k); dedup.append(r)
 return dedup
