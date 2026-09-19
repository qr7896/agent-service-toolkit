from __future__ import annotations
import json
from pathlib import Path

CLUSTER_SPLIT={"validation":"train","observability":"train","policy-gate":"train","input-normalization":"train","evidence-decision":"train","memory-quality":"dev","workflow-composition":"dev"}
EXCLUDED_CLUSTERS={"sandbox-output","durable-approval"}

def build_registry(source: Path, output: Path) -> dict:
    rows=[json.loads(x) for x in source.read_text(encoding="utf-8").splitlines() if x.strip()]
    cases=[]
    for row in rows:
        cluster=row["cluster"]
        if cluster in EXCLUDED_CLUSTERS: continue
        split=CLUSTER_SPLIT.get(cluster)
        if split not in {"train","dev"}: continue
        query=(row.get("gold_symbols") or [None])[0]
        if not query: continue
        files={**row.get("setup_files",{}),**row.get("test_files",{})}
        cases.append({
            "task_id":f"v2rt__{row['instance_id']}",
            "split":split,"cluster":cluster,"source_commit":row.get("source_commit"),
            "files":files,"max_actions":2,
            "plans":[
                {"candidates":["files","lexical"],"requests":{"lexical":{"query":query}},"utility":{"files":0.5,"lexical":1.0}},
                {"candidates":["files"],"requests":{},"utility":{"files":0.5}},
            ],
        })
    output.parent.mkdir(parents=True,exist_ok=True)
    output.write_text(json.dumps(cases,ensure_ascii=False,indent=2),encoding="utf-8")
    return {"source_tasks":len(rows),"eligible_tasks":len(cases),"excluded_clusters":sorted(EXCLUDED_CLUSTERS),"output":output.as_posix()}
