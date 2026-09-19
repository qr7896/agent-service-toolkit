from evals.v2_compression_robustness import audit
def test_positive():
 r={"rows":[{"task_id":"x","items_before":2,"approx_tokens_before":10,"approx_tokens_after":2}]};assert audit(r)["all_positive"]
