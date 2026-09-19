import pytest
from evals.external_sufficiency_compat import inspect,normalize

def test_fixture_ready():
 row={"external_state_id":"x","repository":"r","state_text":"s","candidate_evidence":[],"required_evidence_groups":[["e"]]}
 assert inspect([row])["ready_for_compat_eval"]

def test_fail_closed_missing():
 with pytest.raises(ValueError): normalize({"repository":"r"})
