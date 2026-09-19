from __future__ import annotations
import ast, json
from pathlib import Path
from evals.v2_case_registry import CLUSTER_SPLIT, EXCLUDED_CLUSTERS

def observable_views(row: dict):
    files={**row.get("setup_files",{}),**row.get("test_files",{})}
    views=[]
    for rel,text in sorted(files.items()):
        stem=Path(rel).stem
        if stem and not stem.startswith("test_"): views.append(("file",stem))
        try:
            tree=ast.parse(text)
        except SyntaxError:
            continue
        names=sorted({n.name for n in ast.walk(tree) if isinstance(n,(ast.FunctionDef,ast.AsyncFunctionDef,ast.ClassDef)) and not n.name.startswith("test_")})
        for name in names[:2]: views.append(("ast",name))
    seen=set(); return [(kind,q) for kind,q in views if q and not (q in seen or seen.add(q))]

def build_diverse_registry(source: Path, output: Path, *, max_views_per_task=3):
    rows=[json.loads(x) for x in source.read_text(encoding="utf-8").splitlines() if x.strip()]
    cases=[]
    for row in rows:
        cluster=row["cluster"]; split=CLUSTER_SPLIT.get(cluster)
        if cluster in EXCLUDED_CLUSTERS or split not in {"train","dev"}: continue
        files={**row.get("setup_files",{}),**row.get("test_files",{})}
        for i,(kind,query) in enumerate(observable_views(row)[:max_views_per_task]):
            cases.append({"task_id":f"v2div{i}__{row['instance_id']}","split":split,"cluster":cluster,"source_commit":row.get("source_commit"),"files":files,"max_actions":1,
              "plans":[{"candidates":["lexical"],"requests":{"lexical":{"query":query}},"utility":{"lexical":1.0}}],
              "collection_view":kind})
    output.parent.mkdir(parents=True,exist_ok=True); output.write_text(json.dumps(cases,ensure_ascii=False,indent=2),encoding="utf-8")
    return {"source_tasks":len(rows),"trajectory_cases":len(cases),"max_views_per_task":max_views_per_task,"query_source":"runtime_file_names+AST","output":output.as_posix()}
