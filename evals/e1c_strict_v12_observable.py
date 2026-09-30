"""Generic semantic-clause to production-localization projection.

Development-only until a strict-v12 prereg freezes this file.  The projector
does not know benchmark identities or assertions; it binds issue-visible
call/symbol tokens to independently produced localization candidates.
"""
from __future__ import annotations
import hashlib,json,re
from evals.e1c_strict_v5_boundary import audit_repair_visible_payload
from evals.e1c_strict_v11_observable import observable_contracts as v11_contracts

_TOKEN=re.compile(r"\b([A-Za-z_]\w*)\s*(?=\()")
_BAD=re.compile(r"(?i)\b(?:fail(?:s|ed|ing)?|crash(?:es|ed|ing)?|error|wrong|refuse[sd]?|too aggressive|unexpected)\b")
_GOOD=re.compile(r"(?i)\b(?:works?|succeed|should|expected|allow|let)\b")
_STOP={'print','def','class','str','int','len','list','dict','set','super'}

def _candidates(localization):
 return [x for x in localization.get('candidates',[]) if isinstance(x,dict) and isinstance(x.get('path'),str) and x['path'].endswith('.py')]

def _unique_symbol(localization, token):
 exact=[]
 for x in _candidates(localization):
  if str(x.get('symbol') or '').lower()==token.lower(): exact.append(x)
 paths=list(dict.fromkeys(x['path'] for x in exact))
 return paths[0] if len(paths)==1 else None

def _contract(token,path,polarity):
 v={'schema':'e1c-strict-v12-observable-contract-v1','kind':'nonfailure_postcondition' if polarity=='bad' else 'semantic_postcondition','subject':token,'verb':'must_not_fail' if polarity=='bad' else 'preserve_expected_behavior','object':'','candidate_path':path,'execution_ready':True,'origin':'generic_clause_symbol_binding','provenance':'issue_semantic_clause_plus_unique_production_symbol','benchmark_assertion_used':False,'task_id_used':False}; audit_repair_visible_payload(v); v['witness_sha256']=hashlib.sha256(json.dumps(v,sort_keys=True,separators=(',',':')).encode()).hexdigest(); return v

def observable_contracts(issue,localization):
 out=list(v11_contracts(issue,localization)); sentences=re.split(r'(?<=[.!?])\s+|[\r\n]+',issue)
 for s in sentences:
  polarity='bad' if _BAD.search(s) else ('good' if _GOOD.search(s) else None)
  if not polarity: continue
  for token in dict.fromkeys(_TOKEN.findall(s)):
   if token.lower() in _STOP: continue
   path=_unique_symbol(localization,token)
   if path: out.append(_contract(token,path,polarity))
 seen=set(); result=[]
 for x in out:
  k=x.get('witness_sha256');
  if k not in seen: seen.add(k); result.append(x)
 return result
