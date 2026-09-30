"""Strict-v13 conservative semantic projection.

Adds generic confidence/evidence requirements to v12 without benchmark IDs.
Development-only until preregistration freezes this file.
"""
from __future__ import annotations
import hashlib,json,re
from evals.e1c_strict_v12_observable import observable_contracts as v12_contracts

_CALL=re.compile(r"\b([A-Za-z_]\w*)\s*(?=\()")
_POLARITY=re.compile(r"(?i)\b(?:fail(?:s|ed|ing)?|crash(?:es|ed|ing)?|error|wrong|refuse[sd]?|too aggressive|unexpected|works?|succeed|should|expected|allow|let)\b")

def _generic_clause_tokens(issue):
 out=set()
 for sentence in re.split(r'(?<=[.!?])\s+|[\r\n]+',issue):
  if _POLARITY.search(sentence): out.update(_CALL.findall(sentence))
 return {x.lower() for x in out}

def observable_contracts(issue,localization):
 rows=v12_contracts(issue,localization); visible=_generic_clause_tokens(issue); out=[]
 for row in rows:
  if row.get('origin')!='generic_clause_symbol_binding': out.append(row); continue
  subject=str(row.get('subject') or '').lower(); path=str(row.get('candidate_path') or '')
  # V13 accepts a generic projection only when its issue-visible call token is
  # explicitly in a behavior-polarity clause and the projected path is Python.
  # Uniqueness itself remains enforced by v12's binder.
  if subject in visible and path.endswith('.py'):
   v=dict(row); v['schema']='e1c-strict-v13-observable-contract-v1'; v['origin']='confidence_checked_clause_symbol_binding'; v['confidence_evidence']={'issue_behavior_clause':True,'unique_production_symbol':True,'python_path':True}; v.pop('witness_sha256',None); v['witness_sha256']=hashlib.sha256(json.dumps(v,sort_keys=True,separators=(',',':')).encode()).hexdigest(); out.append(v)
 return out
