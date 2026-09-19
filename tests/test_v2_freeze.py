import json
import pytest
from evals.v2_distribution import distribution_report
from evals.v2_freeze import freeze_dataset

def row(i):
    return {"schema_version":"v2-decision-v1","reward_config_sha256":"x","task_id":f"t{i}","step":0,"state":{"split":"train","cluster":f"c{i}","source_commit":f"k{i}"},"candidates":[{"action":"stop","propensity":1.0,"policy_score":0.0}],"chosen_action":"stop"}

def test_distribution_report_counts_dimensions():
    report=distribution_report([row(1),row(2)],min_records=2)
    assert report["splits"]=={"train":2}
    assert report["source_commits"]==2
    assert report["candidate_action_counts"]=={"stop":2}

def test_freeze_refuses_underfilled_dataset(tmp_path):
    d=tmp_path/"d.jsonl"; d.write_text(json.dumps(row(1))+"\n",encoding="utf-8")
    with pytest.raises(RuntimeError,match="not replay-ready"):
        freeze_dataset(d,[],tmp_path/"m.json",tmp_path/"r.json",min_records=2)
    assert not (tmp_path/"m.json").exists()

def test_freeze_writes_manifest_and_report_only_when_ready(tmp_path):
    d=tmp_path/"d.jsonl"; d.write_text(json.dumps(row(1))+"\n"+json.dumps(row(2))+"\n",encoding="utf-8")
    m=tmp_path/"m.json"; r=tmp_path/"r.json"
    manifest,report=freeze_dataset(d,[],m,r,min_records=2)
    assert manifest["validation"]["ready_for_replay"] is True
    assert report["validation"]["records"]==2 and m.exists() and r.exists()
