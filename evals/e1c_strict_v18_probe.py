"""Strict-v18 development: property/setter structural localization overlay.

Development-only and fail-closed: this consumes only already-visible localization
windows and derives structural facts from their Python AST.  It never reads a
sealed canary, benchmark assertion, task id, or hidden evaluator artifact.
"""
from __future__ import annotations
import ast, hashlib, json, re, textwrap
from evals.e1c_strict_v17_probe import candidate_plan as v17_plan, _family

_ATTRIBUTE_NOUN = re.compile(r"(?i)\b([A-Za-z_]\w*)\s+attribute\b")

def _property_symbols(localization):
 out={}
 for row in localization.get('candidates',[]):
  path=str(row.get('path') or '')
  if not path.endswith('.py'): continue
  text=str(row.get('text') or '')
  try: tree=ast.parse(textwrap.dedent(text))
  except SyntaxError: continue
  for node in ast.walk(tree):
   if not isinstance(node,(ast.FunctionDef,ast.AsyncFunctionDef)): continue
   decorators=[]
   for d in node.decorator_list:
    if isinstance(d,ast.Name): decorators.append(d.id)
    elif isinstance(d,ast.Attribute): decorators.append(d.attr)
   if 'property' not in decorators and 'setter' not in decorators: continue
   out.setdefault(node.name.lower(),set()).add(path)
 return out

def _attribute_property_corroboration(issue,rows,localization):
 props=_property_symbols(localization); names={m.group(1).lower() for m in _ATTRIBUTE_NOUN.finditer(issue)}; out=[]
 for x in rows:
  if not x.get('execution_ready') or x.get('origin')!='generic_relation_clause': continue
  w=x.get('witness') or {}; subject=str(w.get('subject') or '').lower(); path=w.get('candidate_path')
  if subject not in names or subject not in props or len(props[subject])!=1 or next(iter(props[subject]))!=path: continue
  v={'schema':'e1c-strict-v18-attribute-property-corroboration-v1','kind':'structural_corroboration','subject':subject,'candidate_path':path,'execution_ready':True,'origin':'issue_attribute_unique_property_corroboration','provenance':'issue_attribute_noun_plus_unique_visible_production_property_same_path','benchmark_assertion_used':False,'task_id_used':False}
  v['witness_sha256']=hashlib.sha256(json.dumps(v,sort_keys=True,separators=(',',':')).encode()).hexdigest(); out.append({'execution_ready':True,'origin':v['origin'],'witness':v})
 return out

def candidate_plan(issue,localization,*,limit=12):
 b=v17_plan(issue,localization,limit=limit); rows=list(b['candidates']); known={(x.get('witness') or {}).get('witness_sha256') for x in rows}
 for x in _attribute_property_corroboration(issue,rows,localization):
  k=x['witness']['witness_sha256']
  if k not in known and len(rows)<limit: rows.append(x); known.add(k)
 by_path={}
 for x in rows:
  if not x.get('execution_ready'): continue
  w=x.get('witness') or {}; p=w.get('candidate_path') or w.get('path'); origin=x.get('origin','')
  fam='structural' if origin in {'explicit_issue_callable_binding','explicit_callable_same_module_corroboration','relation_object_unique_type_corroboration','issue_attribute_unique_property_corroboration'} else _family(origin)
  if p: by_path.setdefault(p,set()).add(fam)
 consensus={p:sorted(fs) for p,fs in by_path.items() if len(fs)>=2}
 for x in rows:
  w=x.get('witness') or {}; p=w.get('candidate_path') or w.get('path'); x['v18_evidence_consensus']=consensus.get(p,[])
 v={'schema':'e1c-strict-v18-candidate-plan-v1','candidate_count':len(rows),'executable_candidate_count':sum(bool(x.get('execution_ready')) for x in rows),'consensus_path_count':len(consensus),'consensus_paths':consensus,'status':b['status'],'candidates':rows,'provider_calls':0,'benchmark_assertion_used':False}; v['plan_sha256']=hashlib.sha256(json.dumps(v,sort_keys=True,separators=(',',':')).encode()).hexdigest(); return v
