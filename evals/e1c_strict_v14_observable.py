"""Multi-evidence structural projection for strict-v14 development."""
from __future__ import annotations
import hashlib,json,re
from evals.e1c_strict_v13_observable import observable_contracts as v13_contracts

_WORD=re.compile(r"[A-Za-z_][A-Za-z0-9_]*")
_BEHAVIOR=re.compile(r"(?i)\b(?:fail(?:s|ed|ing)?|crash(?:es|ed|ing)?|error|wrong|unexpected|should|expected|allow|refuse[sd]?|ignore[sd]?|preserve[sd]?)\b")
_STOP={'the','and','for','with','from','this','that','when','then','should','expected','error','wrong','fails','failed','crashes','unexpected'}

def _tokens(text): return {x.lower() for x in _WORD.findall(text) if len(x)>2 and x.lower() not in _STOP}

def _structural(issue,loc):
 issue_tokens=_tokens(issue); scored=[]
 for x in loc.get('candidates',[]):
  path=str(x.get('path') or ''); sym=str(x.get('symbol') or ''); origin=str(x.get('origin') or '')
  if not path.endswith('.py') or not sym: continue
  st=_tokens(sym); pt=_tokens(path.replace('/',' ')); overlap=(st|pt)&issue_tokens
  score=4*len(st&issue_tokens)+len(pt&issue_tokens)+(3 if origin=='issue_ast_definition' else 0)
  if score: scored.append((score,path,sym,origin,sorted(overlap)))
 if not scored:return None
 scored.sort(reverse=True); best=scored[0]; runner=scored[1][0] if len(scored)>1 else -1
 if best[0]<7 or best[0]-runner<3:return None
 return best

def observable_contracts(issue,localization):
 out=list(v13_contracts(issue,localization))
 if _BEHAVIOR.search(issue):
  hit=_structural(issue,localization)
  if hit:
   score,path,sym,origin,evidence=hit
   v={'schema':'e1c-strict-v14-observable-contract-v1','kind':'semantic_postcondition','subject':sym,'verb':'preserve_issue_visible_behavior','object':'','candidate_path':path,'execution_ready':True,'origin':'multi_evidence_structural_binding','provenance':'issue_tokens_plus_ast_symbol_plus_path_margin','benchmark_assertion_used':False,'task_id_used':False,'confidence_evidence':{'score':score,'margin_required':3,'issue_overlap':evidence,'localization_origin':origin}}; v['witness_sha256']=hashlib.sha256(json.dumps(v,sort_keys=True,separators=(',',':')).encode()).hexdigest(); out.append(v)
 seen=set(); result=[]
 for x in out:
  k=x.get('witness_sha256');
  if k not in seen: seen.add(k); result.append(x)
 return result
