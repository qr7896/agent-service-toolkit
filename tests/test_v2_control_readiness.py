from evals.v2_control_readiness import gate
def test_oracle_success_does_not_open_control():
 r=gate({"rows":[{"delta":{"unique_evidence":0}}]},{"tasks":1,"outcome_preserved":1,"v1_resolved":1,"early_stop_resolved":1});assert r["oracle_outcome_preserved"] and not r["eligible_for_autonomous_control"]
