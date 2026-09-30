"""Strict-v21 development: explicit callable return-type corroboration.

Development-only successor to frozen V20.  This derives an additional
structural witness only when the issue names a callable and a type-like noun,
and production AST shows that uniquely localized callable defines or returns
that noun.  No benchmark assertions, task ids, grader data, or hidden tests
are consumed.
"""
from __future__ import annotations
import ast, hashlib, json, re
from pathlib import Path
from evals.e1c_strict_v20_probe import candidate_plan as v20_plan, _family

_TYPE_NOUN = re.compile(r"(?i)\b([A-Za-z_]\w*)\s+(?:object|instance|manager|class|type)\b")
_ROLE_NOUN = re.compile(r"(?i)\b(manager|descriptor|factory|builder|handler|adapter|wrapper|serializer|parser|renderer|validator)\b")

def _callable_type_corroboration(issue, rows, source_root):
    nouns={m.group(1).lower() for m in _TYPE_NOUN.finditer(issue)}|{m.group(1).lower() for m in _ROLE_NOUN.finditer(issue)}
    if not nouns: return []
    out=[]
    for x in rows:
        if not x.get('execution_ready') or x.get('origin')!='explicit_issue_callable_binding': continue
        w=x.get('witness') or {}; path=w.get('candidate_path') or w.get('path'); name=str(w.get('subject') or w.get('callable') or '').lower()
        if not path or not name: continue
        p=Path(source_root)/path
        try: tree=ast.parse(p.read_text(encoding='utf-8'))
        except (SyntaxError,UnicodeDecodeError,OSError): continue
        defs=[n for n in ast.walk(tree) if isinstance(n,(ast.FunctionDef,ast.AsyncFunctionDef)) and n.name.lower()==name]
        if len(defs)!=1: continue
        fn=defs[0]; tokens=set()
        for n in ast.walk(fn):
            if isinstance(n,ast.Name): tokens.add(n.id.lower())
            elif isinstance(n,ast.Attribute): tokens.add(n.attr.lower())
            elif isinstance(n,ast.ClassDef): tokens.add(n.name.lower())
        # Match a generic issue noun against production identifiers by token
        # suffix (e.g. "manager" -> "RelatedManager"), not by repository name.
        matched=sorted(n for n in nouns if any(t==n or t.endswith(n) for t in tokens))
        if not matched: continue
        v={'schema':'e1c-strict-v21-callable-type-corroboration-v1','kind':'structural_corroboration','callable':name,'type_nouns':matched,'candidate_path':path,'execution_ready':True,'origin':'explicit_callable_issue_type_corroboration','provenance':'explicit_issue_callable_unique_definition_plus_issue_type_noun_in_production_ast','benchmark_assertion_used':False,'task_id_used':False}
        v['witness_sha256']=hashlib.sha256(json.dumps(v,sort_keys=True,separators=(',',':')).encode()).hexdigest(); out.append({'execution_ready':True,'origin':v['origin'],'witness':v})
    return out

def candidate_plan(issue,localization,*,source_root=None,limit=12):
    b=v20_plan(issue,localization,source_root=source_root,limit=limit); rows=list(b['candidates']); known={(x.get('witness') or {}).get('witness_sha256') for x in rows}
    if source_root:
        for x in _callable_type_corroboration(issue,rows,source_root):
            k=x['witness']['witness_sha256']
            if k not in known and len(rows)<limit: rows.append(x);known.add(k)
    by={}
    for x in rows:
        if not x.get('execution_ready'): continue
        w=x.get('witness') or {};p=w.get('candidate_path') or w.get('path');o=x.get('origin','')
        fam='structural' if o=='explicit_callable_issue_type_corroboration' else ('structural' if o in {'explicit_issue_callable_binding','explicit_callable_same_module_corroboration','relation_object_unique_type_corroboration','issue_attribute_unique_property_corroboration','full_source_unique_attribute_assignment_corroboration','issue_noun_bounded_full_source_assignment'} else 'semantic_localization' if o=='explicit_issue_ownership_clause_binding' else _family(o))
        if p: by.setdefault(p,set()).add(fam)
    consensus={p:sorted(fs) for p,fs in by.items() if len(fs)>=2}
    v={'schema':'e1c-strict-v21-candidate-plan-v1','candidate_count':len(rows),'executable_candidate_count':sum(bool(x.get('execution_ready')) for x in rows),'consensus_path_count':len(consensus),'consensus_paths':consensus,'status':b['status'],'candidates':rows,'provider_calls':0,'benchmark_assertion_used':False};v['plan_sha256']=hashlib.sha256(json.dumps(v,sort_keys=True,separators=(',',':')).encode()).hexdigest();return v
