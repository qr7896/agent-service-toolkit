from evals.v2_compression_preservation import audit
def test_joint():
 b={"reduction":{},"rows":[{"task_id":"x","before":{"items":1,"chars":2,"approx_tokens":1},"after":{"items":1,"chars":2,"approx_tokens":1}}]};c={"rows":[{"task_id":"x","gold_hit":True}]};d={"rows":[{"task_id":"x","resolved":True}]};assert audit(b,c,d)["all_target_coverage_preserved"]
