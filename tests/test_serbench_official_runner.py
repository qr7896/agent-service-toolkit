import json
from evals.serbench_official_runner import write_predictions

def test_abstention_prediction_contract(tmp_path):
 out=tmp_path/"p.jsonl";write_predictions([{"state_id":"s1"},{"state_id":"s2"}],out)
 rows=[json.loads(x) for x in out.read_text(encoding="utf-8").splitlines()]
 assert [x["state_id"] for x in rows]==["s1","s2"]
 assert all(x["ranked_evidence_ids"]==[] for x in rows)
