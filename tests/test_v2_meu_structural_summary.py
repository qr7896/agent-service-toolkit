from evals.v2_meu_structural_summary import audit
def test_summary(): assert audit({"rows":[{"action":"structural","task_id":"x","meu":1,"retained_proxy_tokens":2,"unique_gain":1}]})["all_positive"]
