from evals.v2_weight_free_efficiency import audit
def test_ratios():
 r=audit({"rows":[{"task_id":"x","step":0,"action":"lexical","unique_gain":2,"retained_proxy_tokens":10,"cost":2,"risk":1}]});assert r["by_action"]["lexical"]["unique_gain_per_cost"]==1
