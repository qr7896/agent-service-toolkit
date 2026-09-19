import json
from evals.v2_diverse_registry import observable_views, build_diverse_registry

def test_views_come_only_from_files_and_ast():
    row={"setup_files":{"src/foo.py":"import os\ndef alpha(): pass\nclass Beta: pass"},"test_files":{},"gold_symbols":["SECRET"]}
    views=observable_views(row)
    assert ("file","foo") in views and ("ast","alpha") in views and all("SECRET" not in q for _,q in views)

def test_diverse_registry_namespaces_views(tmp_path):
    src=tmp_path/"s.jsonl"; out=tmp_path/"o.json"
    row={"instance_id":"x","cluster":"validation","source_commit":"c","setup_files":{"src/foo.py":"def alpha(): pass\ndef beta(): pass"},"test_files":{},"gold_symbols":["SECRET"]}
    src.write_text(json.dumps(row),encoding="utf-8"); summary=build_diverse_registry(src,out,max_views_per_task=3)
    cases=json.loads(out.read_text(encoding="utf-8"))
    assert summary["trajectory_cases"]==3
    assert len({c["task_id"] for c in cases})==3
    assert "SECRET" not in out.read_text(encoding="utf-8")
