from evals.external_complete_set_recovery import complete_set_recovery,evaluate

def test_groups():
 r={"required_evidence_groups":[["a","b"],["c"]]}
 assert complete_set_recovery(r,{"b","c"})
 assert not complete_set_recovery(r,{"a"})
