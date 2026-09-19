import json
from evals.v2_observable_registry import observable_query, build_observable_registry

def test_observable_query_uses_statement_and_source_not_gold():
    row={"problem_statement":"allowed 必须拒绝脚本","setup_files":{"a.py":"def allowed(x): return True"},"test_files":{},"gold_symbols":["SECRET"]}
    assert observable_query(row)=="allowed"

def test_registry_has_no_gold_payload(tmp_path):
    src=tmp_path/"s.jsonl"; out=tmp_path/"o.json"
    row={"instance_id":"x","cluster":"validation","source_commit":"c","problem_statement":"allowed should work","setup_files":{"a.py":"def allowed(x): return x"},"test_files":{},"gold_symbols":["SECRET"],"gold_files":["SECRET.py"]}
    src.write_text(json.dumps(row),encoding="utf-8"); summary=build_observable_registry(src,out)
    text=out.read_text(encoding="utf-8")
    assert summary["eligible_tasks"]==1 and "SECRET" not in text and "gold_" not in text
