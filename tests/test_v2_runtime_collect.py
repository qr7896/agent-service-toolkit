import json
from evals.v2_runtime_collect import collect_cases
from evals.v2_dataset import load_jsonl, validate_records

def cases():
    return [
      {"task_id":"r1","split":"train","cluster":"runtime-a","source_commit":"rt1","files":{"a.py":"def alpha(): return 1"},"max_actions":1,
       "plans":[{"candidates":["lexical"],"requests":{"lexical":{"query":"alpha"}},"utility":{"lexical":1.0}}]},
      {"task_id":"r2","split":"train","cluster":"runtime-b","source_commit":"rt2","files":{"b.py":"beta = 2"},"max_actions":2,
       "plans":[{"candidates":["files"],"requests":{},"utility":{"files":1.0}},{"candidates":["lexical"],"requests":{"lexical":{"query":"beta"}},"utility":{"lexical":1.0}}]}
    ]

def test_collect_cases_generates_runtime_native_records(tmp_path):
    out=tmp_path/"runtime.jsonl"; summary=collect_cases(cases(),out); rows=load_jsonl(out)
    assert summary=={"tasks":2,"records":5,"output":out.as_posix()}
    assert [r["chosen_action"] for r in rows]==["lexical","stop","files","lexical","stop"]
    assert validate_records(rows,min_records=5)["ready_for_replay"] is True

def test_collect_cases_is_deterministic(tmp_path):
    a=tmp_path/"a.jsonl"; b=tmp_path/"b.jsonl"
    collect_cases(cases(),a); collect_cases(cases(),b)
    assert a.read_bytes()==b.read_bytes()
