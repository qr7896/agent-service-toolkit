import json
from evals.v2_merge import merge_jsonl

def record(task, step=0):
    return {"schema_version":"v2-decision-v1","reward_config_sha256":"x","task_id":task,"step":step,"state":{},"candidates":[{"action":"stop","propensity":1.0,"policy_score":0.0}],"chosen_action":"stop"}

def test_merge_deduplicates_identical_records(tmp_path):
    a=tmp_path/"a.jsonl"; b=tmp_path/"b.jsonl"; out=tmp_path/"out.jsonl"
    row=record("t")
    a.write_text(json.dumps(row)+"\n",encoding="utf-8"); b.write_text(json.dumps(row)+"\n",encoding="utf-8")
    summary=merge_jsonl([a,b],out,min_records=1)
    assert summary["records"]==1 and summary["source_duplicates_removed"]==1
    assert summary["ready_for_replay"] is True

def test_merge_does_not_hide_conflicting_same_task_step(tmp_path):
    a=tmp_path/"a.jsonl"; b=tmp_path/"b.jsonl"; out=tmp_path/"out.jsonl"
    r1=record("t"); r2=record("t"); r2["state"]={"different":True}
    a.write_text(json.dumps(r1)+"\n",encoding="utf-8"); b.write_text(json.dumps(r2)+"\n",encoding="utf-8")
    summary=merge_jsonl([a,b],out,min_records=1)
    assert any("duplicate task-step" in e for e in summary["errors"])
    assert summary["ready_for_replay"] is False
