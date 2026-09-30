"""Strict-v19 development: complete-source assignment corroboration overlay."""
from __future__ import annotations
import ast, hashlib, json, re
from pathlib import Path
from evals.e1c_strict_v18_probe import candidate_plan as v18_plan, _family

_ATTRIBUTE_NOUN=re.compile(r"(?i)\b([A-Za-z_]\w*)\s+attribute\b")

def _self_attribute_assignments(source_root: Path, names:set[str]):
 out={}
 for p in source_root.rglob('*.py'):
  try: tree=ast.parse(p.read_text(encoding='utf-8'))
  except (SyntaxError,UnicodeDecodeError,OSError): continue
  rel=p.relative_to(source_root).as_posix()
  for node in ast.walk(tree):
   targets=[]
   if isinstance(node,(ast.Assign,ast.AnnAssign)): targets=node.targets if isinstance(node,ast.Assign) else [node.target]
   for t in targets:
    if isinstance(t,ast.Attribute) and isinstance(t.value,ast.Name) and t.value.id=='self' and t.attr.lower() in names:
     fn=next((a for a in ast.walk(tree) if isinstance(a,(ast.FunctionDef,ast.AsyncFunctionDef)) and getattr(a,'lineno',10**9)<=node.lineno<=getattr(a,'end_lineno',-1)),None)
     out.setdefault(t.attr.lower(),[]).append({'path':rel,'line':node.lineno,'function':getattr(fn,'name',None)})
 return out

def _full_source_attribute_corroboration(issue,rows,source_root):
 names={m.group(1).lower() for m in _ATTRIBUTE_NOUN.finditer(issue)}
 if not names: return []
 assignments=_self_attribute_assignments(Path(source_root),names); out=[]
 for x in rows:
  if not x.get('execution_ready') or x.get('origin')!='generic_relation_clause': continue
  w=x.get('witness') or {}; subject=str(w.get('subject') or '').lower()
  if subject not in names: continue
  hits=assignments.get(subject,[])
  # Fail closed unless exactly one production file owns assignment sites.
  paths=sorted({h['path'] for h in hits})
  if len(paths)!=1: continue
  path=paths[0]
  v={'schema':'e1c-strict-v19-full-source-attribute-corroboration-v1','kind':'structural_corroboration','subject':subject,'candidate_path':path,'assignment_count':len(hits),'functions':sorted({h['function'] for h in hits if h['function']}),'execution_ready':True,'origin':'full_source_unique_attribute_assignment_corroboration','provenance':'issue_attribute_noun_plus_complete_production_ast_unique_assignment_path','benchmark_assertion_used':False,'task_id_used':False}
  v['witness_sha256']=hashlib.sha256(json.dumps(v,sort_keys=True,separators=(',',':')).encode()).hexdigest(); out.append({'execution_ready':True,'origin':v['origin'],'witness':v})
 return out

def candidate_plan(issue,localization,*,source_root=None,limit=12):
 b=v18_plan(issue,localization,limit=limit); rows=list(b['candidates']); known={(x.get('witness') or {}).get('witness_sha256') for x in rows}
 if source_root:
  for x in _full_source_attribute_corroboration(issue,rows,source_root):
   k=x['witness']['witness_sha256']
   if k not in known and len(rows)<limit: rows.append(x); known.add(k)
 by_path={}
 for x in rows:
  if not x.get('execution_ready'): continue
  w=x.get('witness') or {}; p=w.get('candidate_path') or w.get('path'); origin=x.get('origin','')
  fam='structural' if origin in {'explicit_issue_callable_binding','explicit_callable_same_module_corroboration','relation_object_unique_type_corroboration','issue_attribute_unique_property_corroboration','full_source_unique_attribute_assignment_corroboration'} else _family(origin)
  if p: by_path.setdefault(p,set()).add(fam)
 consensus={p:sorted(fs) for p,fs in by_path.items() if len(fs)>=2}
 v={'schema':'e1c-strict-v19-candidate-plan-v1','candidate_count':len(rows),'executable_candidate_count':sum(bool(x.get('execution_ready')) for x in rows),'consensus_path_count':len(consensus),'consensus_paths':consensus,'status':b['status'],'candidates':rows,'provider_calls':0,'benchmark_assertion_used':False}; v['plan_sha256']=hashlib.sha256(json.dumps(v,sort_keys=True,separators=(',',':')).encode()).hexdigest(); return v
