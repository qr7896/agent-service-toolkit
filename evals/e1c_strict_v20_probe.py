"""Strict-v20 development: issue-noun bounded complete-source dataflow."""
from __future__ import annotations
import ast,hashlib,json,re
from pathlib import Path
from evals.e1c_strict_v19_probe import candidate_plan as v19_plan,_family
_ATTR=re.compile(r'(?i)\b([A-Za-z_]\w*)\s+attribute\b')
_PLURAL_TYPE=re.compile(r'(?i)\b([A-Za-z_]\w*)\s+fields?\b')

def _bounded_attribute_assignments(issue,source_root):
 attrs={m.group(1).lower() for m in _ATTR.finditer(issue)}
 # "image fields" -> ImageField; generic noun morphology, not framework names.
 stems={m.group(1) for m in _PLURAL_TYPE.finditer(issue)}
 suffixes={s.lower()+'field' for s in stems}|({'field'} if stems else set())
 out=[]
 for p in Path(source_root).rglob('*.py'):
  try: tree=ast.parse(p.read_text(encoding='utf-8'))
  except (SyntaxError,UnicodeDecodeError,OSError): continue
  for cls in [n for n in ast.walk(tree) if isinstance(n,ast.ClassDef) and any(n.name.lower().endswith(s) for s in suffixes)]:
   for n in ast.walk(cls):
    targets=n.targets if isinstance(n,ast.Assign) else [n.target] if isinstance(n,ast.AnnAssign) else []
    for t in targets:
     if isinstance(t,ast.Attribute) and isinstance(t.value,ast.Name) and t.value.id=='self' and t.attr.lower() in attrs:
      out.append({'path':p.relative_to(source_root).as_posix(),'class':cls.name,'attribute':t.attr.lower(),'line':n.lineno})
 return out

def _bounded_corroboration(issue,rows,source_root):
 hits=_bounded_attribute_assignments(issue,source_root); paths=sorted({h['path'] for h in hits})
 if len(paths)!=1:return []
 path=paths[0]; out=[]
 for x in rows:
  if not x.get('execution_ready') or x.get('origin')!='generic_relation_clause':continue
  w=x.get('witness') or {}; subject=str(w.get('subject') or '').lower()
  if not any(h['attribute']==subject for h in hits):continue
  v={'schema':'e1c-strict-v20-bounded-attribute-corroboration-v1','kind':'structural_corroboration','subject':subject,'candidate_path':path,'classes':sorted({h['class'] for h in hits}),'execution_ready':True,'origin':'issue_noun_bounded_full_source_assignment','provenance':'issue_type_noun_boundary_plus_complete_production_ast_attribute_assignment','benchmark_assertion_used':False,'task_id_used':False}; v['witness_sha256']=hashlib.sha256(json.dumps(v,sort_keys=True,separators=(',',':')).encode()).hexdigest(); out.append({'execution_ready':True,'origin':v['origin'],'witness':v})
 return out

def _ownership_semantic_binding(issue,source_root):
 """Semantic witness from an explicit 'X belongs to Y' issue clause.

 Structural location is independently established by bounded AST assignment;
 this witness exists only when the issue itself states ownership semantics.
 """
 if not re.search(r'(?i)\b(?:field|attribute)\b[^.\n]{0,220}\bbelongs?\s+to\b',issue): return []
 hits=_bounded_attribute_assignments(issue,source_root); paths=sorted({h['path'] for h in hits})
 if len(paths)!=1:return []
 v={'schema':'e1c-strict-v20-ownership-semantic-binding-v1','kind':'semantic_localization','candidate_path':paths[0],'execution_ready':True,'origin':'explicit_issue_ownership_clause_binding','provenance':'explicit_issue_belongs_to_clause_plus_issue_noun_type_boundary','benchmark_assertion_used':False,'task_id_used':False};v['witness_sha256']=hashlib.sha256(json.dumps(v,sort_keys=True,separators=(',',':')).encode()).hexdigest();return [{'execution_ready':True,'origin':v['origin'],'witness':v}]

def candidate_plan(issue,localization,*,source_root=None,limit=12):
 # V20 supersedes V19's repository-wide full-source scan. Reuse its inherited
 # plan without source_root, then perform exactly one bounded source scan here.
 b=v19_plan(issue,localization,source_root=None,limit=limit); rows=list(b['candidates']); known={(x.get('witness') or {}).get('witness_sha256') for x in rows}
 if source_root:
  for x in _bounded_corroboration(issue,rows,source_root):
   k=x['witness']['witness_sha256']
   if k not in known and len(rows)<limit:rows.append(x);known.add(k)
  for x in _ownership_semantic_binding(issue,source_root):
   k=x['witness']['witness_sha256']
   if k not in known and len(rows)<limit:rows.append(x);known.add(k)
 by={}
 for x in rows:
  if not x.get('execution_ready'):continue
  w=x.get('witness') or {};p=w.get('candidate_path') or w.get('path');o=x.get('origin',''); fam='structural' if o in {'explicit_issue_callable_binding','explicit_callable_same_module_corroboration','relation_object_unique_type_corroboration','issue_attribute_unique_property_corroboration','full_source_unique_attribute_assignment_corroboration','issue_noun_bounded_full_source_assignment'} else 'semantic_localization' if o=='explicit_issue_ownership_clause_binding' else _family(o)
  if p:by.setdefault(p,set()).add(fam)
 consensus={p:sorted(fs) for p,fs in by.items() if len(fs)>=2}
 v={'schema':'e1c-strict-v20-candidate-plan-v1','candidate_count':len(rows),'executable_candidate_count':sum(bool(x.get('execution_ready')) for x in rows),'consensus_path_count':len(consensus),'consensus_paths':consensus,'status':b['status'],'candidates':rows,'provider_calls':0,'benchmark_assertion_used':False};v['plan_sha256']=hashlib.sha256(json.dumps(v,sort_keys=True,separators=(',',':')).encode()).hexdigest();return v
