from evals.v2_coverage_escalation_summary import compare
def test_recovery():
 d={"rows":[{"task_id":"x","v1":{"resolved":False}}]};p={"rows":[{"task_id":"x","gold_hit":True}]};assert compare(d,p)["coverage_recovery_rate"]==1
