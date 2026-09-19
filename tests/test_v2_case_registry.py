import json
from evals.v2_case_registry import build_registry

def test_registry_excludes_sealed_like_test_clusters_and_gold_payload(tmp_path):
    src=tmp_path/"tasks.jsonl"; out=tmp_path/"cases.json"
    rows=[
      {"instance_id":"a","cluster":"validation","source_commit":"c1","setup_files":{"a.py":"def x(): pass"},"test_files":{},"gold_symbols":["x"],"gold_files":["a.py"]},
      {"instance_id":"b","cluster":"sandbox-output","source_commit":"c2","setup_files":{"b.py":"x=1"},"test_files":{},"gold_symbols":["x"],"gold_files":["b.py"]},
    ]
    src.write_text("\n".join(json.dumps(x) for x in rows),encoding="utf-8")
    summary=build_registry(src,out); cases=json.loads(out.read_text(encoding="utf-8"))
    assert summary["eligible_tasks"]==1 and cases[0]["task_id"]=="v2rt__a"
    assert "gold_files" not in json.dumps(cases)
    assert cases[0]["plans"][0]["requests"]["lexical"]["query"]=="x"
