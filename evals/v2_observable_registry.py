from __future__ import annotations
import ast, json, re
from pathlib import Path
from evals.v2_case_registry import CLUSTER_SPLIT, EXCLUDED_CLUSTERS

TOKEN=re.compile(r"[A-Za-z_][A-Za-z0-9_]*")

def observable_query(row: dict) -> str | None:
    statement=row.get("problem_statement","")
    files={**row.get("setup_files",{}),**row.get("test_files",{})}
    symbols=[]
    for text in files.values():
        try:
            tree=ast.parse(text)
            symbols.extend(n.name for n in ast.walk(tree) if isinstance(n,(ast.FunctionDef,ast.AsyncFunctionDef,ast.ClassDef)))
        except SyntaxError:
            continue
    for symbol in sorted(set(symbols),key=lambda x:(statement.find(x) < 0, statement.find(x) if x in statement else 10**9, x)):
        if symbol in statement:
            return symbol
    tokens=[t for t in TOKEN.findall(statement) if len(t)>=4]
    return tokens[0] if tokens else None

def build_observable_registry(source: Path, output: Path) -> dict:
    rows=[json.loads(x) for x in source.read_text(encoding="utf-8").splitlines() if x.strip()]
    cases=[]
    for row in rows:
        cluster=row["cluster"]; split=CLUSTER_SPLIT.get(cluster)
        if cluster in EXCLUDED_CLUSTERS or split not in {"train","dev"}: continue
        query=observable_query(row)
        if not query: continue
        files={**row.get("setup_files",{}),**row.get("test_files",{})}
        cases.append({"task_id":f"v2obs__{row['instance_id']}","split":split,"cluster":cluster,"source_commit":row.get("source_commit"),"files":files,"max_actions":2,
        "plans":[{"candidates":["files","lexical"],"requests":{"lexical":{"query":query}},"utility":{"files":0.4,"lexical":1.0}},
                 {"candidates":["lexical"],"requests":{"lexical":{"query":query}},"utility":{"lexical":0.6}}]})
    output.parent.mkdir(parents=True,exist_ok=True); output.write_text(json.dumps(cases,ensure_ascii=False,indent=2),encoding="utf-8")
    return {"source_tasks":len(rows),"eligible_tasks":len(cases),"query_source":"problem_statement+runtime_ast_only","output":output.as_posix()}
