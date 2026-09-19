from evals.v2_early_stop_gate import validate
def test_gate_remains_fail_closed():
 r={"rows":[{"task_id":"x","v1":{"unique_evidence":2},"early_stop":{"unique_evidence":2},"delta":{"unique_evidence":0,"actions":-1}}],"aggregate":{}}
 x=validate(r);assert x["all_equal_unique_evidence"] and not x["eligible_for_control"]
