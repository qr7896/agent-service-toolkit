from evals.v2_pareto_audit import summary
def test_three_policies():
 e={"rows":[{"v1":{"action_count":2,"total_cost":2.2,"total_risk":.6},"early_stop":{"action_count":1,"total_cost":1.1,"total_risk":.3}}]};a={"tasks":1,"aggregate":{"actions":2,"cost":2,"risk":.4}};d={"v1_resolved":0,"early_stop_resolved":0};ad={"resolved":1};assert len(summary(e,a,d,ad)["rows"])==3
