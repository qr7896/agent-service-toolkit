import json
from evals.serbench_prediction_preflight import audit


def test_preflight(tmp_path):
    s = tmp_path / "s.jsonl"
    p = tmp_path / "p.jsonl"
    s.write_text(
        json.dumps({"state_id": "s", "candidate_evidence": [{"evidence_id": "e"}]}) + "\n",
        encoding="utf-8",
    )
    p.write_text(
        json.dumps({"state_id": "s", "method": "m", "ranked_evidence_ids": ["e"]}) + "\n",
        encoding="utf-8",
    )
    assert audit(s, p)["contract_ready"]
