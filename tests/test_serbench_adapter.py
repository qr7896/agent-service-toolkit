import pytest
from evals.serbench_adapter import prediction,to_external_state

def test_official_field_mapping():
 row={"state_id":"s","repo":"r","instance_id":"i","issue":"bug","information_need":"need","candidate_evidence":[]}
 out=to_external_state(row);assert out["external_state_id"]=="s" and "information_need: need" in out["state_text"]

def test_prediction_contract():
 assert prediction("s","m",["e1"])=={"state_id":"s","method":"m","ranked_evidence_ids":["e1"]}
 with pytest.raises(ValueError): prediction("s","m",["e1","e1"])
