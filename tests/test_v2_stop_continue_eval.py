from evals.v2_stop_continue_eval import evaluate
def test_observed_continue_gain():
 b={"spent":{"cost":1,"risk":.1},"unique_evidence":2,"mean_redundancy":0};a={"spent":{"cost":2,"risk":.2},"unique_evidence":2,"mean_redundancy":.5}
 rows=[{"task_id":"x","step":1,"shadow_action":"stop","executed_action":"lexical","policy_state":b},{"task_id":"x","step":2,"shadow_action":"stop","executed_action":"stop","policy_state":a}]
 x=evaluate(rows);assert x["cases"]==1 and x["zero_unique_gain_cases"]==1 and x["total_incremental_cost"]==1
